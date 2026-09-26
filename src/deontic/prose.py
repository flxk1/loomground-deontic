# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Lower one English prose sentence to deontic formulae — deterministically.

Purpose: read the operator (O/P/F), the bearer and the action — and, where the
text states them, the condition and the exception — out of a plain English
sentence such as *"The controller must not make a solely automated decision on a
credit application."* → ``F(controller : make a solely automated decision on a
credit application)``.

Every cue comes from the published extraction data
(``artifacts/extraction.json``: ``modal_cues`` and ``slot_cues``); this module
keeps no second copy of them. It is a surface lowering, not reasoning: it never
guesses, and a sentence it cannot read cleanly lowers to ``[]`` (no norm) rather
than to a wrong one. A negated modal ("must not", "shall not", "may not") lowers
to F, never to an obligation to do the forbidden act (the rule of
:func:`deontic.formula.formula_from_fields`). The formal statement grammar
(:func:`deontic.grammar.parse`) is untouched; this is a separate entry for prose.

Scope (defaults): English only; one norm per sentence (the earliest modal cue);
a bearer is the subject noun phrase before the modal with its leading article
removed; a sentence whose subject contains a clause marker ("that", "which",
"who", ...) is left alone (an embedded norm is not asserted by the sentence).
Standard library only.
"""
from __future__ import annotations

import re

from .artifacts import load_json
from .formula import DeonticFormula, formula_from_fields

__all__ = ["extract"]

_EX = load_json("extraction.json")
# (modal class, compiled cue) in published order; a tie on position goes to the
# earlier cue, so "must not" (prohibition, listed first) wins over "must".
_MODAL_CUES = tuple((c["modal"], re.compile(c["pattern"], re.I)) for c in _EX["modal_cues"])
_CONDITION_LEAD = re.compile(_EX["slot_cues"]["condition_lead"], re.I)
_EXCEPTION_LEAD = re.compile(_EX["slot_cues"]["exception_lead"], re.I)
_CONDITION_TAIL = re.compile(_EX["slot_cues"]["condition_tail"], re.I)

# English surface grammar the lowering needs (not deontic vocabulary): articles and
# quantifiers that open a subject noun phrase, and clause markers a bearer never holds.
_DETERMINER = re.compile(r"^(?:the|a|an|every|each|any|all|such|this|that)\s+", re.I)
_NEGATIVE_DETERMINER = re.compile(r"^no\s+", re.I)
_CLAUSE_MARKER = re.compile(r"\b(?:that|which|who|whom|whose|knows|believes|says|said)\b",
                            re.I)
# The published modal cues are bilingual; this lowering reads English word order only,
# so a sentence whose modal is one of the German cue surfaces lowers to [] (not guessed).
_GERMAN_MODAL = re.compile(r"^(?:darf|muss|m(?:ü|u)ssen|hat\s+zu|kann)\b", re.I)
_TRAIL = " \t\r\n.;:!?,"
_MAX_BEARER_WORDS = 6


def _first_modal(text: str):
    best = None
    for rank, (modal, cue) in enumerate(_MODAL_CUES):
        m = cue.search(text)
        if m and (best is None or (m.start(), rank) < (best[1].start(), best[2])):
            best = (modal, m, rank)
    return best


def extract(sentence: str) -> list[DeonticFormula]:
    """The deontic formulae one English sentence states: ``[]`` or one formula.

    Pure and deterministic. ``raw_sentence`` on the formula is the input unchanged.
    """
    if not isinstance(sentence, str):
        return []
    text = sentence.strip().rstrip(_TRAIL)
    if not text:
        return []

    condition = ""
    m = _CONDITION_LEAD.match(text)
    if m:
        condition = m.group("cond").strip(_TRAIL)
        text = text[m.end():].strip()

    found = _first_modal(text)
    if found is None:
        return []
    modal, cue, _ = found

    exception = ""
    m = _EXCEPTION_LEAD.search(text, cue.end())
    if m:
        exception = m.group("exc").strip(_TRAIL)
        text = text[:m.start()].rstrip(_TRAIL)

    subject = text[:cue.start()].strip(_TRAIL)
    action = text[cue.end():].strip(_TRAIL)

    m = _CONDITION_TAIL.search(action)
    if m:
        tail = m.group("cond").strip(_TRAIL)
        condition = f"{condition}; {tail}" if condition else tail
        action = action[:m.start()].strip(_TRAIL)

    # the modal must be English, the subject a plain noun phrase, the action non-empty
    if _GERMAN_MODAL.match(cue.group(0)) or not subject or not action:
        return []
    if _CLAUSE_MARKER.search(subject):
        return []
    if _NEGATIVE_DETERMINER.match(subject):
        # "No person shall/may X" forbids X for every person: a prohibition.
        subject = _NEGATIVE_DETERMINER.sub("", subject)
        modal = "prohibition"
    bearer = _DETERMINER.sub("", subject).strip()
    if not bearer or len(bearer.split()) > _MAX_BEARER_WORDS:
        return []

    return [formula_from_fields(modal, bearer, action, condition=condition,
                                exception=exception, language="en",
                                raw_sentence=sentence)]
