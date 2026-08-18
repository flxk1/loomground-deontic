# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""deontic — the general deontic language and algebra.

The formal vocabulary of norms (the three deontic modals O/P/F and the eight
Hohfeldian incidents), a grammar for a deontic statement, the formula
representation, and the algebra over those terms that lets a reasoner combine
deontic content with governance and any other language. Pure language, no
inference.

A parallel nD language pack, structured like :mod:`loomground_governance` and
consumed *by* solver — it imports no solver, no rule extractor, no reasoning
layer. Public surface, by module:

  * :mod:`.operators` — the three SDL modals (one primitive, two duals) and
    their relations (duality, square, clash).
  * :mod:`.incidents` — the eight Hohfeld positions, their correlative/opposite
    relations, and the deterministic classifiers.
  * :mod:`.formula` — the formula carrier, rendering, groundedness, and
    candidate-conflict flagging.
  * :mod:`.grammar` — parse / validate / project over the canonical statement
    (also the reference implementation of :mod:`.protocol`).
  * :mod:`.algebra` — the carrier, operators, laws, and composition surface.
  * :mod:`.artifacts` — data-only loader for the packaged language artifacts.
  * :mod:`.conformance` — vectors and the acceptance runner.
  * :mod:`.protocol` — the neutral protocol a runtime implements.
"""

from __future__ import annotations

from ._version import __version__

from .operators import (
    OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION, VALID_OPERATORS,
    gloss, name, dual_of, clashes, CLASH_PAIRS,
)
from .incidents import (
    INCIDENTS, correlative, opposite, is_advantage,
    classify_incident, extract_counterparty, classify_condition_kind,
)
from .formula import (
    DeonticFormula, MODAL_TO_OP, formula_from_fields, claim_right,
    is_grounded, detect_conflicts,
)
from .grammar import DeonticSyntaxError, parse, validate, project
from .algebra import (
    contradictory, contrary, correlative_incident, opposite_incident,
    ContraryToDuty, BilateralLiberty, optional, is_optional,
    Composition, compose, system_health,
    law_square_contraries, law_correlativity_involution,
    law_opposite_involution, law_dual_of_prohibition,
    law_optional_reduces_to_two_permissions,
)
from .intervention import (
    INTERVENTION_KINDS, INTERVENTION_POSITIONS,
    classify_intervention_kind, is_intervention,
    intervention_position, intervention_exposure,
)
from .contract import (
    SOLVER_DIMENSIONS, dimension_affinity, CompositionPacket, packet,
    conflict_candidates, incident_vocabulary, contract_surface, CONTRACT_VERSION,
)
from .artifacts import (
    artifact_path, load_json, language_card, language_version, language_status,
    grammar as grammar_text, vocabulary, schema, conformance_manifest, llms,
)
from .conformance import Vector, ConformanceReport, iter_vectors, run_conformance
from .protocol import DeonticImplementation

__all__ = [
    "__version__",
    # operators
    "OP_OBLIGATION", "OP_PERMISSION", "OP_PROHIBITION",
    "VALID_OPERATORS", "gloss", "name", "dual_of", "clashes", "CLASH_PAIRS",
    # incidents
    "INCIDENTS", "correlative", "opposite", "is_advantage",
    "classify_incident", "extract_counterparty", "classify_condition_kind",
    # formula
    "DeonticFormula", "MODAL_TO_OP", "formula_from_fields", "claim_right",
    "is_grounded", "detect_conflicts",
    # grammar
    "DeonticSyntaxError", "parse", "validate", "project",
    # algebra
    "contradictory", "contrary", "correlative_incident", "opposite_incident",
    "ContraryToDuty", "BilateralLiberty", "optional", "is_optional",
    "Composition", "compose", "system_health",
    "law_square_contraries", "law_correlativity_involution",
    "law_opposite_involution", "law_dual_of_prohibition",
    "law_optional_reduces_to_two_permissions",
    # intervention profile (correctability over the existing incidents)
    "INTERVENTION_KINDS", "INTERVENTION_POSITIONS",
    "classify_intervention_kind", "is_intervention",
    "intervention_position", "intervention_exposure",
    # contract (composition surface)
    "SOLVER_DIMENSIONS", "dimension_affinity", "CompositionPacket", "packet",
    "conflict_candidates", "incident_vocabulary", "contract_surface",
    "CONTRACT_VERSION",
    # artifacts
    "artifact_path", "load_json", "language_card", "language_version",
    "language_status", "grammar_text", "vocabulary", "schema",
    "conformance_manifest", "llms",
    # conformance
    "Vector", "ConformanceReport", "iter_vectors", "run_conformance",
    # protocol
    "DeonticImplementation",
]
