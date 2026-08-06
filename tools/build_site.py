#!/usr/bin/env python3
"""Build the static site into _site/.

Outputs:
  _site/index.html          filterable index (vanilla JS, data embedded inline)
  _site/data.json           the same merged data as a stable, documented artifact
  _site/style.css           shared stylesheet
  _site/entries/<id>/index.html   one static detail page per entry

Everything is self-contained: no frameworks, no CDNs, relative paths only.
All curated strings are HTML-escaped — entries arrive via PRs.
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from common import (
    CAP_ICONS,
    CAP_LABELS,
    CAPABILITIES,
    CATEGORIES,
    CATEGORY_TITLES,
    ROOT,
    SENSITIVE,
    load_entries,
    load_generated,
    load_summary,
)

SITE_DIR = ROOT / "site"
OUT = ROOT / "_site"
REPO_URL = "https://github.com/bruhautomation/home-assistant-ai-index"

INSTALL_LABELS = {
    "core-integration": "core integration",
    "hacs-integration": "HACS integration",
    "addon": "add-on",
    "container": "container",
    "external": "external",
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def evidence_url(entry: dict, ev: dict) -> str:
    repo = ev.get("repo") or entry["repo"]
    return f"https://github.com/{repo}/blob/{ev['commit']}/{ev['path']}#L{ev['line']}"


def build_data() -> dict:
    summary = load_summary()
    merged = []
    for entry in load_entries():
        entry = {k: v for k, v in entry.items() if not k.startswith("_")}
        entry["generated"] = load_generated(entry["id"])
        merged.append(entry)
    return {
        "schema_version": 1,
        "project": "Home Assistant AI Index",
        "repo": REPO_URL,
        "docs": f"{REPO_URL}#data",
        "license": "CC BY 4.0",
        "harvested_at": summary.get("harvested_at"),
        "capabilities": CAPABILITIES,
        "sensitive_capabilities": SENSITIVE,
        "capability_labels": CAP_LABELS,
        "capability_icons": CAP_ICONS,
        "categories": {c: CATEGORY_TITLES[c] for c in CATEGORIES},
        "entries": merged,
    }


def page(title: str, body: str, css_path: str, description: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{css_path}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔎</text></svg>">
</head>
<body>
{body}
<footer>
  <p>Facts with evidence, not scores. Content <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> ·
  code <a href="{REPO_URL}/blob/main/LICENSE">MIT</a> ·
  <a href="{REPO_URL}">source &amp; corrections</a></p>
</footer>
</body>
</html>
"""


def correction_url(entry_id: str) -> str:
    return (f"{REPO_URL}/issues/new?template=correction.yml"
            f"&title=%5Bcorrection%5D%20{entry_id}")


