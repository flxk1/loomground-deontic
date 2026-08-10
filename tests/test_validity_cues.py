# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The published validity vocabulary and the clause-level deadline surface.

Validity norms are CONSTITUTIVE: "ist unwirksam" / "is void" directs no
conduct — it denies legal effect. The language therefore publishes them as
cues with an effect (void / preserved / substitution) mapped by
validity_rules onto the Hohfeldian incident layer it already owns (void =
the drafter's disability; the counterparty's immunity follows via the
published correlatives). NOT a fourth operator: O/P/F stay the operator set.

The clause-level deadline entries widen the published deadline SURFACE (the
full match a consumer records or removes) to the whole clause — connective,
feasibility qualifier, cue, value, reference-point tail — while each named
group still holds only the value.

    python -m pytest tests/test_validity_cues.py
"""
from __future__ import annotations

import re

import deontic

_EX = deontic.load_json("extraction.json")
_VALIDITY = [(c["effect"], re.compile(c["pattern"], re.I))
             for c in _EX["validity_cues"]]
_DEADLINE = [re.compile(p, re.I) for p in _EX["deadline_cues"].values()]


def _effects(text: str) -> set[str]:
    return {effect for effect, pattern in _VALIDITY if pattern.search(text)}


def _first_deadline_match(text: str):
    for pattern in _DEADLINE:
        m = pattern.search(text)
        if m:
            return m
    return None


# -- validity cues over the real statute shapes ------------------------------

def test_void_matches_de_blacklist_and_general_clause():
    # §309 word order (predicate before subject) and §307 plural + condition.
    assert _effects("In allgemeinen Geschäftsbedingungen ist unwirksam eine "
                    "Bestimmung, durch die der Verwender die Beweislast "
                    "ändert.") == {"void"}
    assert _effects("Bestimmungen in allgemeinen Geschäftsbedingungen sind "
                    "unwirksam, wenn sie den Vertragspartner unangemessen "
                    "benachteiligen.") == {"void"}


def test_void_matches_en_forms():
    assert _effects("Such a term is void.") == {"void"}
    assert _effects("The waiver shall be null and void.") == {"void"}
    assert _effects("Any such clause is unenforceable.") == {"void"}


def test_preserved_and_substitution_match_para306():
    assert _effects("Bei Unwirksamkeit bleibt der Vertrag im Übrigen "
                    "wirksam.") == {"preserved"}
    assert _effects("An die Stelle der unwirksamen Klausel treten die "
                    "gesetzlichen Vorschriften.") == {"substitution"}
    assert _effects("The remainder of the contract remains in force and the "
                    "void term is replaced by the statutory provisions."
                    ) == {"preserved", "substitution"}


def test_validity_cues_fail_closed():
    # Negated validity and plain conduct norms match nothing.
    assert _effects("The clause is not void.") == set()
    assert _effects("Die Klausel ist nicht unwirksam.") == set()
    assert _effects("The controller shall notify the authority.") == set()


def test_void_rule_lands_on_the_hohfeld_square():
    # The published rule maps void onto a REAL incident, and the language's
    # own correlative gives the counterparty's position — the doctrinal seam.
    rules = {r["effect"]: r["incident"] for r in _EX["validity_rules"]}
    assert rules["void"] == "disability"
    assert rules["void"] in deontic.INCIDENTS
    assert deontic.correlative_incident(rules["void"]) == "immunity"
    # Consequence shapes abstain rather than fake an addressee incident.
    assert rules["preserved"] == ""
    assert rules["substitution"] == ""


# -- clause-level deadline surface -------------------------------------------

def test_deadline_surface_covers_the_gdpr_clause():
    m = _first_deadline_match(
        "notify the supervisory authority without undue delay and, where "
        "feasible, not later than 72 hours after having become aware of it,")
    assert m.group(0) == ("and, where feasible, not later than 72 hours "
                          "after having become aware of it")
    assert m.group("deadline") == "72 hours"


def test_deadline_surface_covers_the_german_clause():
    m = _first_deadline_match(
        "die Aufsichtsbehörde innerhalb von 72 Stunden nach Bekanntwerden "
        "benachrichtigen")
    assert m.group(0) == "innerhalb von 72 Stunden nach Bekanntwerden"
    assert m.group("deadline") == "72 Stunden"


def test_deadline_value_extraction_is_unchanged():
    # The named group still holds only the value, clause entries included.
    m = _first_deadline_match("The provider shall notify the authority "
                              "within 30 days.")
    assert m.group("deadline") == "30 days"
