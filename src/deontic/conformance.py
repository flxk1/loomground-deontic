# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Implementation-neutral access to and execution of conformance vectors.

Mirrors ``loomground_governance.conformance``. A vector pairs an example deontic
statement with its expected outcome; running the published vectors against an
implementation is the acceptance gate for any consumer.

Vector kinds (declared in the manifest):

  * ``statement`` — ``input.deo`` parses and validates, and its projection
    equals ``expected.json``.
  * ``negative`` — ``input.deo`` is rejected; ``reject.json`` says at which
    ``stage`` (``parse`` or ``validate``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .artifacts import artifact_path, conformance_manifest
from .protocol import DeonticImplementation

__all__ = ["Vector", "ConformanceReport", "iter_vectors", "run_conformance"]


@dataclass(frozen=True)
class Vector:
    name: str
    kind: str
    files: tuple[str, ...]
    stage: str = ""

    def text(self, filename: str) -> str:
        return artifact_path("conformance", "vectors", self.name, filename).read_text(
            encoding="utf-8")

    def json(self, filename: str) -> Any:
        import json
        return json.loads(self.text(filename))


@dataclass(frozen=True)
class ConformanceReport:
    total: int
    passed: int
    failures: tuple[dict, ...]

    @property
    def ok(self) -> bool:
        return not self.failures


def iter_vectors() -> Iterable[Vector]:
    for item in conformance_manifest()["vectors"]:
        yield Vector(item["name"], item["kind"], tuple(item["files"]),
                     str(item.get("stage", "")))


def _check(implementation: DeonticImplementation, vector: Vector) -> None:
    source = vector.text("input.deo")

    if vector.kind == "negative":
        try:
            formula = implementation.parse(source)
        except Exception:
            if vector.stage == "parse":
                return
            raise AssertionError("rejected at parse instead of validate")
        report = implementation.validate(formula)
        if vector.stage != "validate" or report.get("ok", True):
            raise AssertionError(f"expected {vector.stage} rejection")
        return

    formula = implementation.parse(source)
    report = implementation.validate(formula)
    if not report.get("ok"):
        raise AssertionError(f"unexpected validate rejection: {report.get('errors', [])}")
    if implementation.project(formula) != vector.json("expected.json"):
        raise AssertionError("statement projection mismatch")


def run_conformance(implementation: DeonticImplementation) -> ConformanceReport:
    """Run every published vector against an implementation object or module."""
    vectors = tuple(iter_vectors())
    failures = []
    for vector in vectors:
        try:
            _check(implementation, vector)
        except Exception as exc:
            failures.append({"name": vector.name, "kind": vector.kind,
                             "error": f"{type(exc).__name__}: {exc}"})
    return ConformanceReport(len(vectors), len(vectors) - len(failures), tuple(failures))
