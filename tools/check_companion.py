# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Keep the bundled skill engine in lockstep with the language.

`skills/deontic/deontic_engine.py` is a self-contained copy of the language
surface shipped with the skill so it runs without the package installed. That
convenience becomes a liability the moment it drifts. This gate proves it has not:

  A. Conformance — the bundled engine reproduces every published vector (a
     statement parses/validates/projects to its expected.json; a negative is
     rejected at its stage), exactly as the product does.
  B. Vocabulary — the engine's operators and incidents equal the published card.

Run standalone: python3 tools/check_companion.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "src" / "deontic" / "artifacts"
sys.path.insert(0, str(ROOT / "skills" / "deontic"))
import deontic_engine as eng  # noqa: E402


def _vectors_dir():
    return ART / "conformance" / "vectors"


def check_conformance() -> list[str]:
    manifest = json.loads((ART / "conformance" / "manifest.json").read_text(encoding="utf-8"))
    fails = []
    for v in manifest["vectors"]:
        name, kind = v["name"], v["kind"]
        src = (_vectors_dir() / name / "input.deo").read_text(encoding="utf-8")
        if kind == "negative":
            try:
                eng.validate(eng.parse(src))
            except eng.DeonticSyntaxError:
                continue
            if str(v.get("stage")) == "parse":
                fails.append(f"{name}: engine accepted a parse-reject vector")
            continue
        try:
            formula = eng.parse(src)
            report = eng.validate(formula)
        except eng.DeonticSyntaxError as exc:
            fails.append(f"{name}: engine rejected a valid statement ({exc})")
            continue
        if not report["ok"]:
            fails.append(f"{name}: engine validate failed ({report['errors']})")
            continue
        expected = json.loads((_vectors_dir() / name / "expected.json").read_text(encoding="utf-8"))
        if eng.project(formula) != expected:
            fails.append(f"{name}: engine projection differs from expected.json")
    return fails


def check_vocabulary() -> list[str]:
    card = json.loads((ART / "deontic-card.json").read_text(encoding="utf-8"))
    fails = []
    if list(eng.OPERATORS) != list(card.get("operators", [])):
        fails.append(f"engine operators {list(eng.OPERATORS)} != card {card.get('operators')}")
    if list(eng.INCIDENTS) != list(card.get("incidents", [])):
        fails.append(f"engine incidents drift from card {card.get('incidents')}")
    return fails


def check_signed_conflicts() -> list[str]:
    """The companion preserves proposition polarity in collision checks."""
    obligation = eng._formula("O", "x", "act")
    refrain = eng._formula("O", "x", "act", negated=True)
    prohibition = eng._formula("F", "x", "act")
    fails = []
    if len(eng.detect_conflicts([obligation, refrain])) != 1:
        fails.append("engine missed O(a) / O(¬a)")
    if eng.detect_conflicts([refrain, prohibition]):
        fails.append("engine flagged equivalent O(¬a) / F(a)")
    return fails


if __name__ == "__main__":
    total = 0
    print(f"companion drift gate against {ROOT}\n")
    for label, fn in (("bundled engine reproduces every vector", check_conformance),
                      ("engine vocabulary equals the card", check_vocabulary),
                      ("engine preserves signed conflicts", check_signed_conflicts)):
        fails = fn()
        total += len(fails)
        print(f"[{'PASS' if not fails else 'FAIL'}] {label}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{'ALL GREEN' if total == 0 else str(total) + ' drift(s)'}")
    sys.exit(0 if total == 0 else 1)
