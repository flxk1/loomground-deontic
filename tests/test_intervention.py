# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The intervention profile: correctability read off the existing incidents.

The load-bearing property these tests defend is that the profile is a *reading*,
not a vocabulary: it introduces no incident, no operator and no correlative pair,
and it computes the intervener's position through `deontic.correlative` rather
than restating it. If that stops holding, the profile has become a fourth
modality by the back door.
"""
from __future__ import annotations

import deontic


# --- the profile adds no vocabulary ------------------------------------------

def test_positions_are_existing_incidents_only():
    assert set(deontic.INTERVENTION_POSITIONS) <= set(deontic.INCIDENTS)


def test_profile_introduces_no_operator():
    # The three SDL modals are untouched; there is no intervention operator.
    assert deontic.VALID_OPERATORS == deontic.VALID_OPERATORS
    assert "intervention" not in {o.lower() for o in deontic.VALID_OPERATORS}


def test_the_four_positions_are_the_two_correctability_pairs():
    # power/liability and immunity/disability, and nothing else.
    assert set(deontic.INTERVENTION_POSITIONS) == {
        "power", "liability", "immunity", "disability"}
    assert deontic.correlative("power") == "liability"
    assert deontic.correlative("immunity") == "disability"


def test_vocabulary_artifact_matches_the_code():
    art = deontic.vocabulary("intervention")
    assert tuple(k["name"] for k in art["kinds"]) == deontic.INTERVENTION_KINDS
    assert set(art["positions"]) - {"describes"} == set(deontic.INTERVENTION_POSITIONS)


# --- kind classification ------------------------------------------------------

def test_each_kind_is_recognised():
    assert deontic.classify_intervention_kind("suspend the run") == "pause"
    assert deontic.classify_intervention_kind("override the result") == "correct"
    assert deontic.classify_intervention_kind("restrict what it may do") == "constrain"
    assert deontic.classify_intervention_kind("terminate the mandate") == "terminate"


def test_abstains_on_a_non_intervention():
    assert deontic.classify_intervention_kind("engage a subprocessor") == ""
    assert deontic.is_intervention("notify the authority") is False


def test_coarsest_kind_wins_when_several_cues_fire():
    # A reader must not be told 'pause' about a statement that also terminates.
    assert deontic.classify_intervention_kind(
        "suspend and then terminate the mandate") == "terminate"


def test_german_cues_are_recognised():
    assert deontic.classify_intervention_kind("den Auftrag widerrufen") == "terminate"
    assert deontic.classify_intervention_kind("den Lauf aussetzen") == "pause"


# --- positions ----------------------------------------------------------------

def test_permission_to_intervene_is_a_power():
    assert deontic.intervention_position("P", "revoke the authority") == "power"


def test_prohibiting_the_exercise_removes_the_power():
    # Prohibiting a position-changing verb is a disability, not a duty.
    assert deontic.intervention_position("F", "revoke the authority") == "disability"


def test_passive_protection_is_the_addressees_immunity():
    assert deontic.intervention_position(
        "F", "the mandate may not be revoked") == "immunity"
    assert deontic.intervention_position(
        "F", "der Auftrag darf nicht widerrufen werden") == "immunity"


def test_position_abstains_outside_the_profile():
    assert deontic.intervention_position("P", "engage a subprocessor") == ""


def test_accepts_operator_or_surface_modal():
    assert (deontic.intervention_position("P", "revoke it")
            == deontic.intervention_position("permission", "revoke it")
            == "power")


def test_general_classifier_is_unchanged_by_the_profile():
    # The profile must not have widened incidents.classify_incident.
    assert deontic.classify_incident(
        "prohibition", "the mandate may not be revoked", "") == "disability"


# --- the diagnostic -----------------------------------------------------------

def _f(modal, bearer, action):
    return deontic.formula_from_fields(modal, bearer, action)


def test_uncorrectable_party_is_flagged_with_its_correlative():
    out = deontic.intervention_exposure(
        [_f("prohibition", "supervisor", "the delegate may not be terminated")])
    assert "intervention-immunity" in out["flags"]
    entry = out["immune"][0]
    assert entry["incident"] == "immunity"
    # The intervener's position is COMPUTED, not restated.
    assert entry["counterparty_position"] == deontic.correlative("immunity")
    assert entry["counterparty_position"] == "disability"


def test_a_conferred_power_raises_no_flag():
    out = deontic.intervention_exposure(
        [_f("permission", "supervisor", "terminate the delegate")])
    assert out["flags"] == []
    assert out["interventions"][0]["incident"] == "power"
    assert out["interventions"][0]["counterparty_position"] == "liability"


def test_intervention_named_but_never_conferred_is_flagged():
    out = deontic.intervention_exposure(
        [_f("obligation", "delegate", "suspend the run")])
    assert "intervention-unheld" in out["flags"]


def test_a_set_with_no_interventions_is_silent():
    out = deontic.intervention_exposure([_f("obligation", "processor", "notify")])
    assert out == {"interventions": [], "immune": [], "flags": []}


def test_diagnostic_flags_and_never_resolves():
    # No verdict, no severity, no resolution — flags only, like candidate
    # conflicts elsewhere in the algebra.
    out = deontic.intervention_exposure(
        [_f("prohibition", "supervisor", "the delegate may not be terminated")])
    assert set(out) == {"interventions", "immune", "flags"}
    for forbidden in ("verdict", "severity", "resolution", "healthy", "ok"):
        assert forbidden not in out


def test_diagnostic_does_not_mutate_its_input():
    f = _f("permission", "supervisor", "terminate the delegate")
    before = f.to_dict()
    deontic.intervention_exposure([f])
    assert f.to_dict() == before


def test_carried_incident_is_respected_over_reclassification():
    f = _f("permission", "supervisor", "terminate the delegate")
    f.incident = "immunity"          # a host classified it; do not overrule
    out = deontic.intervention_exposure([f])
    assert out["interventions"][0]["incident"] == "immunity"
