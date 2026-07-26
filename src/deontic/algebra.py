# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The deontic algebra — carrier, operators, laws, and the composition surface.

Purpose: the part that makes deontic *combinable*. It names, explicitly and
testably:

  * the **carrier** — deontic formulae over a proposition (:mod:`deontic.formula`)
    and the eight Hohfeld incidents (:mod:`deontic.incidents`);
  * the **operators** — duality/negation, conjunction and disjunction of norms,
    the contrary-to-duty conditional, and the incident correlative/opposite;
  * the **laws** — the identities and orderings (the deontic square, F≡O¬,
    correlativity, opposite-involution) as predicates a property test drives;
  * the **composition surface** — :func:`compose`, the shape a reasoner (solver)
    uses to carry deontic content alongside another algebra.

Deterministic and pure — the algebra is language, not inference. Standard
library only.

Scope note: the operators and law predicates are complete here; the *formal*
composition contract a reasoner consumes lives in :mod:`deontic.contract`, and
the exact ``SolverProjection`` mapping is co-designed with solver before it is
frozen. The :func:`compose` surface below is the provisional shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .operators import (
    OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION, clashes,
)
from .formula import DeonticFormula, detect_conflicts
from .incidents import correlative, opposite, INCIDENTS

__all__ = [
    "contradictory", "contrary", "correlative_incident", "opposite_incident",
    "ContraryToDuty", "BilateralLiberty", "optional", "is_optional",
    "Composition", "compose", "system_health",
    "law_square_contraries", "law_correlativity_involution",
    "law_opposite_involution", "law_dual_of_prohibition",
    "law_optional_reduces_to_two_permissions",
]


# --- operators over the modal carrier ---------------------------------------

# The square of opposition, as operator maps over a fixed proposition a.
# Contradictory: exactly one of the pair holds. O(a) contradicts P(¬a);
# F(a) contradicts P(a). We express the operator side; the ¬ on the
# proposition is carried by the returned ``negate_proposition`` flag.
_CONTRADICTORY: dict[str, tuple[str, bool]] = {
    OP_OBLIGATION: (OP_PERMISSION, True),    # O(a)  ⟷ ¬  P(¬a)
    OP_PROHIBITION: (OP_PERMISSION, False),  # F(a)  ⟷ ¬  P(a)
    OP_PERMISSION: (OP_OBLIGATION, True),    # P(a)  ⟷ ¬  O(¬a)
}


def contradictory(operator: str) -> tuple[str, bool]:
    """The operator (and whether its proposition is negated) that contradicts
    ``operator`` over the same base proposition. Returns ``("", False)`` for
    anything outside the three modalities (which has no deontic contradictory)."""
    return _CONTRADICTORY.get(operator, ("", False))


def contrary(op_a: str, op_b: str) -> bool:
    """True when two operators are contraries over the same proposition — they
    cannot both hold (O and F). Distinct from :func:`deontic.operators.clashes`,
    which also covers the F/P and F/R exclusions."""
    return {op_a, op_b} == {OP_OBLIGATION, OP_PROHIBITION}


def correlative_incident(incident: str) -> str:
    """The counterparty's jural correlative of an incident."""
    return correlative(incident)


def opposite_incident(incident: str) -> str:
    """The jural opposite of an incident for the same party."""
    return opposite(incident)


# --- the contrary-to-duty conditional ---------------------------------------

@dataclass(frozen=True)
class ContraryToDuty:
    """A primary norm paired with the norm that applies when it is violated.

    The classic CTD structure: ``primary`` is what ought to hold; ``secondary``
    is what ought to hold *given* the primary is breached (e.g. O(not harm) with
    O(compensate) under ¬(not harm)). Represented, not resolved — SDL's CTD
    paradoxes are exactly why the language transcribes the pairing and leaves
    inference to a consumer.
    """

    primary: DeonticFormula
    secondary: DeonticFormula

    def render(self) -> str:
        return f"{self.primary.render()}  ; on-violation: {self.secondary.render()}"


# --- bilateral liberty (the optional / facultative / indifferent) -----------

