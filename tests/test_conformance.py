# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Run the published conformance vectors against the reference implementation.

The reference implementation is the package's own grammar module, which exposes
``parse``/``validate``/``project`` and so satisfies
:class:`deontic.protocol.DeonticImplementation` structurally. A consumer runs
the same vectors against its own runtime.

    python -m pytest tests/test_conformance.py
"""
from __future__ import annotations

import deontic
from deontic import grammar as reference


def test_all_published_vectors_pass():
    report = deontic.run_conformance(reference)
    assert report.ok, report.failures
    assert report.total == report.passed
    assert report.total >= 8


def test_reference_satisfies_protocol():
    assert isinstance(reference, deontic.DeonticImplementation)
