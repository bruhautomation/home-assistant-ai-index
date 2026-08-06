#!/usr/bin/env python3
"""Harvest mechanical facts about every entry into data/generated/.

This is the bot's half of the repo. It never touches entries/*.yaml.

Per entry it collects, where obtainable:
  - GitHub repo metadata (stars, pushed_at, license, archived, latest release)
    — requires GITHUB_TOKEN / GH_TOKEN; skipped gracefully without one
  - a pinned commit SHA (GitHub API, or anonymous `git ls-remote` fallback)
  - the integration's manifest.json at that SHA: domain, iot_class,
    requirements, and providers detected from requirements — with the file,
    line, and commit as evidence
  - the add-on's config at its packaging repo: the permission keys it
    requests (each with file+line+commit evidence) and the Supervisor
    security rating computed by the ported algorithm in rating.py

Design rules:
  - per-entry output files contain no timestamps, and are only rewritten when
    their content changes — a quiet night is a no-op commit-wise.
  - the run timestamp and error report live in data/generated/summary.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import yaml

from common import GENERATED_DIR, load_entries
from rating import rating_security

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

# requirement package -> provider slug (as used in entries' `providers`)
REQUIREMENT_PROVIDERS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google-generativeai": "google",
    "google-genai": "google",
    "ollama": "ollama",
    "mistralai": "mistral",
    "groq": "groq",
    "openrouter": "openrouter",
}

# Add-on config keys worth surfacing as permission facts, with plain-language
# descriptions. Severity is the reader's call; we only state what is requested.
ADDON_PERMISSION_KEYS = {
    "full_access": "full hardware access (disables protections; rating forced to 1)",
    "docker_api": "access to the Docker API (control over all containers; rating forced to 1)",
    "privileged": "extra kernel capabilities",
    "host_network": "runs on the host network",
    "host_pid": "shares the host PID namespace",
    "host_uts": "shares the host UTS namespace",
    "host_dbus": "access to the host D-Bus",
    "kernel_modules": "can load kernel modules",
    "apparmor": "AppArmor setting",
    "hassio_role": "Supervisor API role",
    "hassio_api": "Supervisor API access",
    "homeassistant_api": "Home Assistant API access",
    "auth_api": "Home Assistant authentication API",
    "ingress": "web UI through authenticated ingress",
    "map": "mapped Home Assistant folders",
    "devices": "direct device access",
    "udev": "hardware/udev events",
    "uart": "serial/UART access",
    "audio": "audio subsystem access",
    "video": "video device access",
    "gpio": "GPIO access",
    "codenotary": "signed container image",
}


def http_get(url: str, *, accept: str | None = None, auth: bool = False) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "home-assistant-ai-index harvester"})
    if accept:
        req.add_header("Accept", accept)
    if auth and TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()
    except (urllib.error.URLError, TimeoutError) as err:
        return 0, str(err).encode()


def api_json(path: str) -> tuple[int, dict | list | None]:
    status, body = http_get(f"{API}{path}", accept="application/vnd.github+json", auth=True)
    if status == 200:
        return status, json.loads(body)
    return status, None


def ls_remote_head(repo: str) -> str | None:
    """Anonymous fallback for pinning a SHA when the API is unavailable."""
    try:
        out = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{repo}", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
        return out.split()[0] if out.strip() else None
    except (subprocess.SubprocessError, OSError):
        return None


def find_line(text: str, pattern: str) -> int | None:
    for i, line in enumerate(text.splitlines(), start=1):
        if re.search(pattern, line):
            return i
    return None


def requirement_name(req: str) -> str:
    return re.split(r"[=<>!~\[;]", req, maxsplit=1)[0].strip().lower()


def integration_domain_candidates(entry: dict) -> list[str]:
    """Places an integration's manifest directory name might come from."""
    candidates = []
    if entry.get("domain"):
        candidates.append(entry["domain"])
    url = entry.get("url", "")
    m = re.search(r"/integrations/([a-z0-9_]+)", url)
    if m:
        candidates.append(m.group(1))
    repo_name = entry["repo"].split("/")[1]
    for raw in (entry["id"], repo_name, re.sub(r"^(ha|hass|homeassistant)[-_]", "", repo_name)):
        candidates.append(raw.replace("-", "_"))
    seen, out = set(), []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def harvest_repo_meta(entry: dict, result: dict, errors: list) -> None:
    repo = entry["repo"]
    status, meta = api_json(f"/repos/{repo}")
    if meta:
        lic = meta.get("license") or {}
        result["repo_meta"] = {
            "stars": meta.get("stargazers_count"),
            "forks": meta.get("forks_count"),
            "open_issues": meta.get("open_issues_count"),
            "archived": meta.get("archived", False),
            "license": lic.get("spdx_id"),
            "pushed_at": meta.get("pushed_at"),
            "default_branch": meta.get("default_branch"),
        }
        # Latest release is uninformative for monorepos like home-assistant/core
        if repo != "home-assistant/core":
            status, release = api_json(f"/repos/{repo}/releases/latest")
            if release:
                result["latest_release"] = {
                    "tag": release.get("tag_name"),
                    "published_at": release.get("published_at"),
                }
    elif status in (403, 429):
        errors.append({"id": entry["id"], "stage": "repo_meta", "error": f"rate limited ({status})"})
    elif status != 404 and not TOKEN:
        pass  # no token: expected degradation, not an error
    elif status:
        errors.append({"id": entry["id"], "stage": "repo_meta", "error": f"HTTP {status}"})