@dataclass(frozen=True)
class BilateralLiberty:
    """A two-way liberty over an action — the deontic *optional*.

    Hohfeld's privilege is *unilateral*: ``P(a)`` alone ("no duty to the
    contrary"), and it survives even under ``O(a)`` (``O(a) → P(a)`` by
    subalternation). A **bilateral** liberty is ``P(a) ∧ P(¬a)`` — free to do
    *and* free to refrain — the genuine "optional / facultative / indifferent".

    It is not a fourth modality: it reduces to a conjunction of two permissions
    (:meth:`permissions`). By the square it is inconsistent with any obligation
    or prohibition on the same action (:meth:`excludes`) — stated as an
    identity, not derived: ``O(a) ≡ ¬P(¬a)`` negates the second conjunct and
    ``F(a) ≡ ¬P(a)`` negates the first.
    """

    bearer: str
    action: str
    language: str = "en"

    def permissions(self) -> tuple[DeonticFormula, DeonticFormula]:
        """The two permissions the liberty conjoins: ``P(a)`` and ``P(¬a)``."""
        do = DeonticFormula(operator=OP_PERMISSION, bearer=self.bearer,
                            action=self.action, negated=False, language=self.language)
        refrain = DeonticFormula(operator=OP_PERMISSION, bearer=self.bearer,
                                 action=self.action, negated=True, language=self.language)
        return (do, refrain)

    def excludes(self) -> tuple[str, str]:
        """The two cores a bilateral liberty is inconsistent with, rendered:
        an obligation and a prohibition on the same action. Stated, not derived."""
        return (
            DeonticFormula(operator=OP_OBLIGATION, bearer=self.bearer, action=self.action).core(),
            DeonticFormula(operator=OP_PROHIBITION, bearer=self.bearer, action=self.action).core(),
        )

    def render(self) -> str:
        do, refrain = self.permissions()
        return f"{do.core()} ∧ {refrain.core()}"


def optional(bearer: str, action: str, *, language: str = "en") -> BilateralLiberty:
    """Construct the bilateral liberty (optional) over ``action`` for ``bearer``."""
    return BilateralLiberty(bearer=bearer, action=action, language=language)


def is_optional(formulae: list[DeonticFormula], bearer: str, action: str) -> bool:
    """True when a set of formulae grants both the permission to do ``action``
    and the permission to refrain, for ``bearer`` — i.e. it expresses a
    bilateral liberty. Detects presence; it does not infer one from an absence."""
    key_b, key_a = _key(bearer), _key(action)
    has_do = has_refrain = False
    for f in formulae:
        if f.operator != OP_PERMISSION:
            continue
        if _key(f.bearer) != key_b or _key(f.action) != key_a:
            continue
        if f.negated:
            has_refrain = True
        else:
            has_do = True
    return has_do and has_refrain


def _key(s: str) -> str:
    return " ".join((s or "").lower().split())


# --- composition surface (provisional; hardened with solver in step 3) ------

@dataclass
class Composition:
    """The result of combining deontic content, in the shape a reasoner reads.

    ``formulae`` is the merged carrier; ``conflicts`` are the flagged candidate
    clashes (never resolved here). ``foreign`` carries opaque content from
    another algebra combined alongside deontic, untouched — the seam where
    solver composes deontic with governance and others.
    """

    formulae: list[DeonticFormula] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    foreign: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "formulae": [f.to_dict() for f in self.formulae],
            "conflicts": self.conflicts,
            "foreign": list(self.foreign),
        }


def compose(*parts: Any) -> Composition:
    """Combine deontic formulae (and opaque foreign content) into one carrier.

    Each part is either a :class:`DeonticFormula`, an iterable of them, or
    foreign content from another algebra (carried through untouched). Candidate
    conflicts across the merged deontic formulae are flagged, not resolved.
    """
    formulae: list[DeonticFormula] = []
    foreign: list[Any] = []
    for part in parts:
        if isinstance(part, DeonticFormula):
            formulae.append(part)
        else:
            materialized = _formulae_from_iterable(part)
            if materialized is None:
                foreign.append(part)
            else:
                formulae.extend(materialized)
    return Composition(
        formulae=formulae,
        conflicts=detect_conflicts(formulae),
        foreign=foreign,
    )


