# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A negated surface modal must not silently become an obligation.

``formula_from_fields`` keys ``MODAL_TO_OP`` on the canonical force names
(obligation/permission/prohibition/right). A negated modal phrase — "must not",
"shall not", "may not", "cannot", "is not permitted to" — is none of those, so
the pre-fix code fell through to the O fallback: a prohibition transcribed as an
obligation to do the very act it forbids. That is a governance-safety inversion,
so a negated modal now lowers to F and a genuinely unrecognised modal fails
closed rather than asserting a duty no source states.

    python -m pytest tests/test_negated_modal.py
"""
from __future__ import annotations

import pytest

import deontic
from deontic import operators


NEGATED = [
    "must not",
    "shall not",
    "may not",
    "cannot",
    "can not",
    "must never",
    "shall never",
    "is not permitted to",
    "is not allowed to",
    "not entitled to",
]


@pytest.mark.parametrize("modal", NEGATED)
def test_negated_modal_lowers_to_prohibition(modal):
    f = deontic.formula_from_fields(
        modal, "processor", "disclose the data",
        raw_sentence=f"The processor {modal} disclose the data.")
    assert f.operator == operators.OP_PROHIBITION, (
        f"{modal!r} must lower to F, not {f.operator}")


@pytest.mark.parametrize("modal", NEGATED)
def test_negated_modal_is_never_an_obligation(modal):
    # The exact inversion the defect produced: a prohibition read as O(act).
    f = deontic.formula_from_fields(modal, "processor", "disclose the data")
    assert f.operator != operators.OP_OBLIGATION


def test_negated_modal_does_not_negate_the_action():
    # A prohibition is carried by operator F, not by negating the proposition.
    f = deontic.formula_from_fields("must not", "processor", "disclose the data")
    assert f.negated is False
    assert f.render() == "F(processor : disclose the data)"


def test_affirmative_canonical_names_are_unchanged():
    assert deontic.formula_from_fields("obligation", "x", "act").operator == "O"
    assert deontic.formula_from_fields("permission", "x", "act").operator == "P"
    assert deontic.formula_from_fields("prohibition", "x", "act").operator == "F"
    assert deontic.formula_from_fields("right", "x", "act").operator == "P"


def test_unrecognised_modal_fails_closed():
    # An unrecognised, non-negated modal must not silently assert a duty.
    with pytest.raises(ValueError, match="unrecognised deontic modal"):
        deontic.formula_from_fields("recommendation", "x", "do y")
    with pytest.raises(ValueError, match="unrecognised deontic modal"):
        deontic.formula_from_fields("gobbledygook", "x", "do y")
