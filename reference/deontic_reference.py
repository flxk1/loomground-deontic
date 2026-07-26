# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""An independent reference implementation of the deontic language surface.

This module implements the conformance protocol (`parse` / `validate` / `project`)
from the *published* artifacts alone — the grammar (`deontic.ebnf`), the JSON
schema (`statement.schema.json`), and the conformance vectors. It imports no
product package (`deontic`, solver, …); an import-isolation gate
(`tools/check_reference_isolation.py`) enforces that. Its purpose is to prove the
contract is implementable by a third party, so a consumer can trust the vectors
define conformance rather than an implementation.

Standard library only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# The published artifact tree (data files, loaded by path — not an import).
_ARTIFACTS = Path(__file__).resolve().parent.parent / "src" / "deontic" / "artifacts"


def _schema() -> dict:
    return json.loads((_ARTIFACTS / "schema" / "statement.schema.json").read_text(encoding="utf-8"))


_SCHEMA = _schema()
_OPERATORS = tuple(_SCHEMA["properties"]["operator"]["enum"])          # ("O","P","F")
_INCIDENTS = tuple(_SCHEMA["properties"]["incident"]["enum"])          # 8 + ""
_REQUIRED = tuple(_SCHEMA["required"])                                 # operator, bearer, action

# The canonical statement grammar (deontic.ebnf), implemented independently.
_COND = re.compile(r"^\s*if\s*\[(?P<cond>.*?)\]\s*then\s+", re.S | re.I)
_EXC = re.compile(r"\s+unless\s*\[(?P<exc>.*?)\]\s*$", re.S | re.I)
_CORE = re.compile(
    r"^\s*(?P<op>[A-Za-z]+)\s*\(\s*(?P<bearer>[^():]+?)\s*:\s*(?P<action>[^()]+?)\s*\)\s*$",
    re.S,
)


class DeonticSyntaxError(ValueError):
    """A statement string does not conform to the deontic grammar."""


def parse(source: str) -> dict[str, Any]:
    """Parse a canonical statement into a structured formula dict."""
    if not isinstance(source, str) or not source.strip():
        raise DeonticSyntaxError("empty statement")
    rest, condition, exception = source, "", ""

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
    if op not in _OPERATORS:
        raise DeonticSyntaxError(f"unknown operator {op!r} (not in {_OPERATORS})")

    bearer = m.group("bearer").strip()
    action = m.group("action").strip()
    negated = action.startswith("¬")
    if negated:
        action = action[1:].strip()
    if not bearer:
        raise DeonticSyntaxError("empty bearer")
    if not action:
        raise DeonticSyntaxError("empty action")

    return {
        "operator": op, "bearer": bearer, "action": action,
        "condition": condition, "exception": exception, "negated": negated,
        "incident": "", "counterparty": "",
    }


def validate(formula: dict[str, Any]) -> dict[str, Any]:
    """Check well-formedness against the published schema."""
    errors: list[str] = []
    if formula.get("operator") not in _OPERATORS:
        errors.append(f"unknown operator: {formula.get('operator')!r}")
    for field in _REQUIRED:
        if not str(formula.get(field, "")).strip():
            errors.append(f"empty {field}")
    if formula.get("incident") and formula["incident"] not in _INCIDENTS:
        errors.append(f"unknown incident: {formula['incident']!r}")
    return {"ok": not errors, "errors": errors}


def project(formula: dict[str, Any]) -> dict[str, Any]:
    """Project to the structured statement shape (statement.schema.json)."""
    return {
        "operator": formula["operator"],
        "bearer": formula["bearer"],
        "action": formula["action"],
        "condition": formula.get("condition", ""),
        "exception": formula.get("exception", ""),
        "negated": bool(formula.get("negated", False)),
        "incident": formula.get("incident", ""),
        "counterparty": formula.get("counterparty", ""),
    }