# --- systemic health (the utopia/dystopia diagnostic) -----------------------

def system_health(formulae: list[DeonticFormula]) -> dict[str, Any]:
    """Diagnose the *structural* health of a whole norm-set — the utopia/dystopia
    axis, read off the deontic and Hohfeld structure. It FLAGS pathologies; it
    never renders a verdict (whether a system is good is an evaluative and human
    call, not a deontic one).

    The three structural pathologies:

      * ``normative-collapse`` — a candidate conflict exists (``O(a) ∧ F(a)``):
        the ideal-worlds set is locally empty, the ``ought-implies-can`` /
        seriality (SDL ``D``) floor is breached.
      * ``liberty-absent`` — the set has norms but no permission or privilege:
        every action is duty or prohibition, no liberty survives (a totalitarian
        structure — no bilateral liberty is even possible).
      * ``immunity-absent`` — a power is present with no immunity: a capacity to
        change others' positions with nothing protecting against it (unchecked
        power — rights-as-side-constraints missing).

    ``liberties`` lists the (bearer, action) pairs that are genuine bilateral
    liberties (:func:`is_optional`). A set with no pathologies and standing
    liberties/immunities is structurally healthy; a human still judges its worth.
    """
    conflicts = detect_conflicts(formulae)

    liberties: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for f in formulae:
        k = (_key(f.bearer), _key(f.action))
        if k in seen:
            continue
        if is_optional(formulae, f.bearer, f.action):
            seen.add(k)
            liberties.append({"bearer": f.bearer, "action": f.action})

    privileges_present = any(
        f.operator == OP_PERMISSION or f.incident == "privilege"
        for f in formulae)
    immunities_present = any(f.incident == "immunity" for f in formulae)
    powers_present = any(f.incident == "power" for f in formulae)

    pathologies: list[str] = []
    if conflicts:
        pathologies.append("normative-collapse")
    if formulae and not privileges_present:
        pathologies.append("liberty-absent")
    if powers_present and not immunities_present:
        pathologies.append("immunity-absent")

    return {
        "conflict_free": not conflicts,
        "liberties": liberties,
        "privileges_present": privileges_present,
        "immunities_present": immunities_present,
        "powers_present": powers_present,
        "pathologies": pathologies,
        "healthy": not pathologies,
    }


def _formulae_from_iterable(x: Any) -> list[DeonticFormula] | None:
    if isinstance(x, (str, bytes, bytearray, Mapping)):
        return None
    try:
        items = list(x)
    except TypeError:
        return None
    if all(isinstance(i, DeonticFormula) for i in items):
        return items
    return None


# --- laws (predicates a property test drives over all inputs) ---------------
# Each returns True when the law holds for the given arguments; the step-3
# property suite asserts them across the whole carrier.

def law_square_contraries(op_a: str, op_b: str) -> bool:
    """Contraries clash: if two operators are contraries they cannot both hold."""
    if contrary(op_a, op_b):
        return clashes(op_a, op_b)
    return True


def law_correlativity_involution(incident: str) -> bool:
    """A correlative's correlative is the original incident (the pairing is an
    involution): correlative(correlative(x)) == x for every incident."""
    return correlative(correlative(incident)) == incident


def law_opposite_involution(incident: str) -> bool:
    """An opposite's opposite is the original incident."""
    return opposite(opposite(incident)) == incident


def law_dual_of_prohibition(action: str) -> bool:
    """F(a) is exposed as O(¬a): the prohibition's dual names an obligation over
    the negated action."""
    f = DeonticFormula(operator=OP_PROHIBITION, bearer="x", action=action)
    return f.dual() == f"O(¬ {action})"


def law_optional_reduces_to_two_permissions(action: str) -> bool:
    """A bilateral liberty is not primitive: it is exactly ``P(a) ∧ P(¬a)`` — two
    permissions over the same action, one to do and one to refrain."""
    do, refrain = optional("x", action).permissions()
    return (do.operator == OP_PERMISSION and refrain.operator == OP_PERMISSION
            and do.negated is False and refrain.negated is True
            and do.action == action and refrain.action == action)
