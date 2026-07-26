# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Property tests for the deontic algebra laws and the composition contract.

The carriers are finite — three modal operators, eight Hohfeld incidents — so the
laws are checked exhaustively over them, with a small sample of propositions for
the duality strings. These are the checkable identities the algebra promises:
the square of opposition, F≡O¬ / P≡¬O¬ duality, jural correlativity and
opposition as commuting involutions, and the composition contract's totality.

    python -m pytest tests/test_algebra_laws.py
"""
from __future__ import annotations

import itertools

import deontic
from deontic import operators, incidents, algebra, contract

OPS = operators.VALID_OPERATORS
INCS = incidents.INCIDENTS
PROPS = ["disclose the data", "assign the contract", "act", "¬-looking text", ""]


# --- the modal square of opposition -----------------------------------------

def test_clash_is_symmetric_and_irreflexive():
    for a, b in itertools.product(OPS, repeat=2):
        assert operators.clashes(a, b) == operators.clashes(b, a)
    for a in OPS:
        assert not operators.clashes(a, a)


def test_contraries_clash_law_holds_for_every_operator_pair():
    for a, b in itertools.product(OPS, repeat=2):
        assert algebra.law_square_contraries(a, b)


def test_obligation_and_prohibition_are_the_contraries():
    for a, b in itertools.product(OPS, repeat=2):
        expected = {a, b} == {operators.OP_OBLIGATION, operators.OP_PROHIBITION}
        assert algebra.contrary(a, b) is expected


def test_contradictory_relations_are_the_square_diagonals():
    assert algebra.contradictory(operators.OP_OBLIGATION) == (operators.OP_PERMISSION, True)
    assert algebra.contradictory(operators.OP_PROHIBITION) == (operators.OP_PERMISSION, False)
    assert algebra.contradictory(operators.OP_PERMISSION) == (operators.OP_OBLIGATION, True)
    # Anything outside the three modalities (e.g. a legacy "R") has none.
    assert algebra.contradictory("R") == ("", False)


# --- duality ----------------------------------------------------------------

def test_duality_strings_over_all_operators_and_propositions():
    for a in PROPS:
        assert operators.dual_of("F", a) == f"O(¬ {a})"      # F(a) ≡ O(¬a)
        assert operators.dual_of("P", a) == f"¬O(¬ {a})"     # P(a) ≡ ¬O(¬a)
        assert operators.dual_of("O", a) == f"¬P(¬ {a})"     # O(a) ≡ ¬P(¬a)
        assert operators.dual_of("R", a) == ""               # not a modality → no dual
        assert algebra.law_dual_of_prohibition(a)


def test_operator_set_is_the_three_modalities():
    # "Right" is not a fourth operator: O/P/F only, with O the primitive.
    assert operators.VALID_OPERATORS == ("O", "P", "F")
    assert "R" not in operators.VALID_OPERATORS
    # A surface "right" reduces to a P (liberty) for the holder.
    assert deontic.formula_from_fields("right", "data subject", "access data").operator == "P"
    # The grammar rejects R as an operator (documented by the conformance vector).
    import pytest
    with pytest.raises(deontic.DeonticSyntaxError):
        deontic.parse("R(data subject : access data)")


def test_formula_dual_matches_operator_dual():
    for op in OPS:
        f = deontic.DeonticFormula(operator=op, bearer="x", action="do y")
        assert f.dual() == operators.dual_of(op, "do y")


# --- Hohfeld incidents: correlativity and opposition ------------------------

def test_incidents_closed_under_correlative_and_opposite():
    for x in INCS:
        assert incidents.correlative(x) in INCS
        assert incidents.opposite(x) in INCS


def test_correlative_and_opposite_are_involutions():
    for x in INCS:
        assert algebra.law_correlativity_involution(x)
        assert algebra.law_opposite_involution(x)


def test_correlative_and_opposite_are_fixed_point_free():
    for x in INCS:
        assert incidents.correlative(x) != x
        assert incidents.opposite(x) != x


def test_hohfeld_square_commutes():
    # correlative ∘ opposite == opposite ∘ correlative for every incident
    # (the diagonal of the Hohfeld square is well-defined).
    for x in INCS:
        assert incidents.correlative(incidents.opposite(x)) == \
               incidents.opposite(incidents.correlative(x))


def test_correlative_and_opposite_flip_advantage_side():
    for x in INCS:
        assert incidents.is_advantage(incidents.correlative(x)) != incidents.is_advantage(x)
        assert incidents.is_advantage(incidents.opposite(x)) != incidents.is_advantage(x)


def test_each_pair_has_exactly_one_advantage_side():
    seen = set()
    for x in INCS:
        pair = frozenset((x, incidents.correlative(x)))
        if pair in seen:
            continue
        seen.add(pair)
        adv = [i for i in pair if incidents.is_advantage(i)]
        assert len(adv) == 1, pair
    assert len(seen) == 4  # four correlative pairs


# --- bilateral liberty (the optional) ---------------------------------------

def test_bilateral_liberty_reduces_to_two_permissions():
    for prop in PROPS:
        if not prop:
            continue
        assert algebra.law_optional_reduces_to_two_permissions(prop)
    lib = deontic.optional("data subject", "receive marketing")
    do, refrain = lib.permissions()
    assert (do.operator, do.negated) == ("P", False)
    assert (refrain.operator, refrain.negated) == ("P", True)
    assert lib.render() == "P(data subject : receive marketing) ∧ P(data subject : ¬ receive marketing)"


def test_bilateral_liberty_excludes_obligation_and_prohibition():
    lib = deontic.optional("x", "act")
    excl = lib.excludes()
    assert excl == ("O(x : act)", "F(x : act)")


def test_is_optional_detects_both_permissions_present():
    do = deontic.DeonticFormula(operator="P", bearer="x", action="act", negated=False)
    refrain = deontic.DeonticFormula(operator="P", bearer="x", action="act", negated=True)
    assert deontic.is_optional([do, refrain], "x", "act")
    # a single unilateral privilege is not a bilateral liberty
    assert not deontic.is_optional([do], "x", "act")


# --- systemic health (utopia/dystopia axis) ---------------------------------

def test_system_health_flags_normative_collapse():
    a = deontic.formula_from_fields("obligation", "x", "act")
    b = deontic.formula_from_fields("prohibition", "x", "act")
    h = deontic.system_health([a, b])
    assert h["conflict_free"] is False
    assert "normative-collapse" in h["pathologies"]
    assert h["healthy"] is False


def test_system_health_flags_liberty_absent():
    # all duty / prohibition, no permission or privilege anywhere
    a = deontic.formula_from_fields("obligation", "x", "file report")
    b = deontic.formula_from_fields("prohibition", "y", "disclose")
    h = deontic.system_health([a, b])
    assert "liberty-absent" in h["pathologies"]


def test_system_health_flags_unchecked_power():
    power = deontic.formula_from_fields("permission", "x", "terminate the contract",
                                        incident="power")
    h = deontic.system_health([power])
    assert h["powers_present"] is True
    assert h["immunities_present"] is False
    assert "immunity-absent" in h["pathologies"]


def test_system_health_healthy_set_has_no_pathologies():
    do = deontic.DeonticFormula(operator="P", bearer="x", action="act", negated=False)
    refrain = deontic.DeonticFormula(operator="P", bearer="x", action="act", negated=True)
    immunity = deontic.formula_from_fields("prohibition", "y", "amend without consent",
                                           incident="immunity")
    h = deontic.system_health([do, refrain, immunity])
    assert h["conflict_free"] is True
    assert h["pathologies"] == []
    assert h["healthy"] is True
    assert {"bearer": "x", "action": "act"} in h["liberties"]


# --- the composition contract -----------------------------------------------

def test_dimension_affinity_is_total_and_in_solver_vocabulary():
    for op in OPS:
        assert contract.dimension_affinity(op) in contract.SOLVER_DIMENSIONS
    # unknown operators fall to the relational floor, still a valid string
    assert contract.dimension_affinity("Z") == "relational"


def test_solver_dimension_strings_are_the_canonical_five():
    assert set(contract.SOLVER_DIMENSIONS) == {
        "structural", "causal", "intentional", "temporal", "relational",
    }


def test_packet_is_lossless_over_statement_and_names_correlative():
    f = deontic.formula_from_fields(
        "obligation", "processor", "notify the controller",
        incident="duty", counterparty="controller",
        raw_sentence="The processor shall notify the controller.",
    )
    p = deontic.packet(f)
    assert p.statement == deontic.project(f)
    assert p.dimension == "causal"
    assert p.incident == "duty"
    assert p.correlative == "claim"        # the counterparty's jural correlative
    assert p.dual == f.dual()


def test_conflict_candidates_carry_the_collision_predicate():
    a = deontic.formula_from_fields("obligation", "processor", "notify")
    b = deontic.formula_from_fields("prohibition", "processor", "notify")
    cands = deontic.conflict_candidates([a, b])
    assert len(cands) == 1
    assert cands[0]["predicate"] == "may-conflict-with"
    assert cands[0]["resolution"] == "candidate-escalate"


def test_incident_vocabulary_is_the_closed_eight():
    assert deontic.incident_vocabulary() == INCS
    assert len(INCS) == 8


def test_contract_surface_is_self_consistent():
    s = deontic.contract_surface()
    assert s["operators"] == list(OPS)
    assert s["incidents"] == list(INCS)
    assert set(s["operator_dimension_affinity"].values()) <= set(contract.SOLVER_DIMENSIONS)
    assert s["conflict_predicate"] == "may-conflict-with"


# --- compose merges without resolving ---------------------------------------

def test_compose_preserves_foreign_content_untouched():
    a = deontic.formula_from_fields("obligation", "x", "act")
    foreign = {"algebra": "governance", "opaque": [1, 2, 3]}
    comp = deontic.compose(a, foreign)
    assert comp.formulae == [a]
    assert comp.foreign == [foreign]
    assert comp.conflicts == []


def test_compose_flags_but_never_resolves_conflicts():
    a = deontic.formula_from_fields("permission", "x", "act")
    b = deontic.formula_from_fields("prohibition", "x", "act")
    comp = deontic.compose([a, b])
    assert len(comp.conflicts) == 1
    assert comp.conflicts[0]["resolution"] == "candidate-escalate"
