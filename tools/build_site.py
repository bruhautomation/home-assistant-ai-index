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
    CAP_TIPS,
    CAPABILITIES,
    CATEGORIES,
    CATEGORY_TITLES,
    ROOT,
    SENSITIVE,
    load_entries,
    load_generated,
    load_summary,
)

# Inline SVG icon set (24px grid, stroke-based, currentColor). One coherent
# family instead of emoji, so icons render identically everywhere and pick up
# the text color in both themes.
SVG_PATHS = {
    "reads_entity_states": '<path d="M12 6.6C10.8 5 8.9 4 6.8 4H3v14.5h4.2c1.8 0 3.6.7 4.8 2 1.2-1.3 3-2 4.8-2H21V4h-3.8c-2.1 0-4 1-5.2 2.6z"/><path d="M12 6.6V20"/>',
    "reads_history": '<path d="M3.8 12a8.4 8.4 0 1 0 2.3-5.7L3.8 8.6"/><path d="M3.8 3.6v5h5"/><path d="M12 7.6V12l3 2"/>',
    "reads_camera": '<path d="M3 8h3.2l1.9-2.6h7.8L17.8 8H21v11H3z"/><circle cx="12" cy="13.2" r="3.4"/>',
    "listens_microphone": '<rect x="9" y="2.5" width="6" height="11.5" rx="3"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0"/><path d="M12 18v3.5"/>',
    "controls_devices": '<path d="M4 7h8m5.4 0H20M4 12h3m5.4 0H20M4 17h11m5.4 0H20"/><circle cx="14.7" cy="7" r="2.2"/><circle cx="9.7" cy="12" r="2.2"/><circle cx="17.7" cy="17" r="2.2"/>',
    "creates_automations": '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M12 8.5v7M8.5 12h7"/>',
    "edits_files": '<path d="M13 4H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/><path d="M17.8 3.2a2.05 2.05 0 0 1 2.9 2.9L14 12.8l-3.7.8.8-3.7z"/>',
    "executes_code": '<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="m6.5 9.5 3.5 2.7-3.5 2.7M12.8 15h4.7"/>',
    "runs_unattended": '<circle cx="12" cy="12" r="8.8"/><path d="M10.2 8.7v6.6l5.4-3.3z"/>',
    "local": '<path d="M3.5 10.8 12 3.5l8.5 7.3"/><path d="M5.5 9.3V20h13V9.3"/>',
    "cloud": '<path d="M17.3 18.5H7a4.2 4.2 0 0 1-.6-8.4 6 6 0 0 1 11.6 1.6 3.4 3.4 0 0 1-.7 6.8z"/>',
    "shield": '<path d="M12 3 5 5.8v5.4c0 4.3 2.9 7.6 7 9.3 4.1-1.7 7-5 7-9.3V5.8z"/>',
    "star": '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8L3.5 9.7l5.9-.8z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.4-4.4"/>',
    "warn": '<path d="M12 3.5 2.5 20h19z"/><path d="M12 9.5v4.5"/><circle cx="12" cy="17" r="0.4"/>',
}


CATEGORY_SHORT = {
    "conversation-agent": "Conversation",
    "agent-platform": "Agent platform",
    "vision": "Vision",
    "automation-authoring": "Automation",
    "mcp": "MCP",
    "agent-tools": "Agent tools",
    "model-runtime": "Model runtime",
    "voice-stack": "Voice",
    "dashboard-ui": "Dashboards",
    "summaries": "Summaries",
}


def svg(name: str, cls: str = "ic") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{SVG_PATHS[name]}</svg>')

SITE_DIR = ROOT / "site"
OUT = ROOT / "_site"
REPO_URL = "https://github.com/bruhautomation/home-assistant-ai-index"
SITE_URL = "https://bruhautomation.github.io/home-assistant-ai-index"

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
        "capability_tips": CAP_TIPS,
        "capability_svgs": SVG_PATHS,
        "categories": {c: CATEGORY_TITLES[c] for c in CATEGORIES},
        "categories_short": CATEGORY_SHORT,
        "entries": merged,
    }


def page(title: str, body: str, css_path: str, description: str, canonical: str = "") -> str:
    canonical_tag = f'\n<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">{canonical_tag}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Home Assistant AI Index">
