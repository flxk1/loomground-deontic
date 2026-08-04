# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Hold the published extraction cues equal to the language.

`artifacts/extraction.json` lets a generic consumer (the ingest plane) lower free
text into deontic deterministically, without any deontic code. That is only safe
if the published cues cannot drift from the language they claim to describe. This
gate proves they have not:

  A. Incident cues — the power-verb and immunity regex sources equal the compiled
     sources in `deontic.incidents`.
  B. Operator mapping / axis — `modal_operator` and `operator_axis` equal the
     language's modal→operator and the contract's dimension affinity.
  C. Incident rules — applying the published rules reproduces
     `deontic.incidents.classify_incident` over an oracle set covering every branch.
  D. Regex validity — every published pattern compiles.

Run standalone: python3 tools/check_extraction.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import deontic  # noqa: E402
from deontic import incidents as di  # noqa: E402
from deontic import contract  # noqa: E402

EX = json.loads((SRC / "deontic" / "artifacts" / "extraction.json").read_text(encoding="utf-8"))


def check_incident_cues() -> list[str]:
    fails = []
    if EX["incident_cues"]["power_verb"] != di._POWER_VERBS.pattern:
        fails.append("incident_cues.power_verb != deontic.incidents._POWER_VERBS")
    if EX["incident_cues"]["immunity"] != di._IMMUNITY_CUES.pattern:
        fails.append("incident_cues.immunity != deontic.incidents._IMMUNITY_CUES")
    return fails


def check_operator_mapping() -> list[str]:
    fails = []
    expected_op = {"obligation": deontic.OP_OBLIGATION, "permission": deontic.OP_PERMISSION,
                   "prohibition": deontic.OP_PROHIBITION}
    if EX["modal_operator"] != expected_op:
        fails.append(f"modal_operator {EX['modal_operator']} != language {expected_op}")
    expected_axis = {op: contract.dimension_affinity(op) for op in deontic.VALID_OPERATORS}
    if EX["operator_axis"] != expected_axis:
        fails.append(f"operator_axis {EX['operator_axis']} != contract affinity {expected_axis}")
    if EX["dimension"] != "nD":
        fails.append(f"dimension {EX['dimension']!r} != 'nD'")
    return fails


def _apply_rules(modal: str, action: str, raw: str) -> str:
    blob = f"{action} {raw}"
    cues = EX["incident_cues"]
    for rule in EX["incident_rules"]:
        if rule["modal"] != modal:
            continue
        wm = rule.get("when_matches")
        if wm and not re.search(cues[wm], blob, re.I):
            continue
        return rule["incident"]
    return ""


# Oracle set: (modal, action, raw) covering every incident branch.
_ORACLE = [
    ("obligation", "notify the authority", "shall notify"),
    ("prohibition", "disclose the data", "must not disclose"),
    ("prohibition", "assign the contract", "may not assign"),          # power verb -> disability
    ("prohibition", "be amended", "this agreement may not be amended"),  # immunity cue
    ("permission", "terminate the contract", "may terminate"),          # power verb -> power
    ("permission", "access the record", "may access"),                  # -> privilege
]


def check_incident_rules() -> list[str]:
    fails = []
    for modal, action, raw in _ORACLE:
        want = di.classify_incident(modal, action, raw)
        got = _apply_rules(modal, action, raw)
        if got != want:
            fails.append(f"rules[{modal},{action!r}] -> {got!r}, language says {want!r}")
    return fails


def check_regex_validity() -> list[str]:
    fails = []
    patterns = [c["pattern"] for c in EX["modal_cues"]]
    patterns += list(EX["incident_cues"].values())
    patterns += list(EX["slot_cues"].values())
    for section in ("deadline_cues", "cross_reference_cues", "sanction_cues"):
        patterns += list(EX.get(section, {}).values())
    for p in patterns:
        try:
            re.compile(p)
        except re.error as exc:
            fails.append(f"invalid regex {p!r}: {exc}")
    return fails


_CHECKS = (
    ("incident cues equal the language", check_incident_cues),
    ("operator mapping / axis equal the language", check_operator_mapping),
    ("incident rules reproduce classify_incident", check_incident_rules),
    ("every published pattern compiles", check_regex_validity),
)


def test_extraction_in_sync():
    fails = [f for _, fn in _CHECKS for f in fn()]
    assert not fails, "extraction drift:\n  " + "\n  ".join(fails)


if __name__ == "__main__":
    total = 0
    print(f"extraction-sync gate against {ROOT}\n")
    for label, fn in _CHECKS:
        fails = fn()
        total += len(fails)
        print(f"[{'PASS' if not fails else 'FAIL'}] {label}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{'ALL GREEN' if total == 0 else str(total) + ' drift(s)'}")
    sys.exit(0 if total == 0 else 1)
