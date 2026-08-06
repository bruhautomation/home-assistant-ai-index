#!/usr/bin/env python3
"""Regenerate the README index tables between the GENERATED markers.

Joins curated entries with harvested data. Six columns, grouped by category,
sorted by name — never by stars (this is an index, not a scoreboard).
Run with --check to verify the README is in sync (CI uses this).
"""

from __future__ import annotations

import argparse
import sys

from common import (
    CAP_ICONS,
    CAPABILITIES,
    CATEGORIES,
    CATEGORY_TITLES,
    ROOT,
    load_entries,
    load_generated,
    load_summary,
)

SITE = "https://bruhautomation.github.io/home-assistant-ai-index"
BEGIN = "<!-- BEGIN GENERATED -->"
END = "<!-- END GENERATED -->"

INSTALL_LABELS = {
    "core-integration": "core",
    "hacs-integration": "HACS",
    "addon": "add-on",
    "container": "container",
    "external": "external",
}


def fmt_stars(n) -> str:
    if n is None:
        return ""
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def caps_cell(entry: dict) -> str:
    disputed = set(entry.get("disputed", []))
    icons = [
        CAP_ICONS[cap] + ("⚠️" if cap in disputed else "")
        for cap in CAPABILITIES
        if entry["capabilities"].get(cap)
    ]
    return "".join(icons) or "—"


def inference_cell(entry: dict) -> str:
    inf = set(entry.get("inference", []))
    if inf == {"local"}:
        return "🏠 local"
    if inf == {"cloud"}:
        return "☁️ cloud"
    return "🏠/☁️ choice"


def health_cell(entry: dict, generated: dict) -> str:
    parts = []
    meta = generated.get("repo_meta") or {}
    if entry["repo"] == "home-assistant/core":
        parts.append("part of core")
    elif entry["repo"] == "home-assistant/addons":
        parts.append("official add-on")
    else:
        if meta.get("stars") is not None:
            parts.append(f"★ {fmt_stars(meta['stars'])}")
        if meta.get("pushed_at"):
            parts.append(meta["pushed_at"][:10])
        if meta.get("archived"):
            parts.append("⚠️ archived")
    addon = generated.get("addon")
    if addon:
        parts.append(f"🛡️ {addon['supervisor_rating']['value']}/8")
    return " · ".join(parts) or "—"


def render_tables() -> str:
    entries = load_entries()
    summary = load_summary()
    by_category: dict[str, list[dict]] = {}
    for entry in entries:
        by_category.setdefault(entry["category"], []).append(entry)

    lines = []
    harvested = summary.get("harvested_at", "")
    stamp = f", metrics harvested {harvested[:10]}" if harvested else ""
    lines.append(f"**{len(entries)} projects indexed**{stamp}. "
                 f"Sorted by name — never by stars. "
                 f"[Filter, compare, and see the evidence on the site →]({SITE}/)")
    lines.append("")

    for category in CATEGORIES:
        group = by_category.get(category)
        if not group:
            continue
        lines.append(f"### {CATEGORY_TITLES[category]}")
        lines.append("")
        lines.append("| Name | Capabilities | Inference | Install | Health | |")
        lines.append("|---|---|---|---|---|---|")
        for entry in sorted(group, key=lambda e: e["name"].lower()):
            generated = load_generated(entry["id"])
            name = f"[{entry['name']}](https://github.com/{entry['repo']})"
            install = ", ".join(INSTALL_LABELS[i] for i in entry["install"])
            details = f"[→]({SITE}/entries/{entry['id']}/)"
            lines.append(
                f"| {name} | {caps_cell(entry)} | {inference_cell(entry)} "
                f"| {install} | {health_cell(entry, generated)} | {details} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the README is out of sync instead of writing")
    args = parser.parse_args()

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if BEGIN not in readme or END not in readme:
        print("README markers missing", file=sys.stderr)
        return 1

    head, rest = readme.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    updated = f"{head}{BEGIN}\n{render_tables()}{END}{tail}"

    if args.check:
        if updated != readme:
            print("README is out of sync — run: python tools/render_readme.py", file=sys.stderr)
            return 1
        print("README in sync.")
        return 0

    if updated != readme:
        readme_path.write_text(updated, encoding="utf-8")
        print("README updated.")
    else:
        print("README already current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
