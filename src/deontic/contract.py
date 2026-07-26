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
     Each operator declares the reasoning axis its edge carries, as a STRING
     drawn from :data:`SOLVER_DIMENSIONS`. Solver validates a projected edge's
     ``dimension`` by string membership (``SolverProjection.validate``), so the
     string *is* the contract — deontic imports no ``Dimension`` type and builds
     no edge. The consumer maps the string to its own dimension and composes via
     solver's ``COMPOSITION_TABLE``.

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
from .operators import (
    OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION, VALID_OPERATORS,
)
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

# Each operator's primary reasoning axis. An obligation or prohibition is
# *triggered* by its condition (causal); a permission exists *for* a bearer's
# benefit (intentional). This is language — the operator's meaning — expressed as
# a contract string; the consumer builds the typed edge and may override per its
# own domain knowledge.
_OP_AFFINITY: dict[str, str] = {
    OP_OBLIGATION: "causal",
    OP_PROHIBITION: "causal",
    OP_PERMISSION: "intentional",
}


def dimension_affinity(operator: str) -> str:
    """The reasoning-dimension string an operator's edge carries.

    Total over :data:`~deontic.operators.VALID_OPERATORS`; returns ``"relational"``
    (solver's safe floor: "these two things are linked") for anything else. The
    return is always a member of :data:`SOLVER_DIMENSIONS`.
    """
    return _OP_AFFINITY.get(operator, "relational")


@dataclass(frozen=True)
class CompositionPacket:
    """What deontic hands a reasoner for one formula.

    Solver-agnostic and lossless: the ``statement`` is the structured projection
    (statement.schema.json shape); ``dimension`` is the affinity string; the
    ``incident``/``correlative`` name the Hohfeld positions of the addressee and
    counterparty; ``dual`` exposes the operator's defining identity. A consumer
    assembles this into a ``SolverProjection`` pair with a dimensioned edge; the
    edge construction and any dimension override are the consumer's.
    """

    statement: dict[str, Any]
    dimension: str
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
    presents, versioned, so a consumer can negotiate against it."""
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
