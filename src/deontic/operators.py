# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The deontic modal operators — vocabulary and their relations.

Purpose: the three Standard Deontic Logic modalities the language transcribes to,
plus the pure relations over them (duality, the square of opposition, the
operator clash). Language only: these state identities, they do not infer with
them.

There is one primitive and two duals: take obligation (``O``) as primitive, then
``F(a) ≡ O(¬a)`` (forbidden) and ``P(a) ≡ ¬O(¬a)`` (permitted). "Right" is NOT a
fourth modality — it is a Hohfeldian term that reduces to a ``P`` (liberty) for
the holder or to the counterparty's ``O`` (the correlative of a duty); it lives
in :mod:`deontic.incidents`, not here.

Contract: the operator identifiers are stable — they appear in formulae, the
JSON schema, and any audit log. Renaming one is a migration.

The operator→reasoning-dimension projection deliberately does not live here; it
is a consumer's job at its own seam. This module imports nothing but the standard
library.
"""

from __future__ import annotations

__all__ = [
    "OP_OBLIGATION", "OP_PERMISSION", "OP_PROHIBITION",
    "VALID_OPERATORS", "gloss", "name", "dual_of", "clashes", "CLASH_PAIRS",
]

OP_OBLIGATION = "O"    # it is obligatory that …  (the primitive)
OP_PERMISSION = "P"    # it is permitted that …   (P ≡ ¬O¬)
OP_PROHIBITION = "F"   # it is forbidden that …   (F ≡ O¬)

VALID_OPERATORS = (OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION)

_GLOSS: dict[str, str] = {
    OP_OBLIGATION: "obligatory",
    OP_PERMISSION: "permitted",
    OP_PROHIBITION: "forbidden",
}

_NAME: dict[str, str] = {
    OP_OBLIGATION: "obligation",
    OP_PERMISSION: "permission",
    OP_PROHIBITION: "prohibition",
}


def gloss(operator: str) -> str:
    """Human-readable gloss for an operator ('' if unknown)."""
    return _GLOSS.get(operator, "")


def name(operator: str) -> str:
    """Canonical modal name for an operator ('' if unknown)."""
    return _NAME.get(operator, "")


def dual_of(operator: str, action: str, *, negated: bool = False) -> str:
    """The SDL identity that makes an operator's meaning explicit, as a string.

    ``F(a) ≡ O(¬a)`` ; ``P(a) ≡ ¬O(¬a)`` ; ``O(a) ≡ ¬P(¬a)``. Set ``negated``
    when the supplied action denotes ``¬a``; double negation is simplified in the
    returned string. The duality is exposed as readable text, never used to derive.
    Anything outside the three modalities has no deontic dual and returns ``""``.
    """
    complement = action if negated else f"¬ {action}"
    if operator == OP_PROHIBITION:
        return f"O({complement})"
    if operator == OP_PERMISSION:
        return f"¬O({complement})"
    if operator == OP_OBLIGATION:
        return f"¬P({complement})"
    return ""


# Two operators clash when they cannot both hold over the same bearer + action:
# an obligation and a prohibition; a prohibition and a permission (you cannot be
# forbidden and permitted to do the same thing). This flags a candidate
# conflict; it never resolves one.
CLASH_PAIRS = frozenset({
    frozenset((OP_OBLIGATION, OP_PROHIBITION)),
    frozenset((OP_PROHIBITION, OP_PERMISSION)),
})


def clashes(op_a: str, op_b: str) -> bool:
    """True when two operators over the same proposition are in deontic conflict."""
    if op_a == op_b:
        return False
    return frozenset((op_a, op_b)) in CLASH_PAIRS
