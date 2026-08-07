"""Shared loading helpers for the index tools."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "entries"
GENERATED_DIR = ROOT / "data" / "generated"
SCHEMA_PATH = ROOT / "schema" / "entry.schema.json"

CAPABILITIES = [
    "reads_entity_states",
    "reads_history",
    "reads_camera",
    "listens_microphone",
    "controls_devices",
    "creates_automations",
    "edits_files",
    "executes_code",
    "runs_unattended",
]

# Flags that require a source citation when true (see CONTRIBUTING.md).
SENSITIVE = [
    "reads_camera",
    "listens_microphone",
    "edits_files",
    "executes_code",
    "runs_unattended",
]

CAP_ICONS = {
    "reads_entity_states": "📖",
    "reads_history": "📜",
    "reads_camera": "📷",
    "listens_microphone": "🎙️",
    "controls_devices": "🎛️",
    "creates_automations": "⚙️",
    "edits_files": "📝",
    "executes_code": "⚡",
    "runs_unattended": "⏰",
}

CAP_LABELS = {
    "reads_entity_states": "reads states",
    "reads_history": "reads history",
    "reads_camera": "reads camera",
    "listens_microphone": "microphone",
    "controls_devices": "controls devices",
    "creates_automations": "creates automations",
    "edits_files": "edits files",
    "executes_code": "executes code",
    "runs_unattended": "unattended",
}

# One-line plain-language explanations, used as tooltips on the site.
CAP_TIPS = {
    "reads_entity_states": "Can read the live state of entities exposed to it — temperatures, lights, locks, presence.",
    "reads_history": "Can query past states and events from the recorder, history, or logbook.",
    "reads_camera": "Can access camera images or streams.",
    "listens_microphone": "Processes live audio — voice commands, wake words, or ambient sound.",
    "controls_devices": "Can call Home Assistant services to switch, dim, unlock, or otherwise act on devices.",
    "creates_automations": "Can write automations, scripts, or helpers into your configuration.",
    "edits_files": "Can write to configuration files or the filesystem beyond its own storage.",
    "executes_code": "Can run arbitrary code — shell commands or generated scripts.",
    "runs_unattended": "Starts AI activity by itself on schedules, watchers, or triggers — no human in the loop.",
}

CATEGORIES = [
    "conversation-agent",
    "agent-platform",
    "vision",
    "automation-authoring",
    "mcp",
    "agent-tools",
    "model-runtime",
    "voice-stack",
    "dashboard-ui",
    "summaries",
]

CATEGORY_TITLES = {
    "conversation-agent": "Conversation agents",
    "agent-platform": "Agent platforms",
    "vision": "Vision",
    "automation-authoring": "Automation authoring",
    "mcp": "Model Context Protocol",
    "agent-tools": "Agent tools & frameworks",
    "model-runtime": "Model runtimes",
    "voice-stack": "Voice stack",
    "dashboard-ui": "Dashboards & UI",
    "summaries": "Summaries & briefings",
}


def _stringify_dates(value):
    """YAML parses bare dates into date objects; the schema (and JSON) want strings."""
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _stringify_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify_dates(v) for v in value]
    return value


def load_entries() -> list[dict]:
    entries = []
    for path in sorted(ENTRIES_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            entry = _stringify_dates(yaml.safe_load(f))
        entry["_file"] = path.name
        entries.append(entry)
    return entries


def load_generated(entry_id: str) -> dict:
    path = GENERATED_DIR / f"{entry_id}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_summary() -> dict:
    path = GENERATED_DIR / "summary.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)
