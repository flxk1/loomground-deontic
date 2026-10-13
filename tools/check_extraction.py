# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Hold the published extraction cues equal to the language.

`artifacts/extraction.json` is sufficient on its own for a generic consumer (the
ingest plane) to lower free text into deontic deterministically without importing
any deontic code. The package's own reference producer, `deontic.prose`, does
**not** read this file at runtime: Phase 1 replaced the regex walk with a
stdlib recursive-descent parser (`deontic.prose_grammar`) driven by the JSON
gazetteers under `artifacts/gazetteer/*.json`. The two surfaces are kept from
drifting apart the same way as everything else this gate checks — by equality,
not by one reading the other: Gate F below checks every gazetteer-published cue
(modal phrases, negation adverbs, negating interposed phrases, condition
leads/tails, exception leads) is still covered by this file's regex cues, so a
consumer that only has `extraction.json` never falls behind what the package's
own parser actually recognises. Either way the data is only safe if the
published cues cannot drift from the language they claim to describe. This gate
proves they have not:

  A. Incident cues — the power-verb and immunity regex sources equal the compiled
     sources in `deontic.incidents`, and `require_power_cue`'s structured data
     equals `deontic.incidents`' own "require" constants ("require" is
     deliberately NOT a `power_verb` regex alternative — see
     `require_power_cue`'s own `describes` for why — so it gets its own
     equality check here).
  B. Operator mapping / no-dimension rule (Round 4, deontic-is-ought correction:
     D1 reversed) — `modal_operator` equals the language's modal→operator, and
     the published artifact carries NO operator->5D-dimension binding at all:
     no key named `operator_axis` (or any operator->dimension map, under any
     name, anywhere in the artifact) is present. Operators (O/P/F) are OUGHT —
     the 5D describes what IS — so no operator may be bound to a 5D dimension;
     a norm's content enters 5D only through the factual plane. This gate is
     independent of `deontic.contract.dimension_affinity` and
     `deontic.plane.binding` on purpose (both are also asserted, elsewhere, to
     return no dimension for any operator) — Gate B fails on the ARTIFACT
     itself carrying an operator->dimension map, a stricter and independent
     guard than merely trusting the code that reads it.
  C. Incident rules — applying the published rules reproduces
     `deontic.incidents.classify_incident` over an oracle set covering every branch.
  D. Regex validity — every published pattern compiles.
  E. Validity rules — every effect in `validity_rules` is carried by a cue and
     vice versa, and every non-abstaining incident names a real Hohfeld incident.
  F. Gazetteer sync — every cue `deontic.prose_grammar` actually dispatches on
     (read from `artifacts/gazetteer/*.json`, the parser's single source of
     truth) is matched by this file's `modal_cues`/`slot_cues` regex, so the
     two published surfaces cannot silently diverge.
  G. Gazetteer sync, reverse direction — for `condition_lead`,
     `condition_lead_with_phrase` and `exception_lead`, every ENGLISH literal
     alternative actually published in the regex is also a gazetteer
     `lead_phrases` entry, so this file cannot carry an English alternative
     the parser does not recognise (Gate F alone only catches the opposite
     drift — a gazetteer entry missing from the regex). German alternatives
     are exempted by an explicit, documented allowlist
     (`_NON_ENGLISH_ALTERNATIVES`): the gazetteer-driven parser is
     English-only (Phase 1 scope, `modal_lexemes.json`), so extraction.json's
     German alternatives are a deliberate, pre-existing asymmetry for a
     generic (code-independent) consumer, not a drift this gate polices.

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
GAZETTEER_DIR = SRC / "deontic" / "artifacts" / "gazetteer"

# Gate B's independent rule (Round 4, D1 reversed): ought carries no 5D
# dimension. No dict anywhere in the published artifact may map an operator (or
# a subset of the operators) to a 5D dimension name — under `operator_axis` or
# any other key. Deliberately NOT read from `deontic.contract` (which no longer
# reads any such mapping either, but this gate does not trust that).
FIVE_DIMENSIONS = {"structural", "causal", "intentional", "temporal", "relational"}


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
    req = ex.get("require_power_cue", {})
    if set(req.get("active_forms", [])) != set(di._REQUIRE_FORMS):
        fails.append("require_power_cue.active_forms != "
                      "deontic.incidents._REQUIRE_FORMS")
    if req.get("scope") != "action":
        fails.append("require_power_cue.scope != 'action'")
    return fails


