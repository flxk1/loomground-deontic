# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Scope/effect (constitutive, non-duty) statements.

A sentence whose action opens on a scope/effect verb phrase about an
instrument or provision — "apply to", "apply from", "affect", "preclude",
"be without prejudice to" (``artifacts/gazetteer/scope_verbs.json``, the sole
source of this list — no inline copy lives in ``deontic.prose_grammar``) — is
constitutive: it states what the instrument does or covers, not a bearer's
duty. ``deontic.prose_grammar.analyze`` abstains the whole frame with the
documented reason code ``SCOPE_STATEMENT``: ``operator == ""``,
``field_reasons["operator"] == pg.SCOPE_STATEMENT`` (the repo's abstention
form for "no modality" — see ``ProseFrame``/``ABSTAIN_REASONS``), no bearer,
no action_head.

    python -m pytest tests/test_scope_statements.py
"""
from __future__ import annotations

import pytest

from deontic import prose_grammar as pg


def _assert_scope_statement(frame):
    assert frame.operator == ""
    assert frame.field_reasons.get("operator") == pg.SCOPE_STATEMENT
    assert frame.bearer == ""
    assert frame.field_reasons.get("bearer") == pg.SCOPE_STATEMENT
    assert frame.action_head == ""
    assert frame.field_reasons.get("action_head") == pg.SCOPE_STATEMENT
    assert frame.accepted is False
    assert frame.reason == pg.SCOPE_STATEMENT


@pytest.mark.parametrize("sentence", [
    "This Regulation shall not apply to processing carried out by a natural person.",
    "This Regulation shall apply to processing carried out by a controller.",
    "This Article shall not affect the application of Regulation (EU) 2016/679.",
    "This Article shall affect the application of Regulation (EU) 2016/679.",
    "This Chapter shall be without prejudice to the powers of supervisory authorities.",
    "This Regulation shall not preclude Member State law.",
    "This Regulation shall preclude Member State law.",
    "This Regulation shall apply from 25 May 2018.",
    "This Regulation shall not apply from 25 May 2018.",
    "This Chapter shall not be without prejudice to the powers of supervisory authorities.",
])
def test_scope_statement_patterns_negated_and_positive(sentence):
    frame = pg.analyze(sentence)
    _assert_scope_statement(frame)


# ── control: an ordinary duty with a personal bearer is NOT a scope
#    statement — "apply" alone (not "apply to"/"apply from") is not a scope
#    verb, so the ordinary reading must still yield O with a bearer ──────────
def test_ordinary_duty_control_still_yields_O_with_bearer():
    frame = pg.analyze("The controller shall apply appropriate measures.")
    assert frame.operator == "O"
    assert frame.bearer == "controller"
    assert frame.action_head == "apply"
    assert "operator" not in frame.field_reasons
    assert "bearer" not in frame.field_reasons
    assert "action_head" not in frame.field_reasons


def test_scope_statement_is_a_typed_abstain_reason():
    assert pg.SCOPE_STATEMENT in pg.ABSTAIN_REASONS


# ── a scope statement keeps the exception the sibling-constituent scan found;
#    only the scope phrase itself ("be without prejudice to") is not one ──────
@pytest.mark.parametrize("sentence,status,exception", [
    ("This Regulation shall not apply to processing unless required by Union law.",
     pg.EXCEPTION_EXTERNAL_UNRESOLVED, "required by Union law"),
    ("This Regulation shall not apply to processing, without prejudice to Article 6(2).",
     pg.EXCEPTION_XREF_UNRESOLVED, "Article 6(2)"),
])
def test_scope_statement_keeps_a_detected_exception(sentence, status, exception):
    frame = pg.analyze(sentence)
    _assert_scope_statement(frame)
    assert frame.exception_status == status
    assert frame.exception == exception
    assert frame.certainty["exception_status"] == pg.AMBIGUOUS
    assert frame.field_reasons.get("exception_status") == status


@pytest.mark.parametrize("sentence", [
    "This Chapter shall be without prejudice to the powers of supervisory authorities.",
    "This Regulation shall not apply to processing.",
])
def test_scope_phrase_itself_is_not_an_exception(sentence):
    frame = pg.analyze(sentence)
    _assert_scope_statement(frame)
    assert frame.exception_status == pg.NONE_DETECTED
    assert frame.exception == ""
