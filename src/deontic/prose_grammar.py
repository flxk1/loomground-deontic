# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""A stdlib-only, deterministic recursive-descent parser for one English
prose sentence, compiled from and kept in sync with
``artifacts/grammar/deontic.ebnf`` (the ``modal_frame`` production appended
there for Phase 1).

    modal_frame = subject, modal_head, interposed*, negation?, action ;

``condition`` and ``exception`` are sibling constituents of the frame, never
nested inside it (``statement`` in the grammar). This module replaces the
regex "modal cue" table :mod:`deontic.prose` used to walk (Round 5 and
earlier): the productions are table-driven — every language-specific surface
(modal lexemes, interposed phrases, negation adverbs, condition/exception
leads, the exception content markers) is a JSON gazetteer under
``artifacts/gazetteer/``, not a hard-coded pattern. Regex is used only to
tokenise (:data:`_TOKEN_RE`); every decision after that — where the modal
head sits, what counts as interposed material, whether a negation adverb
follows, where the action span begins and ends, whether an exception clause
is present and how it classifies — is a walk over the token list against a
loaded table, never a compiled pattern search.

The single truth table the grammar dispatches into for the operator is
:data:`_NEGATED_MODAL`: ``(lexeme, negated) -> operator``. Mutating one cell
of that table changes the operator a matching sentence lowers to — the
mutation the conformance suite exercises (``tests/test_prose_grammar_dispatch.py``
and ``tests/test_prose_grammar_phrases.py``).

Every emitted field — operator, bearer, action, condition, exception_status —
carries a certainty in ``{CERTAIN, INFERRED, AMBIGUOUS}`` (:data:`CERTAINTY`).
A sentence the parser cannot ground abstains (accepted=False) with a typed
reason code (:data:`ABSTAIN_REASONS`); it never guesses. An exception clause
that is found but not resolvable to a local text (a cross-reference to
another article, or to law/statute outside the instrument) does not abstain
the whole sentence — only its own field carries the unresolved status: no
cross-reference resolver is built (out of scope), so ``EXCEPTION_XREF_UNRESOLVED``
/ ``EXCEPTION_EXTERNAL_UNRESOLVED`` are terminal, published statuses, not a
promise of a future resolution.

Standard library only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .artifacts import load_json

__all__ = [
    "CERTAIN", "INFERRED", "AMBIGUOUS", "CERTAINTY",
    "ACTION_IMPLICIT", "NO_MODAL", "AMBIGUOUS_NEGATION", "AMBIGUOUS_SUBJECT",
    "EXCEPTION_XREF_UNRESOLVED", "EXCEPTION_EXTERNAL_UNRESOLVED",
    "CONDITION_ADVERBIAL_AMBIGUOUS", "ABSTAIN_REASONS",
    "NONE_DETECTED", "INTERNAL_PARSED", "EXCEPTION_STATUSES",
    "ProseFrame", "analyze", "classify_exception_status",
]

# ── certainty vocabulary ──────────────────────────────────────────────
CERTAIN = "CERTAIN"
INFERRED = "INFERRED"
AMBIGUOUS = "AMBIGUOUS"
CERTAINTY = (CERTAIN, INFERRED, AMBIGUOUS)

# ── typed abstention reason codes (per field) ──────────────────────────
ACTION_IMPLICIT = "ACTION_IMPLICIT"
NO_MODAL = "NO_MODAL"
AMBIGUOUS_NEGATION = "AMBIGUOUS_NEGATION"
AMBIGUOUS_SUBJECT = "AMBIGUOUS_SUBJECT"
EXCEPTION_XREF_UNRESOLVED = "EXCEPTION_XREF_UNRESOLVED"
EXCEPTION_EXTERNAL_UNRESOLVED = "EXCEPTION_EXTERNAL_UNRESOLVED"
CONDITION_ADVERBIAL_AMBIGUOUS = "CONDITION_ADVERBIAL_AMBIGUOUS"
ABSTAIN_REASONS = frozenset({
    ACTION_IMPLICIT, NO_MODAL, AMBIGUOUS_NEGATION, AMBIGUOUS_SUBJECT,
    EXCEPTION_XREF_UNRESOLVED, EXCEPTION_EXTERNAL_UNRESOLVED,
    CONDITION_ADVERBIAL_AMBIGUOUS,
})

