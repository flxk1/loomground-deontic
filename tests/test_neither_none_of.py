# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Ledger L128: negative-quantifier and coordinated-negation subjects.

A subject opening with "none of", "neither" (the "Neither X nor Y ..."
coordination), "nobody", or "no one" forces the frame to F exactly like a
bare "no" does (``negation.json``'s ``subject_leads``, checked ahead of
``lexicon.json``'s single-word ``negative_determiner``) — but, unlike "No X
...", none of these names a single resolvable noun phrase, so the bearer
abstains (``AMBIGUOUS_SUBJECT``) rather than guess one side of an unresolved
coordination or a quantified set as if it were the bearer.

A coordinated action ("shall neither VERB nor VERB") is a second, orthogonal
construct: "neither" there negates the frame from the ``negation?``
production (``negation.json``'s ``coordinated_negators``, merged with
``adverbs`` at the point ``deontic.prose_grammar.analyze`` walks that
production) — the bearer resolves normally, and ``action_head`` is the first
of the two coordinated verbs, never the word "neither" itself.

    python -m pytest tests/test_neither_none_of.py
"""
from __future__ import annotations

import pytest

from deontic import prose_grammar as pg


# ── L128's three literal fixtures ─────────────────────────────────────────
def test_none_of_the_processors_abstains_bearer_forces_F():
    frame = pg.analyze("None of the processors shall disclose the data.")
    assert frame.operator == "F"
    assert frame.bearer == ""
    assert frame.field_reasons.get("bearer") == pg.AMBIGUOUS_SUBJECT
    assert frame.action_head == "disclose"
    assert "action_head" not in frame.field_reasons


def test_neither_controller_nor_processor_abstains_bearer_forces_F():
    frame = pg.analyze("Neither the controller nor the processor shall disclose the data.")
    assert frame.operator == "F"
    assert frame.bearer == ""
    assert frame.field_reasons.get("bearer") == pg.AMBIGUOUS_SUBJECT
    assert frame.action_head == "disclose"
    assert "action_head" not in frame.field_reasons


def test_shall_neither_disclose_nor_sell_forces_F_action_head_never_neither():
    frame = pg.analyze("The processor shall neither disclose nor sell the data.")
    assert frame.operator == "F"
    assert frame.bearer == "processor"
    # action_head is 'disclose' (the first coordinated verb) or abstained —
    # it must never be the coordinator word itself.
    assert frame.action_head in ("disclose", "")
    assert frame.action_head != "neither"


# ── the wider negative-quantifier-subject matrix ──────────────────────────
@pytest.mark.parametrize("sentence,expected_bearer_abstains", [
    ("None of the processors shall disclose the data.", True),
    ("None of the controllers shall retain the record.", True),
    ("Neither the controller nor the processor shall disclose the data.", True),
    ("Neither the lender nor the borrower shall disclose the data.", True),
    ("Nobody shall disclose the data.", True),
    ("No one shall disclose the data.", True),
    # control: the existing single-word "no" negative determiner still
    # resolves a bearer from the remaining noun phrase — unaffected.
    ("No processor shall retain the record.", False),
])
def test_negative_subject_matrix(sentence, expected_bearer_abstains):
    frame = pg.analyze(sentence)
    assert frame.operator == "F", (sentence, frame)
    if expected_bearer_abstains:
        assert frame.bearer == "", (sentence, frame)
        assert frame.field_reasons.get("bearer") == pg.AMBIGUOUS_SUBJECT, (sentence, frame)
    else:
        assert frame.bearer != "", (sentence, frame)
        assert "bearer" not in frame.field_reasons, (sentence, frame)


def test_neither_nor_coordination_does_not_leak_into_action_or_action_head():
    frame = pg.analyze("The processor shall neither disclose nor sell the data.")
    assert "neither" not in frame.action
    assert frame.action_head != "neither"
    assert frame.action_head != "nor"
