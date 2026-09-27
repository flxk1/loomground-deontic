# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""COVERAGE (per-field abstention) + ``action_head``.

Abstention is per field: a sentence with a clear modal yields a modality even
when its bearer or action cannot be grounded (``ProseFrame.field_reasons``
records exactly the fields that failed, never collapsing the whole sentence
to one guess). ``action_head`` is new, additive to the existing ``action``
(the full span, unchanged): the governing verb's lemma, stdlib rule-based and
deterministic (``deontic.prose_grammar._action_head`` /
``verb_lemma.json``) — the *matrix* verb of the action clause, never a verb
inside a subordinate complement ("ensure that the data is disclosed" heads on
"ensure", never "disclose"). It abstains
(``field_reasons["action_head"]``) rather than guess when no governing verb
can be identified.

    python -m pytest tests/test_action_head.py
"""
from __future__ import annotations

import pytest

from deontic import prose_grammar as pg


# ── COVERAGE: abstention is per field, not per sentence ──────────────────
def test_clear_modal_with_unclear_bearer_still_yields_modality():
    # "The auditor believes that ..." is a clause-marker subject: bearer
    # abstains, but the modal ("must") and the action ("delete the data")
    # are both perfectly clear and must not be thrown away with it.
    frame = pg.analyze("The auditor believes that the processor must delete the data.")
    assert frame.operator == "O"
    assert frame.action == "delete the data"
    assert frame.action_head == "delete"
    assert frame.field_reasons == {"bearer": pg.AMBIGUOUS_SUBJECT}
    assert frame.bearer == ""
    # accepted stays the whole-frame predicate (bearer is one of its three
    # required fields) — per-field callers read field_reasons instead.
    assert frame.accepted is False
    assert frame.reason == pg.AMBIGUOUS_SUBJECT


def test_clear_modal_with_unclear_action_still_yields_modality_and_bearer():
    # a bare passive action ("be notified ...") is not itself an act: action
    # (and so action_head) abstains, but the modal and the bearer are clear.
    frame = pg.analyze("The data subject shall be notified without delay.")
    assert frame.operator == "O"
    assert frame.bearer == "data subject"
    assert frame.action == ""
    assert frame.action_head == ""
    assert frame.field_reasons == {
        "action": pg.ACTION_IMPLICIT, "action_head": pg.ACTION_IMPLICIT,
    }


def test_every_field_reason_key_is_a_typed_abstain_reason():
    frame = pg.analyze("It must be noted that the report is late.")
    assert set(frame.field_reasons) <= {"bearer", "action", "action_head", "operator",
                                        "exception_status"}
    for reason in frame.field_reasons.values():
        assert reason in pg.ABSTAIN_REASONS or reason in pg.EXCEPTION_STATUSES


# ── action_head over >= 10 distinct constructions, incl. passive ─────────
@pytest.mark.parametrize("sentence,expected_head", [
    # 1. plain transitive
    ("The processor shall disclose the data.", "disclose"),
    # 2. multi-word object
    ("The controller shall notify the supervisory authority.", "notify"),
    # 3. 'shall ensure that' + a phrasal complement whose own (passive) verb
    #    must NOT be picked up as the head
    ("The controller shall ensure that the data is disclosed only with consent.", "ensure"),
    # 4. adverb-fronted action
    ("The processor shall promptly notify the authority.", "notify"),
    # 5. phrasal verb (particle 'out')
    ("The processor shall carry out a risk assessment.", "carry"),
    # 6. causative passive ('have X corrected')
    ("The controller shall have the data corrected without delay.", "have"),
    # 7. forced-F modal phrase, gerund complement (tests the lemma table's
    #    gerund-stripping entry, not just the bare infinitive)
    ("The processor is prohibited from disclosing the data.", "disclose"),
    # 8. forced-P modal phrase, infinitive complement
    ("The controller is authorised to disclose the data.", "disclose"),
    # 9. negative-determiner-forced prohibition, plain action
    ("No processor shall retain the record.", "retain"),
    # 10. 'must' modal
    ("The processor must delete the data.", "delete"),
    # 11. verb requiring silent-e restoration in the lemma fallback (not in
    #     the exceptions table): 'stores' -> 'store'
    ("The processor shall store the record for six years.", "store"),
    # 12. object-fronted-by-determiner action, third construction of the
    #     complementizer family ('shall see to it that ...' collapses to the
    #     matrix verb 'see')
    ("The controller shall see to it that the request is answered.", "see"),
])
def test_action_head_across_constructions(sentence, expected_head):
    frame = pg.analyze(sentence)
    assert frame.action_head == expected_head, (sentence, frame)
    assert "action_head" not in frame.field_reasons


# ── passive: a bare passive action abstains action_head rather than guess ──
def test_action_head_abstains_on_a_bare_passive_action():
    frame = pg.analyze("The data subject shall be notified without delay.")
    assert frame.action_head == ""
    assert frame.field_reasons["action_head"] == pg.ACTION_IMPLICIT


# ── dev-set finding: "chapter" is a cross-reference marker too ───────────
def test_chapter_is_an_xref_marker():
    # surfaced by the scratchpad/p3/dev precision/coverage report: "under
    # Chapter II" is as much an unresolved cross-reference as "under Article
    # 6" or "under Annex I" — classify_exception_status must not call it
    # internal_parsed just because "chapter" was missing from xref_markers.
    assert pg.classify_exception_status("requested to do so by the user under Chapter II") \
        == pg.EXCEPTION_XREF_UNRESOLVED


def test_action_head_is_deterministic_and_pure():
    sentence = "The processor shall carry out a risk assessment."
    a = pg.analyze(sentence)
    b = pg.analyze(sentence)
    assert a.action_head == b.action_head == "carry"


# ── the ledger surfaces action_head, and abstains a whole frame that fails
#    one of operator/bearer/action (action_head's own reason is then the
#    same one that already aborted the frame — see `reason` on the record) ──
def test_ledger_record_carries_action_head_for_an_accepted_sentence(tmp_path):
    from deontic import ledger

    path = tmp_path / "ledger.jsonl"
    ledger.run_batch(["The controller shall notify the authority."], path)
    (record,) = ledger.read_records(path)
    assert record["accepted"] is True
    assert record["action_head"] == "notify"
    assert "field_abstentions" not in record


def test_ledger_record_abstains_whole_frame_when_action_is_a_bare_passive(tmp_path):
    from deontic import ledger

    path = tmp_path / "ledger.jsonl"
    ledger.run_batch(["The data subject shall be notified without delay."], path)
    (record,) = ledger.read_records(path)
    assert record["accepted"] is False
    assert record["reason"] == pg.ACTION_IMPLICIT
