# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Neutral protocol implemented by any deontic-language runtime.

Mirrors ``loomground_governance.protocol``: the operations the conformance
runner drives, so any implementation (this package's reference, or a host's own)
can be checked against the published vectors. A runtime parses a statement,
validates its well-formedness, and projects it to the structured shape.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DeonticImplementation(Protocol):
    """Operations required by the deontic conformance runner."""

    def parse(self, source: str) -> Any: ...

    def validate(self, formula: Any) -> dict: ...

    def project(self, formula: Any) -> dict: ...