# ── exception_status vocabulary (stored on the deontic coordinate, next to
#    the operator — see deontic.plane.claim_for / deontic.plane.read_polarity) ─
NONE_DETECTED = "none_detected"
INTERNAL_PARSED = "internal_parsed"
EXCEPTION_STATUSES = (NONE_DETECTED, INTERNAL_PARSED,
                      EXCEPTION_XREF_UNRESOLVED, EXCEPTION_EXTERNAL_UNRESOLVED)

# ── the grammar's one and only truth table: (lexeme, negated) -> operator ──
# The grammar dispatches into this table; it is not derived from a pattern.
_NEGATED_MODAL: dict[tuple[str, bool], str] = {
    ("shall", False): "O", ("shall", True): "F",
    ("must", False): "O", ("must", True): "F",
    ("may", False): "P", ("may", True): "F",
}

# ── tokeniser: the ONLY regex in this module; used for tokenisation only ──
# Digits are word tokens too (e.g. "Article 6"): a bare number embedded in a
# condition/exception span must not fall out of the token stream and truncate
# the slice that reconstructs the surface text.
_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|[,;:()]")
_TRAIL = " \t\r\n.;:!?,"
_MAX_BEARER_WORDS = 6


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    is_word: bool

    @property
    def lower(self) -> str:
        return self.text.lower()


def _tokenize(text: str) -> list[Token]:
    out = []
    for m in _TOKEN_RE.finditer(text):
        t = m.group(0)
        out.append(Token(t, m.start(), m.end(), t[0].isalpha()))
    return out


def _load_gazetteer(name: str) -> dict:
    return load_json("gazetteer", f"{name}.json")


def _phrase_words(phrase: str) -> list[str]:
    return phrase.lower().split()


def _sorted_phrases(entries: list[dict], phrase_key: str = "phrase") -> list[tuple[list[str], dict]]:
    """Entries as (words, entry), longest phrase (most words) first."""
    out = [(_phrase_words(e[phrase_key]), e) for e in entries]
    out.sort(key=lambda pair: -len(pair[0]))
    return out


def _match_words_at(tokens: list[Token], i: int, words: list[str]) -> int | None:
    """``i + len(words)`` when ``tokens[i:]`` spells ``words`` (word tokens,
    case-insensitive, contiguous over word-kind tokens only); ``None`` else."""
    j = i
    for w in words:
        if j >= len(tokens) or not tokens[j].is_word or tokens[j].lower != w:
            return None
        j += 1
    return j


def _match_longest(tokens: list[Token], i: int,
                    ranked: list[tuple[list[str], dict]]) -> tuple[int, dict] | None:
    for words, entry in ranked:
        end = _match_words_at(tokens, i, words)
        if end is not None:
            return end, entry
    return None


def _skip_delimiters(tokens: list[Token], i: int) -> int:
    while i < len(tokens) and not tokens[i].is_word:
        i += 1
    return i


def _slice(text: str, tokens: list[Token], i: int, j: int) -> str:
    """The original substring spanning ``tokens[i:j]`` (inclusive start,
    exclusive end); ``""`` for an empty range."""
    if i >= j or i >= len(tokens) or j <= 0:
        return ""
    return text[tokens[i].start:tokens[j - 1].end].strip(_TRAIL).strip()


@dataclass(frozen=True)
class ProseFrame:
    """The parser's full result for one sentence: accepted fields with
    per-field certainty, or a typed abstention. Never a guess."""

    accepted: bool
    reason: str = ""
    operator: str = ""
    modal_lexeme: str = ""
    bearer: str = ""
    action: str = ""
    condition: str = ""
    exception: str = ""
    exception_status: str = NONE_DETECTED
    negated: bool = False
    certainty: dict[str, str] = field(default_factory=dict)


def classify_exception_status(exception_text: str) -> str:
    """The exception_status a clause's own text implies — a pure function of
    the text, so it agrees whether the clause came from the parser or from a
    published conformance vector. No cross-reference is resolved: an
    ``Article N`` / ``law`` marker only classifies the clause as unresolved.
    """
    if not (exception_text or "").strip():
        return NONE_DETECTED
    gaz = _load_gazetteer("exception")
    words = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ§]+", exception_text)}
    if any(marker.rstrip(".") in words or marker in exception_text.lower()
           for marker in gaz["xref_markers"]):
        return EXCEPTION_XREF_UNRESOLVED
    if any(term in words for term in gaz["external_terms"]):
        return EXCEPTION_EXTERNAL_UNRESOLVED
    return INTERNAL_PARSED


