# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Validate every statement vector's expected.json against the published schema.

A statement vector's `expected.json` is the canonical structured projection; it
must satisfy `statement.schema.json`. This catches a vector drifting from the
schema (a renamed field, an out-of-enum operator or incident) before it is
published. Uses jsonschema; stdlib otherwise.

Run standalone: python3 -m pip install jsonschema && python3 tools/check_vectors.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ART = Path(__file__).resolve().parent.parent / "src" / "deontic" / "artifacts"


def main() -> int:
    schema = json.loads((ART / "schema" / "statement.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((ART / "conformance" / "manifest.json").read_text(encoding="utf-8"))
    failures = []
    checked = 0
    for v in manifest["vectors"]:
        if v["kind"] != "statement":
            continue
        expected_path = ART / "conformance" / "vectors" / v["name"] / "expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        checked += 1
        try:
            jsonschema.validate(expected, schema)
        except jsonschema.ValidationError as exc:
            failures.append(f"{v['name']}: {exc.message}")
    print(f"vector-schema gate: {checked - len(failures)}/{checked} expected.json valid")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
