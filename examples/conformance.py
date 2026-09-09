# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Run every published conformance vector against the independent reference.

Loads the conformance manifest and vectors from the published artifact tree and
drives them through `deontic_reference` (which imports no product code). A
statement vector must parse, validate, and project to its `expected.json`; a
negative vector must be rejected at its declared stage. Exits non-zero on any
mismatch — this is the third-party implementability proof for the DoD.

Run standalone: python3 examples/conformance.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deontic_reference as ref  # noqa: E402

_VECTORS = Path(__file__).resolve().parent.parent / "src" / "deontic" / "artifacts" / "conformance"


def _manifest() -> dict:
    return json.loads((_VECTORS / "manifest.json").read_text(encoding="utf-8"))


def _vector_file(name: str, filename: str):
    return json.loads((_VECTORS / "vectors" / name / filename).read_text(encoding="utf-8"))


def _check(vector: dict) -> None:
    name, kind = vector["name"], vector["kind"]
    source = (_VECTORS / "vectors" / name / "input.deo").read_text(encoding="utf-8")
    if kind == "negative":
        stage = str(vector.get("stage", ""))
        try:
            formula = ref.parse(source)
        except Exception:
            if stage == "parse":
                return
            raise AssertionError(f"{name}: rejected at parse instead of {stage}")
        report = ref.validate(formula)
        if stage != "validate" or report.get("ok", True):
            raise AssertionError(f"{name}: expected {stage} rejection")
        return
    formula = ref.parse(source)
    report = ref.validate(formula)
    if not report.get("ok"):
        raise AssertionError(f"{name}: unexpected validate rejection: {report.get('errors')}")
    if ref.project(formula) != _vector_file(name, "expected.json"):
        raise AssertionError(f"{name}: projection mismatch")


def main() -> int:
    vectors = _manifest()["vectors"]
    failures = []
    for v in vectors:
        try:
            _check(v)
        except Exception as exc:
            failures.append(f"{type(exc).__name__}: {exc}")
    print(f"reference conformance: {len(vectors) - len(failures)}/{len(vectors)} vectors pass")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