<meta property="og:image" content="https://raw.githubusercontent.com/bruhautomation/home-assistant-ai-index/main/docs/site-preview.png">
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
    tips = "".join(
        f'<li>{svg(c)}<div><strong>{esc(CAP_LABELS[c])}</strong> — {esc(CAP_TIPS[c])}</div></li>'
        for c in CAPABILITIES
    )
    body = f"""<header class="hero">
  <div class="herotop">
    <h1>Home Assistant AI Index</h1>
    <nav><a href="{REPO_URL}">GitHub</a><a href="./data.json">data</a><a href="{REPO_URL}#this-is-wrong-about-my-project">report an error</a></nav>
  </div>
  <p class="tag"><strong>What can this thing reach?</strong> Every AI project for Home Assistant,
  with its real capabilities cited to source.</p>
  <details class="howto"><summary>How to read the capability icons</summary>
    <ul class="tiplist">{tips}</ul>
    <p>Every icon on a sensitive claim links to the exact line of source that implements it,
    pinned to a commit. Hover any icon or filter for its meaning.</p>
  </details>
</header>
<button id="ftoggle" class="ftoggle" aria-expanded="false">Filters &amp; search</button>
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
        canonical=f"{SITE_URL}/",
    )


def caps_section(entry: dict) -> str:
    """Lead with what the project CAN reach; fold the rest into one line."""
    disputed = set(entry.get("disputed", []))
    evidence = entry.get("evidence", {})
    granted = [c for c in CAPABILITIES if entry["capabilities"].get(c)]
    denied = [c for c in CAPABILITIES if not entry["capabilities"].get(c)]
    rows = []
    for cap in granted:
        hot = " hot" if cap in SENSITIVE else ""
        extra = []
        if cap in evidence:
            extra.append(f'<a href="{evidence_url(entry, evidence[cap])}">source ↗</a>')
        if cap in disputed:
            extra.append(f'<span class="disputed">disputed — <a href="{correction_url(entry["id"])}">see corrections</a></span>')
        rows.append(
            f'<li class="capitem{hot}"><span class="capname">{svg(cap)} <b>{esc(CAP_LABELS[cap])}</b></span>'
            f'<span class="captip">{esc(CAP_TIPS[cap])}</span>'
            f'<span class="capev">{" · ".join(extra)}</span></li>'
        )
    reach = (f'<ul class="canreach">{"".join(rows)}</ul>' if rows
             else '<p class="noreach">Reaches nothing in Home Assistant — see the notes for what it does instead.</p>')
    notline = ""
    if denied and rows:
        notline = ('<p class="notgranted">Not granted: '
                   + " · ".join(esc(CAP_LABELS[c]) for c in denied) + "</p>")
    return f"<h2>What it can reach</h2>\n{reach}\n{notline}"


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
        gloss = {
            "cloud_polling": "talks to a cloud service on a schedule",
            "cloud_push": "a cloud service pushes to it",
            "local_polling": "polls something on your network",
            "local_push": "receives pushes on your network",
            "calculated": "derives values locally",
            "assumed_state": "assumes state without confirmation",
        }.get(manifest["iot_class"], "")
        gloss = f" — {gloss}" if gloss else ""
        manifest_line = (f"<p>Integration <code>iot_class</code> (self-declared): "
                         f"<code>{esc(manifest['iot_class'])}</code>{esc(gloss)}{link}</p>")
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
    shot = (entry.get("generated") or {}).get("screenshot")
    screenshot = ""
    if shot:
        screenshot = f"""<figure class="shot">
  <a href="{esc(shot["url"])}"><img src="{esc(shot["url"])}" alt="Screenshot of {esc(entry["name"])}" loading="lazy" onerror="this.closest('figure').remove()"></a>
  <figcaption>From the project's README at the pinned commit.</figcaption>
</figure>"""
    body = f"""<header>
  <nav><a href="../../">← all {esc(CATEGORY_TITLES[entry["category"]].lower())} &amp; more</a></nav>
  <h1>{esc(entry["name"])}</h1>
  <p class="tag">{esc(entry["summary"])}</p>
  <p class="chips"><span class="chip cat">{esc(CATEGORY_TITLES[entry["category"]])}</span>
  <span class="chip">{esc(install)}</span>
  <span class="chip">inference: {esc(inference)}</span></p>
  <p>{" · ".join(links)}</p>
</header>
{screenshot}
{caps_section(entry)}
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
        canonical=f"{SITE_URL}/entries/{entry['id']}/",
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
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/entries/{e['id']}/" for e in data["entries"]]
    sitemap = "\n".join(
        ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        + [f"  <url><loc>{u}</loc></url>" for u in urls]
        + ["</urlset>", ""]
    )
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built _site/ with {len(data['entries'])} entry pages")


if __name__ == "__main__":
    main()
