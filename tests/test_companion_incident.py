# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The bundled skill engine must classify a negated modal's incident as the
prohibition it is, not abstain. formula_from_fields resolves "must not" to F but
classify_incident keys on the canonical modal, so the incident has to be read
from the resolved operator; feeding the raw surface phrase left it unclassified.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "deontic"))
import deontic_engine as eng  # noqa: E402


def test_negated_conduct_prohibition_is_a_duty():
    f = eng.formula_from_fields("must not", "processor", "disclose the data")
    assert f["operator"] == "F"
    assert f["incident"] == "duty"


def test_negated_power_prohibition_is_a_disability():
    f = eng.formula_from_fields("may not", "tenant", "assign the lease")
    assert f["operator"] == "F"
    assert f["incident"] == "disability"


def test_negated_no_variation_is_an_immunity():
    f = eng.formula_from_fields(
        "may not", "party", "act", raw_sentence="the agreement shall not be varied")
    assert f["operator"] == "F"
    assert f["incident"] == "immunity"


def test_canonical_prohibition_incident_unchanged():
    f = eng.formula_from_fields("prohibition", "processor", "disclose the data")
    assert f["operator"] == "F"
    assert f["incident"] == "duty"


def test_obligation_and_permission_incidents_unchanged():
    assert eng.formula_from_fields("obligation", "x", "act")["incident"] == "duty"
    assert eng.formula_from_fields("permission", "x", "read")["incident"] == "privilege"