def _find_condition_lead(text: str, tokens: list[Token]) -> tuple[str, int]:
    """A sentence-initial condition clause up to the first top-level comma.

    Returns ``(condition_text, token_index_after_comma)``; ``("", 0)`` when
    no condition lead opens the sentence.
    """
    if not tokens:
        return "", 0
    gaz = _load_gazetteer("condition")
    ranked = _sorted_phrases([{"phrase": p} for p in gaz["lead_phrases"]])
    m = _match_longest(tokens, 0, ranked)
    if m is None:
        return "", 0
    lead_end, _entry = m
    for k in range(lead_end, len(tokens)):
        if tokens[k].text == ",":
            cond = _slice(text, tokens, lead_end, k)
            return cond, k + 1
    return "", 0


def _find_condition_tail(text: str, tokens: list[Token], start: int, end: int) -> tuple[int, str, bool]:
    """A trailing condition clause within ``tokens[start:end]`` (the action
    span). Returns ``(new_end, condition, ambiguous)``: ``ambiguous=True``
    means the tail is present but not safely a condition (abstain rather
    than guess), matching the whole-frame abstention this always causes.
    """
    gaz = _load_gazetteer("condition")
    leads = {w for p in gaz["tail_leads"] for w in [p.split()[0]]}
    embedded_markers = set(_load_gazetteer("lexicon")["embedded_markers"])
    clause_verbs = set(_load_gazetteer("lexicon")["clause_verbs"])
    for k in range(start, end):
        if tokens[k].is_word and tokens[k].lower in leads:
            tail_words = {t.lower for t in tokens[k:end] if t.is_word}
            before_words = {t.lower for t in tokens[start:k] if t.is_word}
            if not (tail_words & clause_verbs) or (before_words & embedded_markers):
                return end, "", True
            cond = _slice(text, tokens, k, end)
            return k, cond, False
    return end, "", False


