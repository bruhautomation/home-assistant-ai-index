#!/usr/bin/env python3
"""Validate entry files against the schema and the evidence policy.

Checks, per entries/*.yaml:
  1. JSON Schema (schema/entry.schema.json)
  2. filename matches the entry id
  3. every sensitive capability set to true carries a source citation
     (the whole premise of this index — see CONTRIBUTING.md)

Exit code is non-zero on any failure, so this doubles as the CI gate.
"""

from __future__ import annotations

import json
import sys

import jsonschema

from common import ENTRIES_DIR, SCHEMA_PATH, SENSITIVE, load_entries


def validate() -> int:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)

    failures = []
    entries = load_entries()
    seen_ids = set()

    for entry in entries:
        fname = entry.pop("_file")
        label = f"entries/{fname}"

        for error in validator.iter_errors(entry):
            where = "/".join(str(p) for p in error.absolute_path) or "(root)"
            failures.append(f"{label}: schema: {where}: {error.message}")
            continue

        entry_id = entry.get("id")
        if entry_id:
            if f"{entry_id}.yaml" != fname:
                failures.append(f"{label}: id '{entry_id}' does not match filename")
            if entry_id in seen_ids:
                failures.append(f"{label}: duplicate id '{entry_id}'")
            seen_ids.add(entry_id)

        caps = entry.get("capabilities", {})
        evidence = entry.get("evidence", {})
        for flag in SENSITIVE:
            if caps.get(flag) and flag not in evidence:
                failures.append(
                    f"{label}: '{flag}' is true but has no source citation — "
                    f"sensitive claims must cite {{path, line, commit}} (see CONTRIBUTING.md)"
                )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"\n{len(failures)} problem(s) in {len(entries)} entries.")
        return 1

    print(f"OK: {len(entries)} entries valid ({ENTRIES_DIR}).")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
