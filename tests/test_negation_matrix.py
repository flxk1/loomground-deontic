# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""L121: negation is counted from every source a sentence can carry it in —
an adverb ("not"/"never"), a negative determiner ("No ..."), and a lexical
device (a fixed negating phrase: a forced-operator modal phrase that already
lexicalises a negated modal — "is prohibited from", "is not permitted to" —
or a negating interposed phrase — "at no time") — never from the adverb/
interposed run alone. The polarity check runs before any forced-operator
dispatch: two or more negators from any combination of these sources always
abstain (``AMBIGUOUS_NEGATION``), never collapse to an operator.

This is a parametrised matrix over three axes:

* ``phrase`` — the modal phrasing style: ``forced_F`` ("is prohibited from",
  a modal_lexemes.json entry with a literal ``operator: F`` that itself
  ``negates``), ``forced_P`` ("is authorised to", a literal ``operator: P``
  entry that does **not** itself negate), ``plain`` ("shall", dispatched
  through the lexeme/negation truth table with no forced operator at all).
* ``extra`` — how many *additional* negators (beyond whatever the phrase
  itself already lexicalises) the sentence adds: 0, 1, or 2.
* ``source`` — which device supplies those additional negators: ``adverb``
  ("not"/"never" after the modal), ``determiner`` ("No ..." on the subject),
  ``lexical`` ("at no time", a negating interposed phrase).

Total negators = ``extra`` + (1 if ``phrase`` is ``forced_F``, since that
phrasing is itself one negator, else 0). 0 or 1 total negator always yields a
defined operator (the phrase's forced operator, or the table's polarity flip
for ``plain``, or a flip forced by a negative determiner overriding a forced
operator — "No controller is authorised to disclose ..." flips the
lexically-forced P to F, since a negative determiner is dispatched ahead of
any forced-operator dispatch); 2 or more total negators always abstains with
``AMBIGUOUS_NEGATION`` regardless of which sources supplied them. The three
literal L121 fixtures are exactly three cells of this grid (``forced_F``/
``adverb``/``extra=1``, an equivalent notPermitted phrasing, and ``plain``/
``determiner``/``extra=1`` combined with an adverb) — see
``test_l121_fixtures_abstain``.

    python -m pytest tests/test_negation_matrix.py
"""
from __future__ import annotations

import pytest

from deontic import prose_grammar as pg


def _total(phrase: str, extra: int) -> int:
    return extra + (1 if phrase == "forced_F" else 0)


# (phrase, source, extra) -> sentence
_SENTENCES: dict[tuple[str, str, int], str] = {
    ("forced_F", "adverb", 0): "The processor is prohibited from disclosing the data.",
    ("forced_F", "adverb", 1): "The processor is prohibited from not disclosing the data.",
    ("forced_F", "adverb", 2): "The processor is prohibited from not never disclosing the data.",
    ("forced_F", "determiner", 0): "The processor is prohibited from disclosing the data.",
    ("forced_F", "determiner", 1): "No processor is prohibited from disclosing the data.",
    ("forced_F", "determiner", 2): "No processor is prohibited from not disclosing the data.",
    ("forced_F", "lexical", 0): "The processor is prohibited from disclosing the data.",
    ("forced_F", "lexical", 1): "The processor is prohibited from at no time disclosing the data.",
    ("forced_F", "lexical", 2): "The processor is prohibited from at no time never disclosing the data.",
    ("forced_P", "adverb", 0): "The controller is authorised to disclose the data.",
    ("forced_P", "adverb", 1): "The controller is authorised to not disclose the data.",
    ("forced_P", "adverb", 2): "The controller is authorised to not never disclose the data.",
    ("forced_P", "determiner", 0): "The controller is authorised to disclose the data.",
    ("forced_P", "determiner", 1): "No controller is authorised to disclose the data.",
    ("forced_P", "determiner", 2): "No controller is authorised to not disclose the data.",
    ("forced_P", "lexical", 0): "The controller is authorised to disclose the data.",
    ("forced_P", "lexical", 1): "The controller is authorised to at no time disclose the data.",
    ("forced_P", "lexical", 2): "The controller is authorised to at no time never disclose the data.",
    ("plain", "adverb", 0): "The processor shall disclose the data.",
    ("plain", "adverb", 1): "The processor shall not disclose the data.",
    ("plain", "adverb", 2): "The processor shall not never disclose the data.",
    ("plain", "determiner", 0): "The processor shall disclose the data.",
    ("plain", "determiner", 1): "No processor shall disclose the data.",
    ("plain", "determiner", 2): "No processor shall never disclose the data.",
    ("plain", "lexical", 0): "The processor shall disclose the data.",
    ("plain", "lexical", 1): "The processor shall at no time disclose the data.",
    ("plain", "lexical", 2): "The processor shall at no time never disclose the data.",
}

def _expected_operator(phrase: str, source: str, extra: int) -> str:
    """The operator a cell dispatches to when its total negator count < 2."""
    if source == "determiner" and extra >= 1:
        # a negative determiner is dispatched ahead of any forced operator or
        # table lookup: "No X ..." always forces F once total negators < 2.
        return "F"
    if phrase == "forced_F":
        return "F"          # the phrase's own forced operator (extra must be 0 here)
    if phrase == "forced_P":
        return "P"          # the phrase's own forced operator; not negated by extra <= 1
    # plain: table dispatch, negated flips O -> F
    return "F" if extra >= 1 else "O"


assert len(_SENTENCES) == 27, "the matrix must cover all 3x3x3 cells"


@pytest.mark.parametrize("phrase,source,extra", sorted(_SENTENCES))
def test_negation_matrix_cell(phrase, source, extra):
    sentence = _SENTENCES[(phrase, source, extra)]
    frame = pg.analyze(sentence)
    total = _total(phrase, extra)

    if total >= 2:
        assert frame.field_reasons.get("operator") == pg.AMBIGUOUS_NEGATION, (
            phrase, source, extra, sentence, frame
        )
        assert frame.accepted is False
        return

    # total in {0, 1}: a defined operator, never AMBIGUOUS_NEGATION.
    assert "operator" not in frame.field_reasons, (phrase, source, extra, sentence, frame)
    assert frame.operator == _expected_operator(phrase, source, extra), (
        phrase, source, extra, sentence, frame
    )


# ── the three literal L121 fixtures, as named tests (not just matrix cells) ──
@pytest.mark.parametrize("sentence", [
    "The processor is prohibited from not disclosing the data.",
    "The controller is not permitted to not disclose the data.",
    "No processor shall never disclose the data.",
])
def test_l121_fixtures_abstain(sentence):
    frame = pg.analyze(sentence)
    assert frame.accepted is False
    assert frame.reason == pg.AMBIGUOUS_NEGATION
    assert frame.field_reasons.get("operator") == pg.AMBIGUOUS_NEGATION
    assert frame.operator == ""
