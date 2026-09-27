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
keeps no second copy of them. It is a surface lowering, not reasoning. A negated
modal ("must not", "shall not", "may not") or a negation adverb after a modal
("not", "never", "at no time"), with or without interposed commas or an
interposed phrase (e.g. "shall never, under any circumstances,"), lowers to F,
with the negation adverb and any interposed phrase consumed by the matched cue
so neither is ever left inside ``action`` and never duplicated onto ``negated``
— never to an obligation to do the forbidden act (the rule of
:func:`deontic.formula.formula_from_fields`).
The formal statement grammar (:func:`deontic.grammar.parse`) is untouched; this
is a separate entry for prose.

What it guarantees, and no more: the result is ``[]`` or exactly one formula; it
is deterministic; and it abstains (``[]``) instead of emitting a formula in each
of the cases listed below, which are the shapes it knows it cannot read. It does
NOT guarantee that every formula it does emit is the right reading of an
arbitrary English sentence: outside the listed shapes a sentence can still be
misread, and a consumer that needs certainty validates the claim downstream.

It abstains when:

  * no English modal cue is found, or the modal is a German cue surface
    (this lowering reads English word order only);
  * the subject or the action is empty, or the subject holds a clause marker
    ("that", "which", "who", "knows", ...: an embedded norm is not asserted);
  * the subject is an expletive or bare demonstrative ("it", "there", "this",
    "that", "these", "those"), which bears no norm ("It must be noted that ...");
  * the action opens with "be"/"been"/"being" or "have/has been": the modal then
    reads as a possibility or necessity of a state ("Processing may be
    necessary.") or as an agentless passive, and the subject is not shown to be
    an agent bearing a duty or a permission to act;
  * a trailing ``slot_cues.condition_tail`` phrase is not a clause (it carries
    no auxiliary or copula, e.g. "after use"), or the action before it holds an
    embedded clause ("ensure that data is deleted after use"): the phrase may be
    an adverbial of the action rather than a condition of the norm, and the
    lowering does not pick one;
  * the bearer is longer than six words.

Scope (defaults): English only; one norm per sentence (the earliest modal cue);
a bearer is the subject noun phrase before the modal with its leading article
removed; "No X shall/may ..." lowers to F with bearer X. A trailing condition is
lifted only when it is a clause, as in "before it is sent".
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
# Subjects that bear no norm: expletives and bare demonstratives.
_NON_BEARER = frozenset({"it", "there", "this", "that", "these", "those"})
# An action that opens with a copula reads a state or an agentless passive, not an act.
_STATE_ACTION = re.compile(r"^(?:be|been|being|ha(?:ve|s)\s+been)\b", re.I)
# A trailing condition is lifted only when it is a clause: it carries an auxiliary
# or a copula ("before it IS sent"); a bare phrase ("after use") is not lifted.
_CLAUSE_VERB = re.compile(r"\b(?:is|are|was|were|be|been|has|have|had|does|do|did|"
                          r"can|could|will|would|shall|should|may|might|must)\b", re.I)
# An embedded clause in the action makes the attachment of a trailing phrase ambiguous.
_EMBEDDED = re.compile(r"\b(?:that|which|whether|who|whom|whose)\b", re.I)
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
        # a bare phrase ("after use") or a tail after an embedded clause may modify
        # the action rather than condition the norm: abstain rather than pick one
        if not _CLAUSE_VERB.search(tail) or _EMBEDDED.search(action[:m.start()]):
            return []
        condition = f"{condition}; {tail}" if condition else tail
        action = action[:m.start()].strip(_TRAIL)

    # the modal must be English, the subject a plain noun phrase, the action non-empty
    if _GERMAN_MODAL.match(cue.group(0)) or not subject or not action:
        return []
    if _CLAUSE_MARKER.search(subject):
        return []
    if subject.lower() in _NON_BEARER or _STATE_ACTION.match(action):
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
