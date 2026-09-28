# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Lower one English prose sentence to deontic formulae — deterministically.

Purpose: read the operator (O/P/F), the bearer and the action — and, where the
text states them, the condition and the exception — out of a plain English
sentence such as *"The controller must not make a solely automated decision on a
credit application."* → ``F(controller : make a solely automated decision on a
credit application)``.

Phase 1: the surface walk is a stdlib recursive-descent parser
(:mod:`deontic.prose_grammar`), compiled from and kept in sync with
``artifacts/grammar/deontic.ebnf``'s ``modal_frame`` production. Every
language-specific cue — modal lexemes, interposed material ("under any
circumstances", "at any time", "at no time"), negation adverbs, condition and
exception leads, the exception content markers — is a JSON gazetteer under
``artifacts/gazetteer/``, not a pattern compiled here. :func:`extract` is a
**thin compatibility layer**: it keeps the pre-Phase-1 name and signature
(``sentence -> list[DeonticFormula]``, ``[]`` or one formula) so existing
callers (:mod:`deontic.plane`, and any consumer that imported ``extract_prose``)
keep working unchanged. :func:`parse` is the richer Phase 1 reader — it
returns the full :class:`~deontic.prose_grammar.ProseFrame`, with a per-field
certainty and, on abstention, a typed reason code; use it where those matter.

It abstains (returns ``[]`` from :func:`extract`, or an unaccepted
:class:`~deontic.prose_grammar.ProseFrame` from :func:`parse`) instead of
emitting a guess in each of the cases documented on
:class:`deontic.prose_grammar.ProseFrame` / :data:`deontic.prose_grammar.ABSTAIN_REASONS`:
no modal cue found; an empty or ambiguous subject or action (a clause marker,
an expletive/demonstrative subject, or a subject longer than six words); an
action that opens with a copula or a passive auxiliary (a state, not an act);
a trailing condition phrase that is not safely a clause (an adverbial can look
like one). An exception clause that names an external law or an unresolved
cross-reference does **not** abstain the sentence — no resolver is built, so
that status is carried on the emitted norm instead (``exception_status``, read
back with :func:`deontic.plane.read_polarity`).

Scope (defaults): English only; one norm per sentence (the earliest modal
cue); a bearer is the subject noun phrase before the modal with its leading
article removed; "No X shall/may ..." lowers to F with bearer X. Standard
library only — this module itself imports no regex; :mod:`deontic.prose_grammar`
uses one, for tokenisation only.
"""
from __future__ import annotations

from . import prose_grammar
from .formula import DeonticFormula, formula_from_fields

__all__ = ["extract", "parse"]


def parse(sentence: str) -> prose_grammar.ProseFrame:
    """The full Phase 1 parse of one English sentence.

    Pure and deterministic. Returns a :class:`~deontic.prose_grammar.ProseFrame`
    — ``accepted`` fields with per-field certainty, or an unaccepted frame with
    a typed abstention reason (:data:`deontic.prose_grammar.ABSTAIN_REASONS`).
    """
    return prose_grammar.analyze(sentence)


def extract(sentence: str) -> list[DeonticFormula]:
    """The deontic formulae one English sentence states: ``[]`` or one formula.

    Pure and deterministic. ``raw_sentence`` on the formula is the input
    unchanged. A thin compatibility layer over :func:`parse`/:mod:`deontic.prose_grammar`:
    kept for existing callers — the public name and signature are unchanged
    from before Phase 1. The returned formula's ``exception_status`` always
    travels with its ``operator``: a norm whose exception is detected but not
    resolved is never handed back as if it were bare, unqualified polarity.
    """
    frame = prose_grammar.analyze(sentence)
    if not frame.accepted:
        return []
    modal = "prohibition" if frame.operator == "F" else (
        "obligation" if frame.operator == "O" else "permission")
    return [formula_from_fields(
        modal, frame.bearer, frame.action,
        condition=frame.condition, exception=frame.exception,
        exception_status=frame.exception_status,
        language="en", raw_sentence=sentence,
    )]
