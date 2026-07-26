# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The deontic formula — a norm transcribed into pragmatic Standard Deontic Logic.

Purpose: the formula carrier (operator over a bearer:action pair, with condition
and exception), its rendering to and from the canonical statement string, its
well-formedness/groundedness predicate, and same-bearer/same-action conflict
flagging. This is the algebra's carrier; the operators and laws over it live in
:mod:`deontic.algebra`.

Contract — the two couplings the lift severs:

  * **No surface extractor.** The formula is built from primitive fields
    (:func:`formula_from_fields`), not from a rule-extractor facet. The modal→
    operator mapping is language and lives here; the adapter that reads those
    fields off a host's extracted facet lives in the reasoning layer.
  * **No solver.** No reasoning dimension is assigned here — projecting a formula
    onto a host's dimensions is the consumer's job at its seam.

No inference: SDL has well-known paradoxes (Ross, Good Samaritan, contrary-to-
duty) that automated inference trips over. We transcribe and expose identities;
we do not derive. This module imports only the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .operators import (
    OP_OBLIGATION, VALID_OPERATORS, gloss, dual_of,
)

__all__ = [
    "DeonticFormula", "MODAL_TO_OP", "formula_from_fields", "claim_right",
    "is_grounded", "detect_conflicts",
]

# Surface modal classes → deontic modality. A surface "right" reduces to a P
# (liberty) for the holder; a claim-right (the correlative of someone's duty) is
# the counterparty's O and is carried by the incident/counterparty, not by a
# fourth operator. Anything uncatalogued falls back to O (the safe legal default:
# read an ambiguous norm as a duty and surface it for review).
MODAL_TO_OP: dict[str, str] = {
    "obligation": OP_OBLIGATION,
    "permission": "P",
    "prohibition": "F",
    "right": "P",
}

_UNSPECIFIED = "(unspecified)"


@dataclass
class DeonticFormula:
    """A norm as a deontic formula.

    ``operator`` is one of :data:`~deontic.operators.VALID_OPERATORS`.
    ``negated`` is True when the operator scopes a negative proposition; a
    prohibition is carried by ``operator="F"``, not by negating the action.
    ``incident`` (optional) is the Hohfeldian position from
    :mod:`deontic.incidents`; '' means unclassified.

    ``language``/``raw_sentence``/``confidence`` are provenance metadata carried
    for audit — the algebra's laws never depend on them.
    """

    operator: str
    bearer: str
    action: str
    condition: str = ""
    exception: str = ""
    negated: bool = False
    incident: str = ""
    counterparty: str = ""
    language: str = "en"
    raw_sentence: str = ""
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.operator not in VALID_OPERATORS:
            raise ValueError(f"unknown deontic operator: {self.operator!r}")

    # -- duality ---------------------------------------------------------
    def dual(self) -> str:
        """The operator's defining SDL identity, as a readable string."""
        return dual_of(self.operator, self.action, negated=self.negated)

    # -- rendering -------------------------------------------------------
    def core(self) -> str:
        """The operator applied to (bearer : action), without context."""
        act = f"¬ {self.action}" if self.negated else self.action
        return f"{self.operator}({self.bearer} : {act})"

    def render(self) -> str:
        """The canonical one-line statement, with condition + exception.

        The string this returns is parsed back to an equal formula by
        :func:`deontic.grammar.parse` (round-trip over the structured slots).
        """
        s = self.core()
        if self.condition:
            s = f"if [{self.condition}] then {s}"
        if self.exception:
            s = f"{s} unless [{self.exception}]"
        return s

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["formula"] = self.render()
        d["dual"] = self.dual()
        d["operator_gloss"] = gloss(self.operator)
        d["conditional"] = bool(self.condition)
        d["defeasible"] = bool(self.exception)
        return d


def formula_from_fields(
    modal: str,
    subject: str,
    action: str,
    *,
    condition: str = "",
    exception: str = "",
    incident: str = "",
    counterparty: str = "",
    language: str = "en",
    raw_sentence: str = "",
    confidence: float = 0.0,
) -> DeonticFormula:
    """Build a formula from a norm's primitive fields.

    ``modal`` is a surface modal class (obligation/permission/prohibition/right);
    an uncatalogued class maps to O and drops confidence by 0.1 (the operator is
    then a fallback, not a read). Empty subject/action become ``"(unspecified)"``
    so :func:`is_grounded` can tell a placeholder from a real bearer.
    """
    op = MODAL_TO_OP.get(modal)
    if op is None:
        op = OP_OBLIGATION
        confidence = max(0.0, confidence - 0.1)
    return DeonticFormula(
        operator=op,
        bearer=subject or _UNSPECIFIED,
        action=action or _UNSPECIFIED,
        condition=condition,
        exception=exception,
        negated=False,  # prohibition is carried by operator="F"
        incident=incident,
        counterparty=counterparty,
        language=language,
        raw_sentence=raw_sentence,
        confidence=round(confidence, 3),
    )


