# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""deontic.plane.read_polarity: the typed reader that returns operator AND
exception_status together, so a consumer can never read a norm's polarity
without also seeing whether it carries an unresolved exception.

    python -m pytest tests/test_typed_polarity_reader.py
"""
from __future__ import annotations

import dataclasses

import deontic
from deontic import plane as dplane
from deontic import prose_grammar


def test_read_polarity_returns_operator_and_exception_status_together():
    (claim,) = dplane.produce("The lender shall never disclose the data.")
    pv = deontic.read_polarity(claim)
    assert isinstance(pv, dplane.PolarityView)
    assert pv.operator == "F"
    assert pv.exception_status == prose_grammar.NONE_DETECTED
    # a value object: both fields travel together, always
    fields = {f.name for f in dataclasses.fields(pv)}
    assert fields == {"operator", "exception_status"}


def test_read_polarity_surfaces_an_unresolved_exception_alongside_the_operator():
    (claim,) = dplane.produce(
        "The processor shall not disclose the data, unless required by law.")
    pv = deontic.read_polarity(claim)
    assert pv.operator == "F"
    assert pv.exception_status == prose_grammar.EXCEPTION_EXTERNAL_UNRESOLVED
    assert pv.exception_status != prose_grammar.NONE_DETECTED


def test_no_claim_this_plane_builds_is_missing_its_exception_status_coordinate():
    for sentence in (
        "The lender shall never disclose the data.",
        "The processor shall not disclose the data to any third party, save as permitted.",
        "if [processing is carried out] then O(controller : implement TOMs) unless [Art.11]",
    ):
        for claim in dplane.produce(sentence):
            assert "exception_status" in claim["coordinates"]
            pv = deontic.read_polarity(claim)
            assert pv.exception_status in prose_grammar.EXCEPTION_STATUSES