def build_index(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    payload = payload.replace("</", "<\\/")  # keep the inline JSON script-safe
    body = f"""<header class="hero">
  <h1>Home Assistant AI Index</h1>
  <p class="tag"><strong>What can this thing reach?</strong> Capability and data-flow facts for every way to
  hook AI into Home Assistant — cited to source at a pinned commit.</p>
  <nav><a href="{REPO_URL}">GitHub</a> · <a href="./data.json">data.json</a> ·
  <a href="{REPO_URL}#this-is-wrong-about-my-project">report an error</a></nav>
</header>
<section class="presets" aria-label="Preset questions">
  <button data-preset="cameras">📷 What can see my cameras?</button>
  <button data-preset="localonly">🏠 100% local only</button>
  <button data-preset="autonomous">⏰ Acts on its own</button>
  <button data-preset="cloudcamera">☁️📷 Camera frames leave home</button>
  <button data-preset="clear">✕ Clear filters</button>
</section>
<section class="filters" id="filters"></section>
<p class="count" id="count"></p>
<div class="tablewrap">
<table id="index">
  <thead></thead>
  <tbody></tbody>
</table>
</div>
<div class="comparebar" id="comparebar" hidden>
  <span id="comparelabel"></span>
  <button id="comparebtn">Compare</button>
  <button id="compareclear">clear</button>
</div>
<dialog id="comparedlg"><div id="comparebody"></div><form method="dialog"><button>Close</button></form></dialog>
<script type="application/json" id="data">{payload}</script>
<script src="./app.js"></script>"""
    return page(
        "Home Assistant AI Index",
        body,
        "./style.css",
        "Filterable index of Home Assistant AI integrations: capabilities, data flow, and health — with evidence.",
    )


def cap_rows(entry: dict) -> str:
    rows = []
    disputed = set(entry.get("disputed", []))
    evidence = entry.get("evidence", {})
    for cap in CAPABILITIES:
        value = entry["capabilities"].get(cap, False)
        cells = [
            f"<td>{CAP_ICONS[cap]} {esc(CAP_LABELS[cap])}</td>",
            f'<td class="{"yes" if value else "no"}">{"yes" if value else "no"}</td>',
        ]
        extra = []
        if cap in evidence:
            extra.append(f'<a href="{evidence_url(entry, evidence[cap])}">source ↗</a>')
        if cap in disputed:
            extra.append(f'<span class="disputed">⚠️ disputed — <a href="{correction_url(entry["id"])}">see corrections</a></span>')
        cells.append(f"<td>{' · '.join(extra)}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return "\n".join(rows)


def addon_section(entry: dict) -> str:
    addon = (entry.get("generated") or {}).get("addon")
    if not addon:
        return ""
    rating = addon["supervisor_rating"]
    steps = "".join(
        f'<li><code>{"+" if b["modifier"] > 0 else ""}{b["modifier"] or "→1"}</code> {esc(b["reason"])}</li>'
        for b in rating["breakdown"]
    ) or "<li>no modifiers — base rating</li>"
    perms = "".join(
        f'<tr><td><code>{esc(p["key"])}</code></td><td>{esc(json.dumps(p["value"]) if not isinstance(p["value"], str) else p["value"])}</td>'
        f'<td>{esc(p["description"])}</td>'
        f'<td><a href="https://github.com/{esc(p["evidence"]["repo"])}/blob/{p["evidence"]["commit"]}/{esc(p["evidence"]["path"])}#L{p["evidence"]["line"]}">source ↗</a></td></tr>'
        for p in addon["permissions"]
    )
    return f"""<h2>Add-on packaging</h2>
<p>Permissions requested by the add-on's
<a href="https://github.com/{esc(addon["repo"])}/blob/{addon["commit"]}/{esc(addon["config_path"])}">config</a>,
and Home Assistant's own <a href="https://developers.home-assistant.io/docs/add-ons/security/">security rating</a>
computed by the <a href="{REPO_URL}/blob/main/tools/rating.py">Supervisor's published algorithm</a>:</p>
<div class="ratingbox"><span class="rating">🛡️ {rating["value"]}/8</span>
<ul>{steps}</ul></div>
{"<table class='perms'><thead><tr><th>Key</th><th>Value</th><th>Meaning</th><th></th></tr></thead><tbody>" + perms + "</tbody></table>" if perms else "<p>No notable permissions requested.</p>"}
"""


def health_section(entry: dict) -> str:
    gen = entry.get("generated") or {}
    meta = gen.get("repo_meta") or {}
    release = gen.get("latest_release") or {}
    facts = []
    if entry["repo"] == "home-assistant/core":
        facts.append("ships with Home Assistant core")
    elif entry["repo"] == "home-assistant/addons":
        facts.append("official Home Assistant add-on")
    if gen.get("in_hacs_default") is True:
        facts.append("in the HACS default store")
    elif gen.get("in_hacs_default") is False:
        facts.append("custom HACS repository (not in the default store)")
    if meta.get("stars") is not None:
        facts.append(f"★ {meta['stars']:,}")
    if meta.get("pushed_at"):
        facts.append(f"last push {meta['pushed_at'][:10]}")
    if release.get("tag"):
        facts.append(f"latest release {esc(release['tag'])}")
    if meta.get("license"):
        facts.append(f"license {esc(meta['license'])}")
    if meta.get("open_issues") is not None:
        facts.append(f"{meta['open_issues']:,} open issues")
    archived = '<p class="warn">⚠️ This repository is archived — the project is no longer maintained.</p>' if meta.get("archived") else ""
    manifest = gen.get("manifest") or {}
    manifest_line = ""
    if manifest.get("iot_class"):
        ev = manifest.get("evidence")
        link = f' (<a href="{evidence_url(entry, ev)}">manifest ↗</a>)' if ev else ""
        manifest_line = f"<p>Integration <code>iot_class</code>: <code>{esc(manifest['iot_class'])}</code>{link}</p>"
    return f"""<h2>Health</h2>
{archived}
<p>{" · ".join(facts) if facts else "No harvested metrics yet."}</p>
{manifest_line}"""


def audit_section(entry: dict) -> str:
    audits = entry.get("audits") or []
    if not audits:
        return ""
    items = "".join(
        f'<li>{esc(a["date"])} by {esc(a["reviewer"])} — <a href="{esc(a["url"])}">review</a> at '
        f'<code>{esc(a["reviewed_commit"][:10])}</code> '
        f'(<a href="https://github.com/{esc(entry["repo"])}/compare/{esc(a["reviewed_commit"])}...HEAD">changes since ↗</a>)</li>'
        for a in audits
    )
    return f"<h2>Audits</h2><ul>{items}</ul>"


def build_entry_page(entry: dict, harvested_at: str | None) -> str:
    inference = " · ".join(entry.get("inference", []))
    install = " · ".join(INSTALL_LABELS[i] for i in entry.get("install", []))
    providers = "".join(f'<span class="chip">{esc(p)}</span>' for p in entry.get("providers", []))
    data_sent = "".join(f"<li>{esc(d)}</li>" for d in entry.get("data_sent", [])) or "<li>nothing identified</li>"
    notes = f'<h2>Notes</h2><p>{esc(entry["notes"])}</p>' if entry.get("notes") else ""
    links = [f'<a href="https://github.com/{esc(entry["repo"])}">github.com/{esc(entry["repo"])}</a>']
    if entry.get("url"):
        links.append(f'<a href="{esc(entry["url"])}">docs</a>')
    stamp = f"Metrics harvested {esc(harvested_at[:10])} · " if harvested_at else ""
    body = f"""<header>
  <nav><a href="../../">← all {esc(CATEGORY_TITLES[entry["category"]].lower())} &amp; more</a></nav>
  <h1>{esc(entry["name"])}</h1>
  <p class="tag">{esc(entry["summary"])}</p>
  <p class="chips"><span class="chip cat">{esc(CATEGORY_TITLES[entry["category"]])}</span>
  <span class="chip">{esc(install)}</span>
  <span class="chip">inference: {esc(inference)}</span></p>
  <p>{" · ".join(links)}</p>
</header>
<h2>Capabilities</h2>
<table class="caps"><tbody>
{cap_rows(entry)}
</tbody></table>
<h2>Data flow</h2>
<p>Providers/backends: {providers or "—"}</p>
<p>What can leave your Home Assistant host:</p>
<ul>{data_sent}</ul>
{addon_section(entry)}
{health_section(entry)}
{audit_section(entry)}
{notes}
<div class="correction">
  <p><strong>Is this wrong about {esc(entry["name"])}?</strong> That's the bug we care about most —
  <a href="{correction_url(entry["id"])}">open a correction</a>. Maintainer reports get priority.</p>
</div>
<p class="stamp">{stamp}Entry added {esc(entry.get("added", ""))} ·
<a href="{REPO_URL}/blob/main/entries/{esc(entry["id"])}.yaml">entry source</a></p>"""
    return page(
        f'{entry["name"]} — Home Assistant AI Index',
        body,
        "../../style.css",
        entry["summary"],
    )


def main() -> None:
    data = build_data()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    (OUT / "index.html").write_text(build_index(data), encoding="utf-8")
    (OUT / "data.json").write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copy(SITE_DIR / "style.css", OUT / "style.css")
    shutil.copy(SITE_DIR / "app.js", OUT / "app.js")

    for entry in data["entries"]:
        page_dir = OUT / "entries" / entry["id"]
        page_dir.mkdir(parents=True)
        (page_dir / "index.html").write_text(
            build_entry_page(entry, data["harvested_at"]), encoding="utf-8"
        )
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built _site/ with {len(data['entries'])} entry pages")


if __name__ == "__main__":
    main()
