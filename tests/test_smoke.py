# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Smoke coverage: the language modules import, parse/render round-trips, the
lifted classifiers behave, and the algebra laws hold on their carrier. The
exhaustive property suite for the laws lands with the composition contract in
the next step; these are the sanity gates.

    python -m pytest tests/test_smoke.py
"""
from __future__ import annotations

import deontic
from deontic import incidents, algebra, operators


def test_package_imports_no_solver_no_extractor():
    # Foundational: the package pulls in nothing from solver or a rule extractor.
    import sys
    deontic.language_card()  # touch the artifact loader
    loaded = set(sys.modules)
    assert not any(m.startswith("loomground_solver") for m in loaded)
    assert not any("rule_extractor" in m for m in loaded)


def test_render_parse_round_trip():
    f = deontic.DeonticFormula(
        operator="O", bearer="controller", action="implement TOMs",
        condition="processing is carried out", exception="Art.11",
    )
    again = deontic.parse(f.render())
    assert deontic.project(again) == deontic.project(f)


def test_formula_from_fields_maps_modal():
    f = deontic.formula_from_fields("prohibition", "processor", "engage a subprocessor")
    assert f.operator == operators.OP_PROHIBITION
    assert f.dual() == "O(¬ engage a subprocessor)"


def test_uncatalogued_modal_fails_closed():
    # An unrecognised, non-negated modal must NOT silently become an obligation:
    # reading an unknown modal as a duty can invert the norm's force. It now fails
    # closed. (A negated modal is recognised as F — see test_negated_modal.py.)
    import pytest
    with pytest.raises(ValueError, match="unrecognised deontic modal"):
        deontic.formula_from_fields("recommendation", "x", "do y", confidence=0.5)


def test_is_grounded_requires_span_and_concrete_slots():
    grounded = deontic.formula_from_fields("obligation", "controller", "act",
                                           raw_sentence="The controller shall act.")
    assert deontic.is_grounded(grounded)
    ungrounded = deontic.formula_from_fields("obligation", "", "")
    assert not deontic.is_grounded(ungrounded)


def test_detect_conflicts_flags_obligation_vs_prohibition():
    a = deontic.formula_from_fields("obligation", "processor", "notify")
    b = deontic.formula_from_fields("prohibition", "processor", "notify")
    conflicts = deontic.detect_conflicts([a, b])
    assert len(conflicts) == 1
    assert conflicts[0]["kind"] == "deontic-conflict"


def test_detect_conflicts_respects_proposition_polarity():
    obligation = deontic.DeonticFormula("O", "processor", "notify")
    refrain = deontic.DeonticFormula("O", "processor", "notify", negated=True)
    prohibition = deontic.DeonticFormula("F", "processor", "notify")
    permission_to_refrain = deontic.DeonticFormula(
        "P", "processor", "notify", negated=True)

    assert len(deontic.detect_conflicts([obligation, refrain])) == 1
    assert deontic.detect_conflicts([refrain, prohibition]) == []
    assert len(deontic.detect_conflicts([obligation, permission_to_refrain])) == 1


def test_formula_rejects_unknown_operator():
    import pytest
    with pytest.raises(ValueError, match="unknown deontic operator"):
        deontic.DeonticFormula("Z", "x", "act")


def test_negated_formula_dual_uses_signed_proposition():
    f = deontic.DeonticFormula("O", "x", "act", negated=True)
    assert f.dual() == "¬P(act)"


def test_claim_right_is_modeled_as_the_correlative_duty():
    # "the data subject has a right that the controller erase the data" is the
    # controller's duty, owed to the data subject — not a liberty for the subject.
    f = deontic.claim_right("data subject", "erase the data", "controller",
                            raw_sentence="The data subject shall have the right to erasure.")
    assert f.operator == "O"
    assert f.bearer == "controller"
    assert f.incident == "duty"
    assert f.counterparty == "data subject"
    # its Hohfeld correlative is the holder's claim
    assert incidents.correlative(f.incident) == "claim"
    # a liberty-right stays a permission (privilege), by contrast
    lib = deontic.formula_from_fields("right", "data subject", "access their data")
    assert lib.operator == "P"


def test_resolutive_cue_allows_intervening_words():
    assert incidents.classify_condition_kind("until the licence is revoked") == "resolutive"
    assert incidents.classify_condition_kind("until terminated") == "resolutive"
    assert incidents.classify_condition_kind("bis auf Widerruf") == "resolutive"
    # suspensive still keys on the lead cue; a bare temporal terminus abstains
    assert incidents.classify_condition_kind("if the breach occurs") == "suspensive"
    assert incidents.classify_condition_kind("until majority") == ""


def test_hohfeld_classification_and_pairs():
    # Obligation → duty on the addressee; its correlative is a claim.
    assert incidents.classify_incident("obligation", "notify", "shall notify") == "duty"
    assert incidents.correlative("duty") == "claim"
    # Prohibition of a power verb removes the power → disability.
    assert incidents.classify_incident("prohibition", "assign the contract",
                                       "may not assign") == "disability"
    # Permission with a power verb is a power, else a privilege.
    assert incidents.classify_incident("permission", "terminate", "may terminate") == "power"
    assert incidents.classify_incident("permission", "read", "may read") == "privilege"


def test_incident_relations_are_involutions_over_all_incidents():
    for inc in incidents.INCIDENTS:
        assert algebra.law_correlativity_involution(inc)
        assert algebra.law_opposite_involution(inc)


def test_square_contraries_law_over_all_operator_pairs():
    ops = operators.VALID_OPERATORS
    for a in ops:
        for b in ops:
            assert algebra.law_square_contraries(a, b)


def test_compose_merges_and_flags():
    a = deontic.formula_from_fields("obligation", "processor", "notify")
    b = deontic.formula_from_fields("prohibition", "processor", "notify")
    comp = deontic.compose([a, b], {"foreign": "governance content"})
    assert len(comp.formulae) == 2
    assert len(comp.conflicts) == 1
    assert comp.foreign == [{"foreign": "governance content"}]


def test_compose_preserves_generator_and_empty_iterable_inputs():
    formulae = (
        deontic.DeonticFormula(op, "x", "act")
        for op in ("O", "F")
    )
    foreign = {}
    comp = deontic.compose(formulae, [], foreign)
    assert len(comp.formulae) == 2
    assert len(comp.conflicts) == 1
    assert comp.foreign == [foreign]


def test_claim_does_not_count_as_liberty():
    claim = deontic.formula_from_fields(
        "obligation", "x", "act", incident="claim")
    health = deontic.system_health([claim])
    assert health["privileges_present"] is False
    assert "liberty-absent" in health["pathologies"]
