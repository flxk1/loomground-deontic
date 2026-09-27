# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Negation adverb after a modal — generalised beyond Round-5 defect (a).

``tests/test_prose_never_at_no_time.py`` fixed three literal phrasings ("shall
never", "must never", "shall at no time"). This file locks in the generalised
cue: any negation adverb after a modal ("not", "never", "at no time"), with or
without interposed commas or an interposed phrase between commas (e.g. "shall
never, under any circumstances,"), lowers to F — for every modal that can carry
it, including "may never" (the permission modal was not covered before). The
matched cue consumes the negation adverb and any interposed phrase, so
``action`` is exactly the verb phrase that follows, never a leftover negation
word, "at no time", an interposed phrase, or a stray comma; and ``negated``
stays ``False`` (the prohibition is carried by ``operator="F"``, never by a
second copy of the negation). "must not"/"shall not" keep lowering to F, and
the positive readings ("shall"/"must" -> O, "may" -> P) are unchanged.

    python -m pytest tests/test_prose_negation_adverbs.py
"""
from __future__ import annotations

import pytest

import deontic

NEGATION_VARIANTS = [
    "The lender shall never disclose the data.",
    "The lender must never disclose the data.",
    "The lender may never disclose the data.",
    "The lender shall at no time disclose the data.",
    "The lender shall, at no time, disclose the data.",
    "The lender shall never, under any circumstances, disclose the data.",
    "The lender shall not disclose the data.",
    "The lender must not disclose the data.",
]


@pytest.mark.parametrize("sentence", NEGATION_VARIANTS)
def test_negation_adverb_variants_lower_to_prohibition(sentence):
    (f,) = deontic.extract_prose(sentence)
    assert f.operator == "F"
    assert f.bearer == "lender"
    assert f.action == "disclose the data"
    assert f.negated is False
    # no negation word, "at no time", interposed phrase, or stray comma leaks in
    assert "," not in f.action
    for token in ("never", "not", "at no time", "under any circumstances"):
        assert token not in f.action


def test_must_not_shall_not_and_positive_modals_are_unchanged():
    (f_must_not,) = deontic.extract_prose("The lender must not disclose the data.")
    (f_shall_not,) = deontic.extract_prose("The lender shall not disclose the data.")
    (f_shall,) = deontic.extract_prose("The lender shall disclose the data.")
    (f_must,) = deontic.extract_prose("The lender must disclose the data.")
    (f_may,) = deontic.extract_prose("The lender may disclose the data.")

    assert (f_must_not.operator, f_must_not.action) == ("F", "disclose the data")
    assert (f_shall_not.operator, f_shall_not.action) == ("F", "disclose the data")
    assert (f_shall.operator, f_shall.action) == ("O", "disclose the data")
    assert (f_must.operator, f_must.action) == ("O", "disclose the data")
    assert (f_may.operator, f_may.action) == ("P", "disclose the data")
