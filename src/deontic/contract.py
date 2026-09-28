# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The composition contract — the surface a reasoner uses to combine deontic
content with governance and other algebras.

Purpose: state, in code, exactly what the deontic language *presents* to a
composing reasoner (solver), and in what shape, so solver can carry deontic
content across its nD dimensions alongside another algebra. This is the "algebra
is combinable" promise made concrete.

Deontic presents three things, over three seams solver already has:

  1. **Dimension affinity** (solver's nD edge algebra, ``loomground_solver.dimensions``).
     Round 4 correction: deontic is not causal — the 5D describes what IS; the
     deontic operators (O/P/F) are OUGHT and bind to no 5D dimension. An
     operator is a normative force over a bearer:action pair, not a fact located
     on the 5D manifold; only a norm's *content* (the regulated action/state)
     can be lowered into 5D, and it does so through the factual plane, not
     through the operator. :func:`dimension_affinity` is kept importable for API
     compatibility with callers built against the earlier (reversed) binding; it
     is now total and always returns ``None`` — for O, P, F and for any other
     string. A consumer that needs a dimensioned edge for deontic content
     dimensions the norm's *content* at its own seam (e.g. via the factual
     plane's projection of the regulated action/state), never the operator.

  2. **Incident vocabulary** (solver's norm-theory floor, ``loomground_solver.norm_contract``).
     :func:`incident_vocabulary` is the closed set a consumer injects as
     ``profile.incidents`` so NT-14 validates deontic's incidents rather than the
     solver default (which differs — a consumer must inject this set).

  3. **Conflict candidates** (the same norm-theory floor, NT-6).
     :func:`conflict_candidates` flags same-bearer/same-action operator clashes
     in a shape a consumer turns into a collision edge — flagged, never resolved.

The contract couples to solver by string agreement only; this module imports the
standard library and the deontic language modules, never solver. The dimension
strings mirror ``loomground_solver.dimensions.Dimension`` values and must stay in
sync with them (the same discipline that module keeps with the Federation cell
graph).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from ._version import __version__
from .operators import VALID_OPERATORS
from .incidents import INCIDENTS, correlative
from .formula import DeonticFormula, detect_conflicts
from .grammar import project

__all__ = [
    "SOLVER_DIMENSIONS", "dimension_affinity", "CompositionPacket", "packet",
    "conflict_candidates", "incident_vocabulary", "contract_surface",
    "CONTRACT_VERSION",
]

# The version of the composition surface itself, distinct from the package
# version — a consumer negotiates against this.
CONTRACT_VERSION = "0.1.0"

# The reasoning-dimension strings a projected edge may carry. These mirror
# loomground_solver.dimensions.Dimension's string values; the agreement is by
# string, not by import. Keep in sync with solver (and its Federation-cell
# alignment) — a value not in solver's enum fails SolverProjection.validate.
SOLVER_DIMENSIONS = (
    "structural", "causal", "intentional", "temporal", "relational",
)

# Round 4 (deontic-is-ought correction, D1 reversed): an operator (O/P/F) is a
# deontic modality — an OUGHT — not a fact, so it binds to no 5D dimension. The
# earlier operator->dimension map (``extraction.json`` -> ``operator_axis``) is
# retired; deontic publishes no operator->dimension binding anywhere (see
# ``deontic.plane.binding``, which is now always ``{}``, and
# ``tests/test_plane.py``/``tools/check_extraction.py`` Gate B, which guard that
# no operator carries a 5D dimension). A norm's *content* enters 5D only through
# the factual plane's own lowering of the regulated action/state — never through
# the operator.
def dimension_affinity(operator: str) -> str | None:
    """The reasoning-dimension string an operator's edge carries: always ``None``.

    Total over :data:`~deontic.operators.VALID_OPERATORS` and over any other
    string. Ought carries no 5D dimension: O, P, and F are normative modalities,
    not facts located on the 5D manifold, so this function never names a
    dimension for any operator. A norm's content (the regulated action/state) is
    what a consumer lowers into 5D — through the factual plane at its own seam —
    and that lowering is what may then carry a dimension, never the operator
    itself. Kept importable, returning ``None``, for API compatibility with
    callers built against the earlier (reversed) binding.
    """
    return None


@dataclass(frozen=True)
class CompositionPacket:
    """What deontic hands a reasoner for one formula.

    Solver-agnostic and lossless: the ``statement`` is the structured projection
    (statement.schema.json shape); ``dimension`` is always ``None`` (ought carries
    no 5D dimension — see :func:`dimension_affinity`); the ``incident``/
    ``correlative`` name the Hohfeld positions of the addressee and counterparty;
    ``dual`` exposes the operator's defining identity. A consumer that needs a
    dimensioned edge dimensions the norm's *content* at its own seam (e.g. via
    the factual plane), not this packet's ``dimension`` field; the edge
    construction and any dimensioning are the consumer's.
    """

    statement: dict[str, Any]
    dimension: str | None
    incident: str
    correlative: str
    dual: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def packet(formula: DeonticFormula) -> CompositionPacket:
    """Build the composition packet for one formula."""
    return CompositionPacket(
        statement=project(formula),
        dimension=dimension_affinity(formula.operator),
        incident=formula.incident,
        correlative=correlative(formula.incident) if formula.incident else "",
        dual=formula.dual(),
    )


def conflict_candidates(formulae: list[DeonticFormula]) -> list[dict[str, Any]]:
    """Candidate conflicts across a set of formulae, in a collision-edge shape.

    A thin projection of :func:`deontic.formula.detect_conflicts` that names the
    edge predicate a consumer's norm-theory floor recognises for a collision
    (``may-conflict-with``). ``resolution`` stays ``candidate-escalate``: deontic
    flags a candidate; the consumer decides whether it is a genuine collision to
    escalate (and, in solver's norm_contract, records it as such). Never resolved
    here.
    """
    out: list[dict[str, Any]] = []
    for c in detect_conflicts(formulae):
        edge = dict(c)
        edge["predicate"] = "may-conflict-with"
        out.append(edge)
    return out


def incident_vocabulary() -> tuple[str, ...]:
    """The closed incident vocabulary a consumer injects into its norm-theory
    floor (e.g. ``profile.incidents`` for solver's NT-14)."""
    return INCIDENTS


def contract_surface() -> dict[str, Any]:
    """A self-describing summary of the composition surface — what deontic
    presents, versioned, so a consumer can negotiate against it.

    ``operator_dimension_affinity`` maps every operator to ``None``: ought
    carries no 5D dimension (see :func:`dimension_affinity`). ``dimensions``
    stays published as the vocabulary a *content* projection may draw on.
    """
    return {
        "contract_version": CONTRACT_VERSION,
        "language_version": __version__,
        "operators": list(VALID_OPERATORS),
        "dimensions": list(SOLVER_DIMENSIONS),
        "operator_dimension_affinity": {op: dimension_affinity(op) for op in VALID_OPERATORS},
        "incidents": list(INCIDENTS),
        "conflict_predicate": "may-conflict-with",
        "conflict_resolution": "candidate-escalate",
        "packet_fields": ["statement", "dimension", "incident", "correlative", "dual"],
    }
