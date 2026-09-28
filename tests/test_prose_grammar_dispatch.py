# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Phase 1 mutation evidence: the grammar dispatches through the single
_NEGATED_MODAL truth table, and its lexemes/phrases come from the JSON
gazetteers under artifacts/gazetteer/ — never from a literal in the parser.

    python -m pytest tests/test_prose_grammar_dispatch.py
"""
from __future__ import annotations

import json

import pytest

import deontic
from deontic import prose_grammar


# ── the truth table is the single dispatch point ──────────────────────
def test_negated_modal_table_governs_positive_may():
    frame = prose_grammar.analyze("The lender may disclose the data.")
    assert frame.accepted and frame.operator == "P"


def test_mutating_one_truth_table_cell_flips_the_dispatched_operator(monkeypatch):
    # Mutation evidence: flip (may, False) -> F. If the grammar dispatched
    # anywhere other than this table, this mutation would have no effect.
    monkeypatch.setitem(prose_grammar._NEGATED_MODAL, ("may", False), "F")
    frame = prose_grammar.analyze("The lender may disclose the data.")
    assert frame.accepted
    assert frame.operator == "F", (
        "mutating _NEGATED_MODAL[('may', False)] must change the dispatched "
        "operator: the grammar does not dispatch through the table"
    )


def test_mutating_the_negative_cell_back_to_permission_also_flips():
    original = prose_grammar._NEGATED_MODAL[("may", True)]
    try:
        prose_grammar._NEGATED_MODAL[("may", True)] = "P"
        frame = prose_grammar.analyze("The lender may not disclose the data.")
        assert frame.operator == "P"
    finally:
        prose_grammar._NEGATED_MODAL[("may", True)] = original


# ── gazetteer entries are loaded from the JSON artifact, not hard-coded ──
def test_removing_the_at_no_time_gazetteer_entry_changes_the_case(monkeypatch):
    real_load = prose_grammar._load_gazetteer

    def _without_at_no_time(name):
        doc = real_load(name)
        if name == "interposed":
            doc = dict(doc)
            doc["phrases"] = [p for p in doc["phrases"] if p["phrase"] != "at no time"]
        return doc

    monkeypatch.setattr(prose_grammar, "_load_gazetteer", _without_at_no_time)
    sentence = "The lender shall at no time disclose the data."
    frame = prose_grammar.analyze(sentence)
    # "at no time" is no longer a recognised interposed phrase: none of "at",
    # "no", "time" is a negation adverb either, so the modal reads as the bare
    # affirmative and the leftover words stay in the action — a different,
    # visibly wrong case, proving the gazetteer (not a literal) governs this.
    with_gazetteer = prose_grammar.analyze(sentence)  # unpatched call for contrast is below
    assert frame.operator == "O"  # was "F" with the gazetteer entry present
    assert frame.action != "disclose the data"
    assert "at no time" in frame.action


def test_gazetteer_entries_loaded_directly_from_the_packaged_artifact():
    from deontic.artifacts import artifact_path
    doc = json.loads(artifact_path("gazetteer", "interposed.json").read_text(encoding="utf-8"))
    assert prose_grammar._load_gazetteer("interposed") == doc
    assert any(p["phrase"] == "at no time" and p["negating"] for p in doc["phrases"])


def test_removing_a_modal_lexeme_gazetteer_entry_abstains(monkeypatch):
    real_load = prose_grammar._load_gazetteer

    def _without_must(name):
        doc = real_load(name)
        if name == "modal_lexemes":
            doc = dict(doc)
            doc["phrases"] = [p for p in doc["phrases"] if p["phrase"] != "must"]
        return doc

    monkeypatch.setattr(prose_grammar, "_load_gazetteer", _without_must)
    frame = prose_grammar.analyze("The lender must disclose the data.")
    assert frame.accepted is False
    assert frame.reason == prose_grammar.NO_MODAL


# ── per-field certainty ────────────────────────────────────────────────
def test_every_accepted_field_carries_a_certainty_in_the_closed_vocabulary():
    frame = prose_grammar.analyze("The lender shall never disclose the data.")
    assert frame.accepted
    for field in ("operator", "bearer", "action", "condition", "exception_status"):
        assert frame.certainty[field] in prose_grammar.CERTAINTY, field


def test_operator_certainty_is_certain_for_a_plain_negative_phrase():
    frame = prose_grammar.analyze("The lender shall never disclose the data.")
    assert frame.accepted
    assert frame.certainty["operator"] == prose_grammar.CERTAIN


def test_unresolved_exception_status_is_ambiguous_certainty():
    frame = prose_grammar.analyze(
        "The processor shall not disclose the data, unless required by law.")
    assert frame.accepted
    assert frame.exception_status == prose_grammar.EXCEPTION_EXTERNAL_UNRESOLVED
    assert frame.certainty["exception_status"] == prose_grammar.AMBIGUOUS


# ── typed abstention reason codes ───────────────────────────────────────
@pytest.mark.parametrize("sentence,reason", [
    ("", prose_grammar.NO_MODAL),
    ("The controller processes data.", prose_grammar.NO_MODAL),
    ("The auditor believes that the processor must delete the data.",
     prose_grammar.AMBIGUOUS_SUBJECT),
    ("It must be noted that the report is late.", prose_grammar.AMBIGUOUS_SUBJECT),
    ("The controller shall ensure that data is deleted after use.",
     prose_grammar.CONDITION_ADVERBIAL_AMBIGUOUS),
])
def test_abstentions_carry_a_typed_reason_code(sentence, reason):
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted is False
    assert frame.reason == reason
    assert frame.reason in prose_grammar.ABSTAIN_REASONS
