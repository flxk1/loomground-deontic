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
  C. Power-verb cue parity — the package (`deontic.incidents`) and the
     bundled engine each carry their own copy of `_POWER_VERBS` and the
     narrower `_has_active_require` "require" gate (a Hohfeld-power reading
     of "require" that fires only on the active forms "require"/"requires"/
     "requiring", never any form of "required" — see `deontic.incidents`'s
     comment for why). This gate holds the two regex sources and the two
     helper functions' behaviour over a shared probe set equal, and also
     calls `classify_incident` itself on both sides (not only the bare
     helper), so a scope regression at the call site — checking the whole
     raw sentence instead of the action span — cannot pass silently either.

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
sys.path.insert(0, str(ROOT / "src"))
import deontic.incidents as di  # noqa: E402


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


_REQUIRE_PROBES = (
    "require the borrower to provide additional security",
    "require",
    "requires",
    "requiring",
    "required",
    "is required",
    "was required",
    "required by Article 5",
    "unless required by Union law",
    "as required under Union law",
    "required pursuant to Article 6",
    "where required",
    "requirement",
    "requirements",
    "specific requirements laid down",
    "the controller shall require the processor to delete the data",
    "an authorised representative",
)

# (modal, action, raw) pairs exercising classify_incident ITSELF on both
# sides, not only the bare helper — including the action-only-scope case: an
# active "require" sitting outside `action` (here, in the sentence's
# condition) must not turn an unrelated permission into a power on either
# side.
_CLASSIFY_PROBES = (
    ("permission", "require the borrower to provide additional security",
     "The lender may require the borrower to provide additional security."),
    ("prohibition", "require any specific authorisation",
     "Such a transfer shall not require any specific authorisation."),
    ("permission", "store the data",
     "Where the law requires, the controller may store the data."),
    ("permission", "submit the documents required pursuant to Article 5",
     "The applicant may submit the documents required pursuant to Article 5."),
    ("prohibition", "engage another processor without prior written authorisation",
     "The processor shall not engage another processor without prior written authorisation."),
)


def check_power_verb_parity() -> list[str]:
    """The engine's `_POWER_VERBS`/`_has_active_require`/`classify_incident`
    must equal the package's, source and behaviour, so a power-verb fix (or
    regression) reaches skill users too."""
    fails = []
    if eng._POWER_VERBS.pattern != di._POWER_VERBS.pattern:
        fails.append("engine _POWER_VERBS.pattern != package _POWER_VERBS.pattern")
    for probe in _REQUIRE_PROBES:
        engine_hit = eng._has_active_require(probe)
        package_hit = di._has_active_require(probe)
        if engine_hit != package_hit:
            fails.append(
                f"_has_active_require({probe!r}): engine={engine_hit} package={package_hit}")
    for modal, action, raw in _CLASSIFY_PROBES:
        engine_inc = eng.classify_incident(modal, action, raw)
        package_inc = di.classify_incident(modal, action, raw)
        if engine_inc != package_inc:
            fails.append(
                f"classify_incident({modal!r}, {action!r}, ...): "
                f"engine={engine_inc} package={package_inc}")
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
                      ("engine power-verb cues equal the package", check_power_verb_parity),
                      ("engine preserves signed conflicts", check_signed_conflicts)):
        fails = fn()
        total += len(fails)
        print(f"[{'PASS' if not fails else 'FAIL'}] {label}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{'ALL GREEN' if total == 0 else str(total) + ' drift(s)'}")
    sys.exit(0 if total == 0 else 1)