def _operator_dimension_maps(obj, path=()):
    """Every dict anywhere in ``obj`` whose keys are a (non-empty) subset of the
    deontic operators and whose values are all 5D dimension names — i.e. any
    shape of an operator->dimension binding, under any key."""
    if isinstance(obj, dict):
        if obj and set(obj) <= set(deontic.VALID_OPERATORS) and \
                all(isinstance(v, str) and v in FIVE_DIMENSIONS for v in obj.values()):
            yield path
        for k, v in obj.items():
            yield from _operator_dimension_maps(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _operator_dimension_maps(v, path + (i,))


def check_operator_mapping(ex: dict | None = None) -> list[str]:
    ex = EX if ex is None else ex
    fails = []
    expected_op = {"obligation": deontic.OP_OBLIGATION, "permission": deontic.OP_PERMISSION,
                   "prohibition": deontic.OP_PROHIBITION}
    if ex["modal_operator"] != expected_op:
        fails.append(f"modal_operator {ex['modal_operator']} != language {expected_op}")
    if "operator_axis" in ex:
        fails.append("extraction.json still carries operator_axis: ought binds no 5D dimension")
    hits = list(_operator_dimension_maps(ex))
    if hits:
        fails.append(f"extraction.json carries an operator->5D-dimension map at {hits}: "
                     "ought binds no 5D dimension")
    if ex["dimension"] != "nD":
        fails.append(f"dimension {ex['dimension']!r} != 'nD'")
    return fails


def _matches_cue(ex: dict, wm: str, action: str, raw: str) -> bool:
    """A `when_matches` cue is either a regex in `incident_cues` (checked over
    `action + raw`), or `require_power_cue` — structured data, checked over
    `action` ONLY, by plain word membership (a generic consumer applies this
    without a regex and without importing any code)."""
    if wm == "require_power_cue":
        req = ex.get("require_power_cue", {})
        words = {w.lower() for w in re.findall(r"[A-Za-z]+", action or "")}
        return bool(words & set(req.get("active_forms", [])))
    blob = f"{action} {raw}"
    return bool(re.search(ex["incident_cues"][wm], blob, re.I))


def _apply_rules(modal: str, action: str, raw: str, ex: dict | None = None) -> str:
    ex = EX if ex is None else ex
    for rule in ex["incident_rules"]:
        if rule["modal"] != modal:
            continue
        wm = rule.get("when_matches")
        if wm and not _matches_cue(ex, wm, action, raw):
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
    ("permission",
     "require controllers to consult with, and obtain prior authorisation "
     "from, the supervisory authority",
     "Member State law may require controllers to consult with, and obtain "
     "prior authorisation from, the supervisory authority."),           # require -> power
    ("prohibition", "require any specific authorisation",
     "Such a transfer shall not require any specific authorisation."),  # require -> disability
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


def _load_gazetteer(name: str) -> dict:
    return json.loads((GAZETTEER_DIR / f"{name}.json").read_text(encoding="utf-8"))


def check_gazetteer_sync(ex: dict | None = None) -> list[str]:
    """Gate F: every cue the gazetteer-driven parser dispatches on is still
    matched by this file's regex cues (see the module docstring, Gate F)."""
    ex = EX if ex is None else ex
    fails: list[str] = []
    slot = ex["slot_cues"]
    modal_patterns = {c["modal"]: c["pattern"] for c in ex["modal_cues"]}
    lexeme_to_modal = {"shall": "obligation", "must": "obligation", "may": "permission"}

    modal_gaz = _load_gazetteer("modal_lexemes")
    for entry in modal_gaz["phrases"]:
        phrase = entry["phrase"]
        modal = "prohibition" if entry.get("operator") == "F" else lexeme_to_modal[entry["lexeme"]]
        if not re.search(modal_patterns[modal], phrase, re.I):
            fails.append(f"gazetteer modal phrase {phrase!r} (-> {modal}) not "
                         f"covered by extraction.json modal_cues[{modal}]")

    neg_gaz = _load_gazetteer("negation")
    for adverb in neg_gaz["adverbs"]:
        probe = f"shall {adverb} disclose"
        if not re.search(modal_patterns["prohibition"], probe, re.I):
            fails.append(f"gazetteer negation adverb {adverb!r} not covered by "
                         "extraction.json modal_cues[prohibition]")

    interposed_gaz = _load_gazetteer("interposed")
    for entry in interposed_gaz["phrases"]:
        if not entry.get("negating"):
            continue
        probe = f"shall {entry['phrase']} disclose"
        if not re.search(modal_patterns["prohibition"], probe, re.I):
            fails.append(f"gazetteer negating interposed phrase {entry['phrase']!r} "
                         "not covered by extraction.json modal_cues[prohibition]")

    cond_gaz = _load_gazetteer("condition")
    for entry in cond_gaz["lead_phrases"]:
        phrase = entry["phrase"] if isinstance(entry, dict) else entry
        keep_lead = isinstance(entry, dict) and entry.get("keep_lead")
        probe = f"{phrase} X,"
        pattern = slot["condition_lead_with_phrase"] if keep_lead else slot["condition_lead"]
        if not re.search(pattern, probe, re.I):
            key = "condition_lead_with_phrase" if keep_lead else "condition_lead"
            fails.append(f"gazetteer condition lead {phrase!r} not covered by "
                         f"extraction.json slot_cues.{key}")
    for phrase in cond_gaz["tail_leads"]:
        probe = f" {phrase} it is sent"
        if not re.search(slot["condition_tail"], probe, re.I):
            fails.append(f"gazetteer condition tail lead {phrase!r} not covered by "
                         "extraction.json slot_cues.condition_tail")

    exc_gaz = _load_gazetteer("exception")
    cross_ref = ex.get("cross_reference_cues", {}).get("instrument", "")
    for phrase in exc_gaz["lead_phrases"]:
        # A probe generic enough for every route a gazetteer exception lead may
        # be covered by: exception_lead (any tail), condition_lead ('subject to'
        # doubles as a sentence-initial condition lead — needs the trailing
        # comma that production requires), or cross_reference_cues.instrument
        # ('in accordance with' is published there, not as an exception cue).
        covered = (re.search(slot["exception_lead"], f"{phrase} consent", re.I)
                   or re.search(slot["condition_lead"], f"{phrase} X,", re.I)
                   or (cross_ref and re.search(cross_ref, f"{phrase} Article 5", re.I)))
        if not covered:
            fails.append(f"gazetteer exception lead {phrase!r} not covered by any "
                         "extraction.json slot cue (exception_lead/condition_lead/"
                         "cross_reference_cues.instrument)")
    return fails


# Gate G's documented, out-of-scope-by-design exemption: German alternatives
# the English-only (Phase 1 scope) gazetteer-driven parser never recognises.
# "abweichend" (not "abweichend von") is a pre-existing, unfixed regex issue,
# exempted here rather than silently widened; see extraction.json's and
# exception.json's own describes fields.
_NON_ENGLISH_ALTERNATIVES: dict[str, set[str]] = {
    "condition_lead": {"wenn", "falls", "sofern", "soweit"},
    "condition_lead_with_phrase": set(),
    "exception_lead": {"es sei denn", "abweichend"},
}


def _pattern_alternatives(pattern: str) -> list[str]:
    """The literal `a|b|c` alternatives inside a pattern's first `(?:...)`
    non-capturing group, unescaped of the one metacharacter these specific
    cue patterns use internally (`\\s+`, published as a literal space here).
    These three patterns (`condition_lead`, `condition_lead_with_phrase`,
    `exception_lead`) are, by construction, pure literal alternations with no
    nested group — the one shape this lightweight extraction is safe for."""
    m = re.search(r"\(\?:([^)]+)\)", pattern)
    if not m:
        return []
    return [alt.replace("\\s+", " ") for alt in m.group(1).split("|")]


def check_gazetteer_sync_reverse(ex: dict | None = None) -> list[str]:
    """Gate G: every ENGLISH alternative this file publishes for
    condition_lead/condition_lead_with_phrase/exception_lead is also a
    gazetteer `lead_phrases` entry (see the module docstring, Gate G)."""
    ex = EX if ex is None else ex
    fails: list[str] = []
    slot = ex["slot_cues"]
    groups = (
        ("condition_lead", "condition", lambda e: not (isinstance(e, dict) and e.get("keep_lead"))),
        ("condition_lead_with_phrase", "condition", lambda e: isinstance(e, dict) and e.get("keep_lead")),
        ("exception_lead", "exception", lambda e: True),
    )
    for key, gaz_name, _select in groups:
        if key not in slot:
            continue
        gaz = _load_gazetteer(gaz_name)
        gaz_phrases = {e["phrase"] if isinstance(e, dict) else e for e in gaz["lead_phrases"]}
        alts = set(_pattern_alternatives(slot[key])) - _NON_ENGLISH_ALTERNATIVES.get(key, set())
        extra = alts - gaz_phrases
        if extra:
            fails.append(f"extraction.json slot_cues.{key} has English alternative(s) "
                         f"{sorted(extra)} not in gazetteer/{gaz_name}.json's lead_phrases")
    return fails


_CHECKS = (
    ("incident cues equal the language", check_incident_cues),
    ("operator mapping equals the language; no operator carries a 5D dimension", check_operator_mapping),
    ("incident rules reproduce classify_incident", check_incident_rules),
    ("every published pattern compiles", check_regex_validity),
    ("validity rules stay on the published incidents", check_validity_rules),
    ("gazetteer cues are covered by the published extraction cues", check_gazetteer_sync),
    ("extraction cues do not outrun the gazetteer (English alternatives)", check_gazetteer_sync_reverse),
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
