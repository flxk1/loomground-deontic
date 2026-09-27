# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Phase 1: the recursive-descent prose grammar over the ten named phrase
shapes (legal-prose-parsing-design-2026-09-27.md, Candidate A patched).

    python -m pytest tests/test_prose_grammar_phrases.py
"""
from __future__ import annotations

import pytest

import deontic
from deontic import plane as dplane
from deontic import prose_grammar

NEGATIVE_ACTION = "disclose the data"

NEGATIVE_PHRASES = [
    "The lender shall never disclose the data.",
    "The lender must never disclose the data.",
    "The lender may never disclose the data.",
    "The lender shall at no time disclose the data.",
    "The lender shall, at no time, disclose the data.",
    "The lender shall never, under any circumstances, disclose the data.",
    "The lender shall not, under any circumstances, disclose the data.",
    "The lender may not, at any time, disclose the data.",
]


@pytest.mark.parametrize("sentence", NEGATIVE_PHRASES)
def test_negative_phrases_lower_to_prohibition_with_clean_action(sentence):
    (f,) = deontic.extract_prose(sentence)
    assert f.operator == "F"
    assert f.bearer == "lender"
    assert f.action == NEGATIVE_ACTION
    assert f.negated is False  # F carries the negation; never a second copy
    for leak in ("never", "not", "at no time", "at any time", "under any circumstances"):
        assert leak not in f.action


def test_exception_phrase_save_as_permitted_excludes_exception_from_action():
    sentence = ("The processor shall not disclose the data to any third party, "
                "save as permitted.")
    (f,) = deontic.extract_prose(sentence)
    assert f.operator == "F"
    assert f.action == "disclose the data to any third party"
    assert f.exception == "permitted"
    (claim,) = dplane.produce(sentence)
    assert claim["coordinates"]["exception_status"] != prose_grammar.NONE_DETECTED


def test_exception_phrase_unless_required_by_law_excludes_exception_from_action():
    sentence = "The processor shall not disclose the data, unless required by law."
    (f,) = deontic.extract_prose(sentence)
    assert f.operator == "F"
    assert f.action == "disclose the data"
    assert f.exception == "required by law"
    (claim,) = dplane.produce(sentence)
    assert claim["coordinates"]["exception_status"] != prose_grammar.NONE_DETECTED
    assert claim["coordinates"]["exception_status"] == prose_grammar.EXCEPTION_EXTERNAL_UNRESOLVED


def test_positive_modals_are_unaffected():
    (f_shall,) = deontic.extract_prose("The lender shall disclose the data.")
    (f_must,) = deontic.extract_prose("The lender must disclose the data.")
    (f_may,) = deontic.extract_prose("The lender may disclose the data.")
    assert (f_shall.operator, f_must.operator, f_may.operator) == ("O", "O", "P")
    for f in (f_shall, f_must, f_may):
        assert f.action == NEGATIVE_ACTION
