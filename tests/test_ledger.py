# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The append-only abstention ledger: opened in 'a' mode only, a second run
appends rather than truncates, and accepted + abstained == input for a batch.

    python -m pytest tests/test_ledger.py
"""
from __future__ import annotations

import json

from deontic import ledger


SENTENCES = [
    "The lender shall never disclose the data.",           # accepted
    "The lender may disclose the data.",                   # accepted
    "The controller processes data.",                      # abstained: NO_MODAL
    "It must be noted that the report is late.",            # abstained: AMBIGUOUS_SUBJECT
    "The processor shall not disclose the data, unless required by law.",  # accepted,
                                                             # exception unresolved
]


def test_run_batch_tally_satisfies_the_accept_plus_abstain_invariant(tmp_path):
    path = tmp_path / "ledger.jsonl"
    tally = ledger.run_batch(SENTENCES, path)
    assert tally["input"] == len(SENTENCES)
    assert ledger.check_invariant(tally)
    assert tally["accepted"] + tally["abstained"] == tally["input"]


def test_invariant_check_fails_on_a_mismatched_tally():
    assert ledger.check_invariant({"input": 5, "accepted": 3, "abstained": 1}) is False


def test_ledger_is_opened_append_only_a_second_run_appends_not_truncates(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger.run_batch(SENTENCES[:2], path)
    first_records = ledger.read_records(path)
    assert len(first_records) == 2

    ledger.run_batch(SENTENCES[2:], path)
    second_records = ledger.read_records(path)
    assert len(second_records) == 5
    # the first two records are untouched — the file was never truncated
    assert second_records[:2] == first_records


def test_append_record_uses_open_mode_a_only(tmp_path, monkeypatch):
    seen_modes = []
    real_open = open

    def _spy_open(file, mode="r", *args, **kwargs):
        if str(file).endswith("ledger.jsonl"):
            seen_modes.append(mode)
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _spy_open)
    path = tmp_path / "ledger.jsonl"
    ledger.append_record(path, {"sentence": "x", "accepted": True})
    ledger.append_record(path, {"sentence": "y", "accepted": False, "reason": "NO_MODAL"})
    assert seen_modes == ["a", "a"]


def test_field_abstention_for_unresolved_exception_is_recorded_without_abstaining_sentence(tmp_path):
    path = tmp_path / "ledger.jsonl"
    tally = ledger.run_batch(
        ["The processor shall not disclose the data, unless required by law."], path)
    assert tally == {"input": 1, "accepted": 1, "abstained": 0}
    (record,) = ledger.read_records(path)
    assert record["accepted"] is True
    assert record["field_abstentions"] == [
        {"field": "exception", "reason": "EXCEPTION_EXTERNAL_UNRESOLVED"}
    ]
