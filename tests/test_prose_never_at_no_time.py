# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Round-5 defect (a): "never" / "at no time" prohibition clauses.

Before the fix, ``deontic.prose`` had no cue for "shall never", "must never",
or "shall at no time": the bare "shall"/"must" cue matched first, so the
sentence lowered to O with the negation token left inside ``action`` (e.g.
``action == "never disclose the data"``, ``negated == False``) — a prohibition
silently transcribed as an obligation to do the very act it forbids, and with
the wrong action text besides.

The fix (``artifacts/extraction.json`` ``modal_cues``) makes "shall never",
"must never", "shall at no time", and "must at no time" match the prohibition
class *before* the bare obligation cue, consuming the negation token as part
of the matched cue so it never reaches ``action``. This lowers "never"/"at no
time" clauses exactly the way "must not"/"shall not" already lower — the one
convention ``nd-system.json``/``llms.txt`` and the pre-existing
``test_plane.py::test_normative_sentences`` assertion
(``st["negated"] is False  # "must not" is carried by F, not by negation``)
already specify: operator ``F``, ``negated=False``, and the negation token
removed from ``action``.

    python -m pytest tests/test_prose_never_at_no_time.py
"""
from __future__ import annotations

import pytest

import deontic

SENTENCES = [
    "The lender shall never disclose the data.",
    "The lender must never disclose the data.",
    "The lender shall at no time disclose the data.",
]


@pytest.mark.parametrize("sentence", SENTENCES)
def test_never_and_at_no_time_lower_to_prohibition(sentence):
    (f,) = deontic.extract_prose(sentence)
    assert f.operator == "F"
    assert f.bearer == "lender"
    assert f.action == "disclose the data"
    assert f.negated is False  # "F" carries the negation; not a second copy in `negated`


@pytest.mark.parametrize("sentence", SENTENCES)
def test_never_and_at_no_time_match_must_not_shall_not_convention(sentence):
    # Same convention as the pre-existing "must not" / "shall not" cases: the
    # negation lives only in operator="F", never as leftover text in `action`,
    # and never duplicated onto `negated`.
    (control,) = deontic.extract_prose("The lender must not disclose the data.")
    (f,) = deontic.extract_prose(sentence)
    assert (f.operator, f.bearer, f.action, f.negated) == (
        control.operator, control.bearer, control.action, control.negated,
    )


def test_must_not_and_shall_not_are_not_regressed():
    for sentence in (
        "The lender shall not disclose the data.",
        "The lender must not disclose the data.",
    ):
        (f,) = deontic.extract_prose(sentence)
        assert (f.operator, f.bearer, f.action, f.negated) == (
            "F", "lender", "disclose the data", False,
        )
