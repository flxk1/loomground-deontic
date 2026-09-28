# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Parser and validator for the canonical deontic statement.

Purpose: read a canonical statement string into a :class:`DeonticFormula`
(:func:`parse`), check a formula's well-formedness (:func:`validate`), and
project it to the structured statement shape (:func:`project`). Together these
are the language surface a conformance runner drives (see
:mod:`deontic.protocol`).

The grammar is authoritative in ``artifacts/grammar/deontic.ebnf``; this module
is its executable form. Round-trip holds: ``parse(f.render())`` equals ``f`` on
the structured slots. Language only — parsing and validating a statement is not
reasoning about it. Standard library only.
"""

from __future__ import annotations

import re
from typing import Any

from .formula import DeonticFormula
from .operators import VALID_OPERATORS
from .incidents import INCIDENTS
from .prose_grammar import classify_exception_status

__all__ = ["DeonticSyntaxError", "parse", "validate", "project"]


class DeonticSyntaxError(ValueError):
    """A statement string does not conform to the deontic grammar."""


_COND = re.compile(r"^\s*if\s*\[(?P<cond>.*?)\]\s*then\s+", re.S | re.I)
_EXC = re.compile(r"\s+unless\s*\[(?P<exc>.*?)\]\s*$", re.S | re.I)
_CORE = re.compile(
    r"^\s*(?P<op>[OPF])\s*\(\s*(?P<bearer>[^():]+?)\s*:\s*(?P<action>[^()]+?)\s*\)\s*$",
    re.S,
)


def parse(source: str) -> DeonticFormula:
    """Parse a canonical statement into a :class:`DeonticFormula`.

    Raises :class:`DeonticSyntaxError` on anything the grammar does not accept.
    """
    if not isinstance(source, str) or not source.strip():
        raise DeonticSyntaxError("empty statement")

    rest = source
    condition = ""
    exception = ""

    m = _COND.match(rest)
    if m:
        condition = m.group("cond").strip()
        rest = rest[m.end():]

    m = _EXC.search(rest)
    if m:
        exception = m.group("exc").strip()
        rest = rest[:m.start()]

    m = _CORE.match(rest)
    if not m:
        raise DeonticSyntaxError(f"not a deontic core 'OP(bearer : action)': {rest!r}")

    op = m.group("op")
    bearer = m.group("bearer").strip()
    action = m.group("action").strip()

    negated = False
    if action.startswith("¬"):
        negated = True
        action = action[1:].strip()

    if not bearer:
        raise DeonticSyntaxError("empty bearer")
    if not action:
        raise DeonticSyntaxError("empty action")

    return DeonticFormula(
        operator=op,
        bearer=bearer,
        action=action,
        condition=condition,
        exception=exception,
        exception_status=classify_exception_status(exception),
        negated=negated,
    )


def validate(formula: DeonticFormula) -> dict[str, Any]:
    """Check a formula's well-formedness. Returns ``{"ok": bool, "errors": [...]}``.

    Well-formed means: a catalogued operator, a non-empty bearer and action,
    — when set — an incident drawn from the eight Hohfeld positions, and — when
    set — a ``cross_references`` list of non-empty strings. The optional carry
    fields (``deadline``/``cross_references``/``sanction``) are opaque text; empty,
    they add nothing, so an existing norm validates exactly as before. This is
    structural validation, not a judgment about the norm.
    """
    errors: list[str] = []
    if formula.operator not in VALID_OPERATORS:
        errors.append(f"unknown operator: {formula.operator!r}")
    if not (formula.bearer or "").strip():
        errors.append("empty bearer")
    if not (formula.action or "").strip():
        errors.append("empty action")
    if formula.incident and formula.incident not in INCIDENTS:
        errors.append(f"unknown incident: {formula.incident!r}")
    refs = formula.cross_references
    if refs and (not isinstance(refs, list)
                 or not all(isinstance(r, str) and r.strip() for r in refs)):
        errors.append("cross_references must be a list of non-empty strings")
    return {"ok": not errors, "errors": errors}


def project(formula: DeonticFormula) -> dict[str, Any]:
    """Project a formula to the structured statement shape (statement.schema.json).

    ``exception_status`` is ``formula.exception_status`` when the formula
    already carries one (set by :func:`parse` or a caller of
    :func:`deontic.formula_from_fields` that passed its own classification);
    otherwise it is computed fresh from ``formula.exception`` via
    :func:`deontic.prose_grammar.classify_exception_status` — the same pure
    function :func:`deontic.plane.claim_for` uses for its own coordinate — so
    a :class:`DeonticFormula` built directly (bypassing both) still projects
    a real classification rather than the schema's bare ``''`` default.
    """
    return {
        "operator": formula.operator,
        "bearer": formula.bearer,
        "action": formula.action,
        "condition": formula.condition,
        "exception": formula.exception,
        "exception_status": formula.exception_status or classify_exception_status(formula.exception),
        "negated": formula.negated,
        "incident": formula.incident,
        "counterparty": formula.counterparty,
    }
