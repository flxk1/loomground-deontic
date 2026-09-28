# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Round 5: operators carry no 5D dimension, in any form or under any name; a
norm's factual side enters the versum as its own action-type entry, referenced
(never asserted) by the deontic `action` nD coordinate and linked to the norm
by a structural 'embeds' link. This file checks the wording that carries that
decision (semantically, not by a single-word grep) and pins the credit-case
producer spans the decision depends on.

    python -m pytest tests/test_round5_action_type.py
"""
from __future__ import annotations

import re
from pathlib import Path

import deontic
from deontic import plane as dplane
from deontic.artifacts import load_json

SRC = Path(deontic.__file__).resolve().parent

DIMENSION_NAMES = {"causal", "intentional", "temporal", "conditional", "defeasible",
                    "structural", "relational", "dimension", "dimensions"}
OPERATOR_TERMS = {"operator", "operators", "o/p/f", "o, p, f",
                   "obligation", "permission", "prohibition", "ought", "modal", "modality"}
# Cues that flip an otherwise-positive operator/dimension sentence into a denial.
NEGATION_CUES = ("no ", "not ", "never ", "none", "carries no", "carry no",
                  "does not", "is not a", "no operator", "no such", "no dispatch")


def _sentences(text: str) -> list[str]:
    # crude but adequate sentence splitter for these hand-written docstrings/JSON prose
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", text) if s.strip()]


def _asserts_operator_dimension_projection(text: str) -> bool:
    """True iff some sentence in ``text`` associates an operator/normative-predicate
    term with a dimension name WITHOUT a negation cue in the same sentence — i.e. it
    reads as a positive projection statement, not a denial of one."""
    lowered_sentences = _sentences(text.lower())
    for sentence in lowered_sentences:
        has_operator_term = any(term in sentence for term in OPERATOR_TERMS)
        has_dimension_term = any(name in sentence for name in DIMENSION_NAMES)
        if has_operator_term and has_dimension_term:
            if not any(cue in sentence for cue in NEGATION_CUES):
                return True
    return False


def test_dimensions_json_describes_no_operator_projection():
    doc = load_json("vocabulary", "dimensions.json")
    text = doc["describes"]
    assert not _asserts_operator_dimension_projection(text)
    # positive requirements from the Round 5 decision
    assert "no 5d dimension" in text.lower()
    assert "action-type entry" in text.lower() or "action type" in text.lower()


def test_operators_module_docstring_no_operator_projection():
    text = SRC.joinpath("operators.py").read_text(encoding="utf-8")
    doc = text.split('"""', 2)[1]  # the module docstring
    assert not _asserts_operator_dimension_projection(doc)
    assert "no 5d dimension" in doc.lower()
    assert "action-type entry" in doc.lower() or "action type" in doc.lower()


def test_action_axis_documented_as_a_concept_reference_not_a_5d_channel():
    doc = dplane.nd_system()
    action_axis = doc["axes"]["action"]
    assert action_axis["value_type"] == "concept_reference"
    text = doc["describes"].lower()
    assert "action" in text and "concept_reference" in text.replace("`", "")
    assert "spans.content" in doc["describes"] or "spans.content" in text
    assert "embeds" in text
    assert "5d channel" not in text or "not a 5d channel" in text


def test_negation_lives_on_the_norm_not_the_action_type():
    text = dplane.nd_system()["describes"].lower()
    assert "negated" in text
    assert "polarity" in text or "not/never clause" in text


# ── the credit-decision case: pinned producer spans (independent of docs) ──
CREDIT = {
    "s3": "The controller must not make a solely automated decision on a credit application.",
    "s4": "The controller may use the score to prepare a decision.",
    "s6": "A reviewer shall examine every rejection before it is sent.",
}
EXPECTED_CONTENT = {
    "s3": "make a solely automated decision on a credit application",
    "s4": "use the score to prepare a decision",
    "s6": "examine every rejection",
}
EXPECTED_CONDITION = {"s6": "before it is sent"}


def test_producer_spans_slice_exactly_the_contracted_text():
    for key, content in EXPECTED_CONTENT.items():
        sentence = CREDIT[key]
        (claim,) = dplane.produce(sentence)
        span = claim["spans"]["content"]
        assert span["text"] == content
        assert sentence[span["start"]:span["end"]] == content
    (s6_claim,) = dplane.produce(CREDIT["s6"])
    cond_span = s6_claim["spans"]["condition"]
    assert cond_span["text"] == EXPECTED_CONDITION["s6"]
    assert CREDIT["s6"][cond_span["start"]:cond_span["end"]] == EXPECTED_CONDITION["s6"]


def test_binding_and_affinity_still_carry_no_dimension_for_any_operator():
    from deontic import contract
    assert dplane.binding() == {}
    for op in deontic.VALID_OPERATORS:
        assert contract.dimension_affinity(op) is None
