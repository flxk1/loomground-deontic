# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The deontic plane descriptor (shared plane descriptor contract v1).

Registered under the entry-point group ``loomground.planes`` as ``deontic``. The
zero-argument :func:`plane` returns, as plain data plus one pure function:

  * ``plane`` — ``"deontic"``;
  * ``language_version`` — the language version from the packaged language card;
  * ``nd_system`` — the published nD-system document (``artifacts/nd-system.json``),
    whose ``version`` equals ``language_version``;
  * ``binding`` — relation → 5D dimension, read from exactly one package data file
    (``artifacts/extraction.json`` → ``operator_axis``: O → causal,
    P → intentional, F → causal); a claim's ``relation`` is its operator;
  * ``produce`` — :func:`produce`, pure and deterministic;
  * ``examples`` — the published conformance vectors (formal statements) and the
    published prose vectors (``artifacts/conformance/prose.json``), each with the
    claims the plane must produce for it.

The package never imports a consumer: the descriptor is data a store (the versum)
reads through the entry point. Standard library only.
"""
from __future__ import annotations

import copy
import re
from typing import Any

from .artifacts import artifact_path, language_version, load_json
from .formula import DeonticFormula
from .grammar import DeonticSyntaxError, parse, project
from . import prose

__all__ = ["PLANE_ID", "plane", "produce", "nd_system", "binding", "examples",
           "claim_for", "METHOD_PARSE", "METHOD_PROSE"]

PLANE_ID = "deontic"
METHOD_PARSE = "deontic-parse"
METHOD_PROSE = "deontic-prose-cues"

# statement field -> (nD axis, form slot); the axes and slots are those of nd-system.json
_FIELDS = (
    ("operator", "statement.operator"),
    ("bearer", "statement.bearer"),
    ("action", "statement.action"),
    ("condition", "statement.condition"),
    ("exception", "statement.exception"),
    ("incident", "statement.incident"),
    ("counterparty", "statement.counterparty"),
)
# A formal statement opens with a bracketed condition or an operator core.
_FORMAL = re.compile(r"^\s*(?:if\s*\[|[OPF]\s*\()", re.I)


def nd_system() -> dict:
    """The published deontic nD-system document (a fresh copy)."""
    return load_json("nd-system.json")


def binding() -> dict[str, str]:
    """The plane's relation → 5D binding, from its one data file."""
    return {str(k): str(v) for k, v in load_json("extraction.json")["operator_axis"].items()}


def claim_for(sentence: str, statement: dict[str, Any], method: str) -> dict[str, Any]:
    """The contract-v1 claim for one projected statement over the whole sentence.

    ``statement`` is the language's own output (:func:`deontic.grammar.project`);
    it is carried unchanged under ``statement`` so a consumer can read it back
    field for field. Coordinates are its non-empty fields (plus ``negated``); each
    non-empty field is bound to its form slot.
    """
    coords: dict[str, Any] = {}
    slots: dict[str, str] = {}
    for field, slot in _FIELDS:
        value = statement.get(field, "")
        if value:
            coords[field] = value
            slots[slot] = field
    coords["negated"] = bool(statement.get("negated", False))
    return {
        "relation": statement["operator"],
        "span": [0, len(sentence)],
        "coordinates": coords,
        "slots": slots,
        "method": method,
        "statement": dict(statement),
    }


def _formulae(sentence: str) -> tuple[list[DeonticFormula], str]:
    if _FORMAL.match(sentence):
        try:
            return [parse(sentence)], METHOD_PARSE
        except DeonticSyntaxError:
            return [], METHOD_PARSE
    return prose.extract(sentence), METHOD_PROSE


def produce(sentence: str, context: dict | None = None) -> list[dict]:
    """The deontic claims one sentence states; ``[]`` when it states none.

    A formal statement (``OP(bearer : action)``, optionally ``if [..] then`` /
    ``unless [..]``) is read by :func:`deontic.parse`, unchanged; anything else is
    read as English prose by :func:`deontic.prose.extract`. ``context`` is
    accepted for the contract and not used. Pure and deterministic.
    """
    if not isinstance(sentence, str) or not sentence.strip():
        return []
    formulae, method = _formulae(sentence)
    return [claim_for(sentence, project(f), method) for f in formulae]


def examples() -> list[dict]:
    """The plane's published examples with the claims it must produce for them.

    Built from the published vectors' own expected outputs (never from
    :func:`produce`), so a round-trip through ``produce`` is a real check.
    """
    out: list[dict] = []
    for vec in load_json("conformance", "manifest.json")["vectors"]:
        if vec.get("kind") != "statement":
            continue
        base = artifact_path("conformance", "vectors", vec["name"])
        sentence = base.joinpath("input.deo").read_text(encoding="utf-8").strip()
        expected = load_json("conformance", "vectors", vec["name"], "expected.json")
        out.append({"name": vec["name"], "sentence": sentence,
                    "expected": [claim_for(sentence, expected, METHOD_PARSE)]})
    for vec in load_json("conformance", "prose.json")["vectors"]:
        sentence = vec["sentence"]
        out.append({"name": vec["name"], "sentence": sentence,
                    "expected": [claim_for(sentence, st, METHOD_PROSE)
                                 for st in vec["expected"]]})
    return out


def plane() -> dict:
    """The deontic plane descriptor (contract v1)."""
    return {
        "plane": PLANE_ID,
        "language_version": language_version(),
        "nd_system": nd_system(),
        "binding": binding(),
        "produce": produce,
        "examples": copy.deepcopy(examples()),
    }