def claim_right(
    holder: str,
    action: str,
    obligor: str,
    *,
    condition: str = "",
    exception: str = "",
    language: str = "en",
    raw_sentence: str = "",
    confidence: float = 0.0,
) -> DeonticFormula:
    """Build a **claim-right** as its correlative duty.

    "``holder`` has a right that ``obligor`` φ" *is* "``obligor`` has a duty, owed
    to ``holder``, to φ" — Hohfeld's claim↔duty correlativity. The faithful
    transcription is therefore an obligation on the obligor, not a permission for
    the holder: ``O(obligor : action)`` with ``incident="duty"`` and
    ``counterparty=holder``.

    Use this when a "right" is a **claim** (a right that someone else act — a
    right to erasure, to payment, to notice). For a **liberty** (a freedom to act
    oneself), a permission is correct:
    ``formula_from_fields("permission", holder, action)`` (incident ``privilege``).
    The bare surface ``formula_from_fields("right", …)`` defaults to the liberty
    reading (``P``); a claim-right must be flipped to the obligor, which this
    helper does.
    """
    return DeonticFormula(
        operator=OP_OBLIGATION,
        bearer=obligor or _UNSPECIFIED,
        action=action or _UNSPECIFIED,
        condition=condition,
        exception=exception,
        negated=False,
        incident="duty",           # the obligor bears the duty; the holder holds the claim
        counterparty=holder,
        language=language,
        raw_sentence=raw_sentence,
        confidence=round(confidence, 3),
    )


def is_grounded(f: DeonticFormula) -> bool:
    """A formula is grounded only if it cites its source sentence and names a
    concrete bearer and action — not the ``"(unspecified)"`` placeholder.
    Ungrounded formulae are candidates for the consumer's oversight, not duties
    to emit. This is a well-formedness predicate, not a routing decision."""
    return (bool((f.raw_sentence or "").strip())
            and f.bearer not in ("", _UNSPECIFIED)
            and f.action not in ("", _UNSPECIFIED))


def detect_conflicts(formulae: list[DeonticFormula]) -> list[dict[str, Any]]:
    """Flag *candidate* normative conflicts within one set of formulae.

    A candidate is the classic SDL clash: the same bearer + unsigned action bound
    to incompatible truth values. Proposition polarity is significant: ``O(a)``
    clashes with ``O(¬a)``, while ``O(¬a)`` and ``F(a)`` agree. This flags; it
    never resolves — a genuine conflict is a candidate for the consumer's
    oversight queue, not something the language decides.
    """
    out: list[dict[str, Any]] = []
    for i in range(len(formulae)):
        for j in range(i + 1, len(formulae)):
            a, b = formulae[i], formulae[j]
            if _norm_key(a.bearer) != _norm_key(b.bearer):
                continue
            if _norm_key(a.action) != _norm_key(b.action):
                continue
            if _formulae_clash(a, b):
                out.append({
                    "kind": "deontic-conflict",
                    "bearer": a.bearer,
                    "action": a.action,
                    "operator_a": a.operator,
                    "operator_b": b.operator,
                    "formula_a": a.render(),
                    "formula_b": b.render(),
                    "resolution": "candidate-escalate",
                    "confidence": round(min(a.confidence, b.confidence), 3),
                })
    return out


def _norm_key(s: str) -> str:
    return " ".join((s or "").lower().split())


def _formulae_clash(a: DeonticFormula, b: DeonticFormula) -> bool:
    """Whether two modalities constrain opposite truth values of one proposition."""
    if a.operator == "P" and b.operator == "P":
        return False
    return _modal_truth(a) != _modal_truth(b)


def _modal_truth(formula: DeonticFormula) -> bool:
    """Truth value required (O/F) or permitted (P) for the unsigned action."""
    truth = not formula.negated
    if formula.operator == "F":
        truth = not truth
    return truth
