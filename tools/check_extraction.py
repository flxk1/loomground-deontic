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
  H. Modal-cue precedence — a multi-word gazetteer phrase mapped to one modal
     (e.g. permission's "shall be entitled to") can also contain, as a
     literal substring, a shorter phrase/lexeme published under a DIFFERENT
     modal's own extraction.json pattern (obligation's bare "shall" sits
     inside "shall be entitled to" too). `describes` states the tie-break a
     plain consumer applies when more than one `modal_cues` pattern matches
     the same text: the pattern naming the LONGER literal phrase wins (the
     same longest-match-first rule `modal_lexemes.json`'s own gazetteer-driven
     parser already applies at a single token position). This gate proves
     the rule actually resolves every such overlap rather than merely stating
     it: for every multi-word gazetteer phrase, the LONGEST span of that
     phrase that any OTHER modal's pattern can fully match must be STRICTLY
     SHORTER (fewer words) than the phrase itself, so "longer wins" always
     picks the gazetteer's own modal, never a tie a plain consumer could not
     break. "Longest span a pattern can match" is computed directly
     (`_longest_full_match_words`: every contiguous word span of the phrase,
     longest first, tested with `re.fullmatch`) rather than trusting a single
     `re.search` — Python's `re` tries an alternation's branches in LISTED
     ORDER and returns the first one that matches, which is not necessarily
     the longest; a mutated pattern that lists a short alternative (plain
     "shall") before a long one that also matches the same text ("shall be
     entitled to") would make a bare `re.search`-based check miss the true
     overlap entirely. `tests/test_check_extraction.py` proves this with such
     a mutation: Gate H using plain `re.search` passes it (a false green);
     Gate H as implemented here fails it.
  I. complement_verb_cue sync — the six `requires_verb_complement` phrases
     (`modal_lexemes.json`) read as a permission ONLY when the word right
     after the match is one of a closed, positive list of base-form verbs,
     AND the word after THAT is not a noun-marker for that verb
     (`gazetteer/complement_verbs.json`'s `verbs`/`noun_markers`/
     `verb_specific_noun_markers`; `deontic.prose_grammar`'s own gate); one
     of the six ("shall have the power to") additionally has no fallback on
     a failed check (`abstain_if_no_verb_complement` in the gazetteer,
     `no_fallback_modal_cue` here). This gate holds every one of those
     fields equal to the two gazetteer sources, so a plain, code-free
     consumer's reading of "shall be entitled to compensation" (no verb
     complement), "shall be entitled to transfer OF the data" (a noun-marker
     overlap), or "shall have the power to audit" (the no-fallback phrase,
     where a plain consumer must NOT fall back to reading it as an
     obligation) can never silently drift from what the parser itself does.

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


def check_complement_verb_sync(ex: dict | None = None) -> list[str]:
    """Gate I: complement_verb_cue (the ADDITIVE condition over the word
    following a match on one of the six requires_verb_complement modal_cues
    phrases, and the word after THAT) equals both
    artifacts/gazetteer/complement_verbs.json (the parser's own list and
    noun-marker tables) and artifacts/gazetteer/modal_lexemes.json's own set
    of requires_verb_complement-flagged phrases (and the single
    abstain_if_no_verb_complement-flagged phrase), so a plain consumer's
    permission reading of these six phrases can never silently drift from
    deontic.prose_grammar's own gate — see the module docstring, Gate I."""
    ex = EX if ex is None else ex
    fails: list[str] = []
    cue = ex.get("complement_verb_cue", {})
    gaz = _load_gazetteer("complement_verbs")
    if set(cue.get("verbs", [])) != set(gaz["verbs"]):
        fails.append("complement_verb_cue.verbs != gazetteer/complement_verbs.json's verbs")
    if set(cue.get("noun_markers", [])) != set(gaz["noun_markers"]):
        fails.append("complement_verb_cue.noun_markers != gazetteer/"
                      "complement_verbs.json's noun_markers")
    if cue.get("verb_specific_noun_markers", {}) != gaz["verb_specific_noun_markers"]:
        fails.append("complement_verb_cue.verb_specific_noun_markers != gazetteer/"
                      "complement_verbs.json's verb_specific_noun_markers")
    modal_gaz = _load_gazetteer("modal_lexemes")
    gaz_flagged = {e["phrase"] for e in modal_gaz["phrases"] if e.get("requires_verb_complement")}
    if set(cue.get("applies_to_modal_cues", [])) != gaz_flagged:
        fails.append("complement_verb_cue.applies_to_modal_cues != gazetteer/"
                      "modal_lexemes.json's requires_verb_complement-flagged phrases")
    gaz_no_fallback = {e["phrase"] for e in modal_gaz["phrases"]
                       if e.get("abstain_if_no_verb_complement")}
    cue_no_fallback = {cue["no_fallback_modal_cue"]} if cue.get("no_fallback_modal_cue") else set()
    if cue_no_fallback != gaz_no_fallback:
        fails.append("complement_verb_cue.no_fallback_modal_cue != gazetteer/"
                      "modal_lexemes.json's abstain_if_no_verb_complement-flagged phrase(s)")
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


_BARE_LEXEME_TO_MODAL = {"shall": "obligation", "must": "obligation", "may": "permission"}


def _longest_full_match_words(pattern: str, phrase: str) -> int:
    """The word count of the LONGEST contiguous word span of ``phrase`` that
    ``pattern`` matches in full (``re.fullmatch``), tried longest span
    first; ``0`` if no span matches at all. Deliberately not a single
    ``re.search``: Python's ``re`` tries an alternation's branches in LISTED
    ORDER and stops at the first one that matches at a position, which is
    not necessarily the longest available match — a pattern whose
    alternatives are `(?:shall|shall be entitled to|...)` would have
    `re.search` return "shall" (the first-listed, shorter alternative) even
    though "shall be entitled to" (a later, longer alternative) also
    matches the same text. Trying every candidate span directly, longest
    first, is immune to alternative ORDER inside the pattern."""
    words = phrase.split()
    for span_len in range(len(words), 0, -1):
        for start in range(0, len(words) - span_len + 1):
            span = " ".join(words[start:start + span_len])
            if re.fullmatch(pattern, span, re.I):
                return span_len
    return 0


def check_modal_cue_precedence(ex: dict | None = None) -> list[str]:
    """Gate H: where a multi-word gazetteer phrase overlaps a DIFFERENT
    modal's own extraction.json pattern, "the longer literal phrase wins"
    (this file's published tie-break, mirroring modal_lexemes.json's own
    longest-match-first dispatch) must actually resolve the overlap — see
    the module docstring, Gate H."""
    ex = EX if ex is None else ex
    fails: list[str] = []
    modal_patterns = {c["modal"]: c["pattern"] for c in ex["modal_cues"]}
    modal_gaz = _load_gazetteer("modal_lexemes")
    for entry in modal_gaz["phrases"]:
        phrase = entry["phrase"]
        words = phrase.split()
        if len(words) < 2:
            continue  # a bare lexeme is the baseline other cues overlap WITH
        own_modal = "prohibition" if entry.get("operator") == "F" else \
            _BARE_LEXEME_TO_MODAL[entry["lexeme"]]
        for other_modal, pattern in modal_patterns.items():
            if other_modal == own_modal:
                continue
            overlap_len = _longest_full_match_words(pattern, phrase)
            if overlap_len >= len(words):
                fails.append(
                    f"gazetteer phrase {phrase!r} ({own_modal}) is matched by "
                    f"{other_modal}'s modal_cues pattern over {overlap_len} word(s), "
                    f"equal to or longer than the phrase's own {len(words)} word(s): "
                    "the 'longer phrase wins' tie-break cannot disambiguate this pair")
    return fails


_CHECKS = (
    ("incident cues equal the language", check_incident_cues),
    ("operator mapping equals the language; no operator carries a 5D dimension", check_operator_mapping),
    ("incident rules reproduce classify_incident", check_incident_rules),
    ("every published pattern compiles", check_regex_validity),
    ("validity rules stay on the published incidents", check_validity_rules),
    ("gazetteer cues are covered by the published extraction cues", check_gazetteer_sync),
    ("extraction cues do not outrun the gazetteer (English alternatives)", check_gazetteer_sync_reverse),
    ("the longer-phrase tie-break resolves every modal_cues overlap", check_modal_cue_precedence),
    ("complement_verb_cue stays in sync with the gazetteer", check_complement_verb_sync),
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