def pin_sha(entry: dict, result: dict, errors: list) -> str | None:
    repo = entry["repo"]
    status, commits = api_json(f"/repos/{repo}/commits?per_page=1")
    if commits and isinstance(commits, list):
        sha = commits[0]["sha"]
    else:
        sha = ls_remote_head(repo)
    if sha:
        result["sha"] = sha
    else:
        errors.append({"id": entry["id"], "stage": "pin_sha", "error": "could not resolve HEAD"})
    return sha


def harvest_manifest(entry: dict, sha: str, result: dict, errors: list) -> None:
    """Locate and parse the integration's manifest.json at the pinned SHA."""
    repo = entry["repo"]
    is_core = repo == "home-assistant/core"
    for domain in integration_domain_candidates(entry):
        path = (
            f"homeassistant/components/{domain}/manifest.json"
            if is_core
            else f"custom_components/{domain}/manifest.json"
        )
        status, body = http_get(f"{RAW}/{repo}/{sha}/{path}")
        if status != 200:
            continue
        text = body.decode("utf-8", errors="replace")
        try:
            manifest = json.loads(text)
        except json.JSONDecodeError:
            errors.append({"id": entry["id"], "stage": "manifest", "error": f"unparseable {path}"})
            return
        info = {
            "domain": manifest.get("domain", domain),
            "name": manifest.get("name"),
            "iot_class": manifest.get("iot_class"),
            "requirements": manifest.get("requirements", []),
            "version": manifest.get("version"),
            "evidence": {"repo": repo, "path": path, "commit": sha,
                         "line": find_line(text, r'"iot_class"') or 1},
        }
        providers = sorted({
            REQUIREMENT_PROVIDERS[requirement_name(r)]
            for r in info["requirements"]
            if requirement_name(r) in REQUIREMENT_PROVIDERS
        })
        if providers:
            info["detected_providers"] = providers
        result["manifest"] = info
        return
    errors.append({"id": entry["id"], "stage": "manifest", "error": "manifest.json not found"})


def harvest_addon(entry: dict, result: dict, errors: list) -> None:
    """Fetch the add-on's config from its packaging repo; derive permissions + rating."""
    addon = entry.get("addon_config")
    if not addon:
        return
    repo, base = addon["repo"], addon["path"].strip("/")
    sha = ls_remote_head(repo)
    if not sha:
        errors.append({"id": entry["id"], "stage": "addon", "error": f"no HEAD for {repo}"})
        return
    config, text, path = None, None, None
    for candidate in (f"{base}/config.yaml", f"{base}/config.json"):
        status, body = http_get(f"{RAW}/{repo}/{sha}/{candidate}")
        if status == 200:
            text = body.decode("utf-8", errors="replace")
            path = candidate
            config = yaml.safe_load(text) if candidate.endswith(".yaml") else json.loads(text)
            break
    if config is None:
        errors.append({"id": entry["id"], "stage": "addon", "error": f"no config at {repo}/{base}"})
        return

    status, _ = http_get(f"{RAW}/{repo}/{sha}/{base}/apparmor.txt")
    has_profile = status == 200

    permissions = []
    for key, description in ADDON_PERMISSION_KEYS.items():
        if key in config:
            permissions.append({
                "key": key,
                "value": config[key],
                "description": description,
                "evidence": {"repo": repo, "path": path, "commit": sha,
                             "line": find_line(text, rf'^\s*"?{key}"?\s*:') or 1},
            })

    value, breakdown = rating_security(config, has_profile)
    result["addon"] = {
        "repo": repo,
        "path": base,
        "commit": sha,
        "config_path": path,
        "version": config.get("version"),
        "apparmor_profile": has_profile,
        "permissions": permissions,
        "supervisor_rating": {"value": value, "breakdown": breakdown},
    }


def harvest_entry(entry: dict, errors: list, no_api: bool) -> dict:
    result: dict = {"id": entry["id"], "repo": entry["repo"]}
    if not no_api:
        harvest_repo_meta(entry, result, errors)
    sha = pin_sha(entry, result, errors)
    installs = set(entry.get("install", []))
    if sha and installs & {"core-integration", "hacs-integration"}:
        harvest_manifest(entry, sha, result, errors)
    harvest_addon(entry, result, errors)
    return result


def write_if_changed(path, payload: dict) -> bool:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", help="comma-separated entry ids (default: all)")
    parser.add_argument("--no-api", action="store_true",
                        help="skip GitHub API metadata (SHA pinning + raw fetches only)")
    args = parser.parse_args()

    wanted = set(args.entries.split(",")) if args.entries else None
    entries = [e for e in load_entries() if not wanted or e["id"] in wanted]
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    errors: list[dict] = []
    changed = 0
    for entry in entries:
        result = harvest_entry(entry, errors, args.no_api)
        if write_if_changed(GENERATED_DIR / f"{entry['id']}.json", result):
            changed += 1
        print(f"harvested {entry['id']}", file=sys.stderr)
        time.sleep(0.3)  # stay polite to the API and raw hosts

    summary = {
        "harvested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entries": len(entries),
        "changed": changed,
        "api_authenticated": bool(TOKEN),
        "errors": errors,
    }
    (GENERATED_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{len(entries)} entries, {changed} changed, {len(errors)} errors", file=sys.stderr)
    for err in errors:
        print(f"  {err['id']}: {err['stage']}: {err['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
