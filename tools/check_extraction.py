# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Hold the published extraction cues equal to the language.

`artifacts/extraction.json` is sufficient on its own for a generic consumer (the
ingest plane) to lower free text into deontic deterministically without importing
any deontic code. The package also ships a reference producer, `deontic.prose`,
which reads these same published cues at runtime. Either way the data is only
safe if the published cues cannot drift from the language they claim to describe.
This gate proves they have not:

  A. Incident cues — the power-verb and immunity regex sources equal the compiled
     sources in `deontic.incidents`.
  B. Operator mapping / axis — `modal_operator` equals the language's
     modal→operator, and `operator_axis` equals the binding pinned HERE
     (`EXPECTED_OPERATOR_AXIS`: O/F -> causal, P -> intentional, decision D1) and
     names only dimensions `vocabulary/dimensions.json` publishes. The pin is held
     in this checker on purpose: `deontic.contract.dimension_affinity` now reads
     `operator_axis` itself, so comparing against it would compare the artifact
     with itself and could never fail. Changing the binding means changing this
     pin in the same commit, in review.
  C. Incident rules — applying the published rules reproduces
     `deontic.incidents.classify_incident` over an oracle set covering every branch.
  D. Regex validity — every published pattern compiles.
  E. Validity rules — every effect in `validity_rules` is carried by a cue and
     vice versa, and every non-abstaining incident names a real Hohfeld incident.

Run standalone: python3 tools/check_extraction.py [--artifact PATH]
(`--artifact` checks another copy of extraction.json; the tests use it to prove
the gate fails on a mutated copy.)
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

ARTIFACT = SRC / "deontic" / "artifacts" / "extraction.json"
DIMENSIONS = SRC / "deontic" / "artifacts" / "vocabulary" / "dimensions.json"

# Gate B's independent expectation (decision D1): an obligation or a prohibition
# is triggered by its condition (causal); a permission exists for its bearer's
# benefit (intentional). Deliberately NOT read from extraction.json or from
# deontic.contract (which reads extraction.json).
EXPECTED_OPERATOR_AXIS = {"O": "causal", "F": "causal", "P": "intentional"}


def load(path: Path = ARTIFACT) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


EX = load()


def check_incident_cues(ex: dict | None = None) -> list[str]:
    ex = EX if ex is None else ex
    fails = []
    if ex["incident_cues"]["power_verb"] != di._POWER_VERBS.pattern:
        fails.append("incident_cues.power_verb != deontic.incidents._POWER_VERBS")
    if ex["incident_cues"]["immunity"] != di._IMMUNITY_CUES.pattern:
        fails.append("incident_cues.immunity != deontic.incidents._IMMUNITY_CUES")
    return fails


def check_operator_mapping(ex: dict | None = None) -> list[str]:
    ex = EX if ex is None else ex
    fails = []
    expected_op = {"obligation": deontic.OP_OBLIGATION, "permission": deontic.OP_PERMISSION,
                   "prohibition": deontic.OP_PROHIBITION}
    if ex["modal_operator"] != expected_op:
        fails.append(f"modal_operator {ex['modal_operator']} != language {expected_op}")
    axis = ex["operator_axis"]
    if set(EXPECTED_OPERATOR_AXIS) != set(deontic.VALID_OPERATORS):
        fails.append(f"pinned axis operators {sorted(EXPECTED_OPERATOR_AXIS)} != "
                     f"language operators {sorted(deontic.VALID_OPERATORS)}")
    if axis != EXPECTED_OPERATOR_AXIS:
        fails.append(f"operator_axis {axis} != pinned D1 binding {EXPECTED_OPERATOR_AXIS}")
    published = {d["name"] for d in load(DIMENSIONS)["dimensions"]}
    unknown = {op: dim for op, dim in axis.items() if dim not in published}
    if unknown:
        fails.append(f"operator_axis names dimensions not in dimensions.json: {unknown}")
    if ex["dimension"] != "nD":
        fails.append(f"dimension {ex['dimension']!r} != 'nD'")
    return fails


def _apply_rules(modal: str, action: str, raw: str, ex: dict | None = None) -> str:
    ex = EX if ex is None else ex
    blob = f"{action} {raw}"
    cues = ex["incident_cues"]
    for rule in ex["incident_rules"]:
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


def check_incident_rules(ex: dict | None = None) -> list[str]:
    ex = EX if ex is None else ex
    fails = []
    for modal, action, raw in _ORACLE:
        want = di.classify_incident(modal, action, raw)
        got = _apply_rules(modal, action, raw, ex)
        if got != want:
            fails.append(f"rules[{modal},{action!r}] -> {got!r}, language says {want!r}")
    return fails


def check_regex_validity(ex: dict | None = None) -> list[str]:
    ex = EX if ex is None else ex
    fails = []
    patterns = [c["pattern"] for c in ex["modal_cues"]]
    patterns += [c["pattern"] for c in ex.get("validity_cues", [])]
    patterns += list(ex["incident_cues"].values())
    patterns += list(ex["slot_cues"].values())
    for section in ("deadline_cues", "cross_reference_cues", "sanction_cues"):
        patterns += list(ex.get(section, {}).values())
    for p in patterns:
        try:
            re.compile(p)
        except re.error as exc:
            fails.append(f"invalid regex {p!r}: {exc}")
    return fails


def check_validity_rules(ex: dict | None = None) -> list[str]:
    """Validity is constitutive, not a fourth operator: rules may only map an
    effect its cues actually carry onto a real Hohfeld incident (or abstain)."""
    ex = EX if ex is None else ex
    fails = []
    cue_effects = {c["effect"] for c in ex.get("validity_cues", [])}
    rule_effects = {r["effect"] for r in ex.get("validity_rules", [])}
    for effect in sorted(rule_effects - cue_effects):
        fails.append(f"validity_rules effect {effect!r} has no cue carrying it")
    for effect in sorted(cue_effects - rule_effects):
        fails.append(f"validity_cues effect {effect!r} has no incident rule")
    for rule in ex.get("validity_rules", []):
        incident = rule.get("incident")
        if incident and incident not in di.INCIDENTS:
            fails.append(f"validity_rules[{rule['effect']}] incident {incident!r} "
                         f"is not a Hohfeld incident")
    return fails


_CHECKS = (
    ("incident cues equal the language", check_incident_cues),
    ("operator mapping equals the language; axis equals the pinned D1 binding", check_operator_mapping),
    ("incident rules reproduce classify_incident", check_incident_rules),
    ("every published pattern compiles", check_regex_validity),
    ("validity rules stay on the published incidents", check_validity_rules),
)


def run(ex: dict | None = None) -> list[str]:
    """Every gate's failures over ``ex`` (default: the packaged artifact)."""
    return [f for _, fn in _CHECKS for f in fn(ex)]


def test_extraction_in_sync():
    fails = [f for _, fn in _CHECKS for f in fn()]
    assert not fails, "extraction drift:\n  " + "\n  ".join(fails)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--artifact", type=Path, default=ARTIFACT,
                    help="extraction.json to check (default: the packaged one)")
    target = ap.parse_args().artifact
    ex_arg = load(target)
    total = 0
    print(f"extraction-sync gate against {target}\n")
    for label, fn in _CHECKS:
        fails = fn(ex_arg)
        total += len(fails)
        print(f"[{'PASS' if not fails else 'FAIL'}] {label}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{'ALL GREEN' if total == 0 else str(total) + ' drift(s)'}")
    sys.exit(0 if total == 0 else 1)