def analyze(sentence: str) -> ProseFrame:
    """Parse one English sentence to a :class:`ProseFrame`.

    Deterministic and pure: no I/O, no randomness. Abstains (``accepted=False``)
    rather than emit a guess, per the shapes documented on :mod:`deontic.prose`.
    """
    if not isinstance(sentence, str):
        return ProseFrame(accepted=False, reason=NO_MODAL)
    text = sentence.strip().rstrip(_TRAIL)
    if not text:
        return ProseFrame(accepted=False, reason=NO_MODAL)

    tokens = _tokenize(text)

    condition, after_cond = _find_condition_lead(text, tokens)

    modal_gaz = _sorted_phrases(_load_gazetteer("modal_lexemes")["phrases"])

    # earliest modal_head match over the (post-condition) token stream
    found = None
    for i in range(after_cond, len(tokens)):
        m = _match_longest(tokens, i, modal_gaz)
        if m is not None:
            end, entry = m
            found = (i, end, entry["lexeme"], entry.get("operator"))
            break
    if found is None:
        return ProseFrame(accepted=False, reason=NO_MODAL,
                          certainty={"operator": AMBIGUOUS})
    modal_start, modal_end, lexeme, forced_operator = found

    subject = _slice(text, tokens, after_cond, modal_start)

    # exception is a sibling constituent: locate it first over the whole
    # remainder, so the action span excludes it regardless of the frame walk.
    exception_gaz = _load_gazetteer("exception")
    exc_ranked = _sorted_phrases([{"phrase": p} for p in exception_gaz["lead_phrases"]])
    exc_start = len(tokens)
    for i in range(modal_end, len(tokens)):
        m = _match_longest(tokens, i, exc_ranked)
        if m is not None:
            exc_start = i
            break
    frame_end = exc_start
    exception = _slice(text, tokens, exc_start, len(tokens)) if exc_start < len(tokens) else ""
    if exception:
        # drop the lead phrase itself from the published exception text
        m = _match_longest(tokens, exc_start, exc_ranked)
        lead_end, _entry = m
        exception = _slice(text, tokens, lead_end, len(tokens))

    # interposed* and negation? — a mixed run of gazetteer interposed phrases,
    # single-word negation adverbs, and comma/paren delimiters, in whichever
    # order the surface holds them; the loop stops at the first token that
    # matches neither (that token opens `action`).
    interposed_gaz = _sorted_phrases(_load_gazetteer("interposed")["phrases"])
    negation_adverbs = set(_load_gazetteer("negation")["adverbs"])
    pos = modal_end
    negated = False
    negation_count = 0
    saw_interposed = False
    while pos < frame_end:
        skip = _skip_delimiters(tokens, pos)
        if skip > pos:
            pos = skip
            continue
        m = _match_longest(tokens, pos, interposed_gaz)
        if m is not None:
            end, entry = m
            if entry.get("negating"):
                negated = True
                negation_count += 1
            saw_interposed = True
            pos = end
            continue
        if tokens[pos].is_word and tokens[pos].lower in negation_adverbs:
            negated = True
            negation_count += 1
            pos += 1
            continue
        break

    action_end = frame_end
    new_end, tail_condition, ambiguous = _find_condition_tail(text, tokens, pos, action_end)
    if ambiguous:
        return ProseFrame(accepted=False, reason=CONDITION_ADVERBIAL_AMBIGUOUS,
                          certainty={"condition": AMBIGUOUS})
    if tail_condition:
        condition = f"{condition}; {tail_condition}" if condition else tail_condition
        action_end = new_end

    action = _slice(text, tokens, pos, action_end)

    lexicon = _load_gazetteer("lexicon")
    negative_determiner = lexicon["negative_determiner"]
    determiners = set(lexicon["determiners"])
    clause_markers = set(lexicon["clause_markers"])
    non_bearer = set(lexicon["non_bearer_subjects"])
    state_prefixes = [tuple(p) for p in lexicon["state_action_prefixes"]]

    if not subject or not action:
        return ProseFrame(accepted=False, reason=ACTION_IMPLICIT if subject else AMBIGUOUS_SUBJECT,
                          certainty={"action": AMBIGUOUS} if subject else {"bearer": AMBIGUOUS})

    subject_words = subject.split()
    if any(w.lower() in clause_markers for w in subject_words):
        return ProseFrame(accepted=False, reason=AMBIGUOUS_SUBJECT,
                          certainty={"bearer": AMBIGUOUS})
    if subject.lower() in non_bearer:
        return ProseFrame(accepted=False, reason=AMBIGUOUS_SUBJECT,
                          certainty={"bearer": AMBIGUOUS})

    action_words = [w.lower() for w in action.split()]
    for prefix in state_prefixes:
        if tuple(action_words[:len(prefix)]) == prefix:
            return ProseFrame(accepted=False, reason=ACTION_IMPLICIT,
                              certainty={"action": AMBIGUOUS})

    forced_prohibition = False
    if subject_words and subject_words[0].lower() == negative_determiner:
        subject = " ".join(subject_words[1:])
        forced_prohibition = True

    bearer = subject
    if bearer.split() and bearer.split()[0].lower() in determiners:
        bearer = " ".join(bearer.split()[1:])
    if not bearer or len(bearer.split()) > _MAX_BEARER_WORDS:
        return ProseFrame(accepted=False, reason=AMBIGUOUS_SUBJECT,
                          certainty={"bearer": AMBIGUOUS})

    # Two negation adverbs/negating-interposed-phrases in one frame ("shall
    # never not disclose ...") do not cancel to an affirmative by convention
    # here: the double negation is ambiguous on its face, so the whole frame
    # abstains rather than collapsing to either polarity.
    if negation_count >= 2:
        return ProseFrame(accepted=False, reason=AMBIGUOUS_NEGATION,
                          certainty={"operator": AMBIGUOUS})

    if forced_prohibition:
        operator = "F"
    elif forced_operator:
        operator = forced_operator
    else:
        operator = _NEGATED_MODAL.get((lexeme, negated))
    if operator is None:
        return ProseFrame(accepted=False, reason=AMBIGUOUS_NEGATION,
                          certainty={"operator": AMBIGUOUS})

    exception_status = classify_exception_status(exception)
    # Certainty is computed, not a hard-coded constant: a field is CERTAIN only
    # when its value came straight off a cue anchor (the subject immediately
    # before the modal head; a condition matched by a sentence-initial lead
    # phrase); a field reached by a weaker, non-anchoring route (the bearer
    # after stripping a negative determiner that itself carried the semantics
    # of the whole clause; a condition assembled from a trailing adverbial
    # lead rather than a sentence-initial cue) is INFERRED instead.
    certainty = {
        "operator": CERTAIN,
        "bearer": INFERRED if forced_prohibition else CERTAIN,
        "action": CERTAIN,
        "condition": INFERRED if tail_condition else CERTAIN,
        "exception_status": CERTAIN if exception_status in (NONE_DETECTED, INTERNAL_PARSED)
                            else AMBIGUOUS,
    }
    return ProseFrame(
        accepted=True, operator=operator, modal_lexeme=lexeme, bearer=bearer,
        action=action, condition=condition, exception=exception,
        exception_status=exception_status, negated=False, certainty=certainty,
    )
