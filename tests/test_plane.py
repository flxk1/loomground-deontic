# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The deontic plane descriptor (shared plane descriptor contract v1) and the
prose producer behind it.

    python -m pytest tests/test_plane.py
"""
from __future__ import annotations

import copy
import importlib.metadata
import json
import re
from pathlib import Path

import pytest

import deontic
from deontic import contract, plane as dplane
from deontic.artifacts import artifact_path, load_json

FIVE = {"structural", "causal", "intentional", "temporal", "relational"}
SRC = Path(deontic.__file__).resolve().parent

CREDIT = {
    "s1": "The bank is a controller.",
    "s2": "The scoring model is part of the credit system.",
    "s3": "The controller must not make a solely automated decision on a credit application.",
    "s4": "The controller may use the score to prepare a decision.",
    "s5": "The controller knows that the training data is inaccurate.",
    "s6": "A reviewer shall examine every rejection before it is sent.",
    "s7": "The review follows the automated scoring.",
}


# ── descriptor shape ──────────────────────────────────────────────
def test_entry_point_registered_and_loads_plane():
    eps = [ep for ep in importlib.metadata.entry_points(group="loomground.planes")
           if ep.name == "deontic"]
    assert len(eps) == 1, "exactly one 'deontic' entry point in loomground.planes"
    assert eps[0].value == "deontic.plane:plane"
    assert eps[0].load() is dplane.plane


def test_descriptor_keys_and_versions():
    d = dplane.plane()
    assert set(d) == {"plane", "language_version", "nd_system", "binding", "produce",
                      "examples"}
    assert d["plane"] == "deontic"
    assert d["language_version"] == deontic.language_version() == deontic.__version__
    assert d["nd_system"]["version"] == d["language_version"]
    assert d["nd_system"]["validation"]["unknown_values"] == "reject"
    assert callable(d["produce"])


def test_nd_system_carries_no_5d_version_key():
    doc = dplane.nd_system()
    assert not [k for k in doc if "5d" in k.lower()]


def test_nd_system_vocabularies_equal_the_language():
    axes = dplane.nd_system()["axes"]
    assert axes["operator"]["vocabulary"] == list(deontic.VALID_OPERATORS)
    assert axes["incident"]["vocabulary"] == list(deontic.INCIDENTS)
    # every statement field is an axis, and every binding rule names a declared axis
    assert set(deontic.project(deontic.parse("O(a : b)"))) == set(axes)
    for rule in dplane.nd_system()["bindings"]:
        assert set(rule["allowed_axes"]) <= set(axes)


# ── binding: ought carries no 5D dimension (Round 4, D1 reversed) ────
def test_binding_is_empty_because_ought_carries_no_5d_dimension():
    b = dplane.binding()
    assert b == {}
    assert "operator_axis" not in load_json("extraction.json")
    doc = dplane.nd_system()
    assert ("operators are ought; the 5D describes what is; a norm's content "
            "enters 5D through the factual plane") in doc["describes"]


def test_contract_affinity_is_none_for_every_operator():
    for op in list(deontic.VALID_OPERATORS) + ["O", "P", "F", "Z"]:
        assert contract.dimension_affinity(op) is None
    assert {op: contract.dimension_affinity(op) for op in deontic.VALID_OPERATORS} == \
        {"O": None, "P": None, "F": None}


def _operator_maps(obj, path=()):
    """Every dict in a JSON tree whose keys are operators and values dimensions."""
    if isinstance(obj, dict):
        if obj and set(obj) <= set(deontic.VALID_OPERATORS) and \
                all(isinstance(v, str) and v in FIVE | {"conditional", "defeasible"}
                    for v in obj.values()):
            yield path
        for k, v in obj.items():
            yield from _operator_maps(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _operator_maps(v, path + (i,))


def test_no_package_data_file_publishes_an_operator_dimension_binding():
    root = SRC / "artifacts"
    hits = []
    for f in sorted(root.rglob("*.json")):
        for p in _operator_maps(json.loads(f.read_text(encoding="utf-8"))):
            hits.append((f.relative_to(root).as_posix(), p))
    assert hits == []
    # and no Python module keeps its own operator -> dimension literal
    literal = re.compile(r"""(?:OP_\w+|["'][OPF]["'])\s*:\s*["'](?:structural|causal|"""
                         r"""intentional|temporal|relational)["']""")
    offenders = [f.name for f in SRC.glob("*.py") if literal.search(f.read_text("utf-8"))]
    assert offenders == []


def test_dimensions_vocabulary_is_not_a_binding():
    # D7 is open: dimensions.json is left as published and carries no operator map.
    doc = deontic.vocabulary("dimensions")
    assert "does not live here" in doc["describes"]
    assert not list(_operator_maps(doc))


# ── the credit-decision case ─────────────────────────────────────
@pytest.mark.parametrize("key", ["s1", "s2", "s5", "s7"])
def test_non_normative_sentences_produce_nothing(key):
    assert dplane.produce(CREDIT[key]) == []


@pytest.mark.parametrize("key,op,bearer,action,condition", [
    ("s3", "F", "controller", "make a solely automated decision on a credit application", ""),
    ("s4", "P", "controller", "use the score to prepare a decision", ""),
    ("s6", "O", "reviewer", "examine every rejection", "before it is sent"),
])
def test_normative_sentences(key, op, bearer, action, condition):
    sentence = CREDIT[key]
    (claim,) = dplane.produce(sentence)
    st = claim["statement"]
    assert (st["operator"], st["bearer"], st["action"], st["condition"]) == \
        (op, bearer, action, condition)
    assert st["negated"] is False  # "must not" is carried by F, not by negation
    assert claim["relation"] == op
    assert claim["span"] == [0, len(sentence)]
    assert claim["method"] == dplane.METHOD_PROSE
    assert claim["coordinates"]["operator"] == op
    assert claim["coordinates"]["bearer"] == bearer
    assert claim["slots"]["statement.bearer"] == "bearer"
    # the operator carries no 5D dimension: it is not a key of the (empty) binding
    assert claim["relation"] not in dplane.binding()


@pytest.mark.parametrize("key,content", [
    ("s3", "make a solely automated decision on a credit application"),
    ("s4", "use the score to prepare a decision"),
    ("s6", "examine every rejection"),
])
def test_content_span_is_a_literal_sentence_offset(key, content):
    sentence = CREDIT[key]
    (claim,) = dplane.produce(sentence)
    span = claim["spans"]["content"]
    assert span == {"start": sentence.find(content), "end": sentence.find(content) + len(content),
                    "text": content}
    assert sentence[span["start"]:span["end"]] == content == span["text"]


def test_condition_span_is_a_literal_sentence_offset_where_present():
    sentence = CREDIT["s6"]
    (claim,) = dplane.produce(sentence)
    span = claim["spans"]["condition"]
    condition = "before it is sent"
    assert sentence[span["start"]:span["end"]] == condition == span["text"]
    # s3/s4 carry no condition: no condition span is published
    (s3,) = dplane.produce(CREDIT["s3"])
    (s4,) = dplane.produce(CREDIT["s4"])
    assert "condition" not in s3["spans"]
    assert "condition" not in s4["spans"]


def test_negated_obligation_is_a_prohibition_never_a_duty():
    for s in ("The processor shall not transfer the data.",
              "The processor may not transfer the data.",
              "The processor must not transfer the data."):
        (f,) = deontic.extract_prose(s)
        assert f.operator == "F" and f.action == "transfer the data"


def test_prose_condition_exception_and_negative_determiner():
    (f,) = deontic.extract_prose(
        "If processing is carried out, the controller shall implement appropriate "
        "measures unless the processing is occasional.")
    assert (f.operator, f.bearer, f.action, f.condition, f.exception) == (
        "O", "controller", "implement appropriate measures",
        "processing is carried out", "the processing is occasional")
    (g,) = deontic.extract_prose("No processor may engage another processor.")
    assert (g.operator, g.bearer) == ("F", "processor")


@pytest.mark.parametrize("sentence", [
    "", "   ", "The auditor believes that the processor must delete the data.",
    "Der Verantwortliche muss die Daten löschen.", "must comply.", "The controller must.",
])
def test_prose_abstains_rather_than_guessing(sentence):
    assert deontic.extract_prose(sentence) == []
    assert dplane.produce(sentence) == []


# ── abstention on shapes the prose lowering cannot read (round 2) ────────
@pytest.mark.parametrize("sentence", [
    "Processing may be necessary.",                    # epistemic 'may be', no agent
    "It must be noted that the report is late.",        # expletive subject
    "The controller shall ensure that data is deleted after use.",  # 'after use' is
                                                        # an adverbial, not a condition
])
def test_prose_abstains_on_non_agentive_expletive_and_adverbial(sentence):
    assert deontic.extract_prose(sentence) == []
    assert dplane.produce(sentence) == []


def test_credit_case_normative_outputs_are_pinned_literally():
    got = {k: [c["statement"] for c in dplane.produce(CREDIT[k])] for k in ("s3", "s4", "s6")}
    blank = {"exception": "", "negated": False, "incident": "", "counterparty": ""}
    assert got == {
        "s3": [{"operator": "F", "bearer": "controller",
                "action": "make a solely automated decision on a credit application",
                "condition": "", **blank}],
        "s4": [{"operator": "P", "bearer": "controller",
                "action": "use the score to prepare a decision", "condition": "", **blank}],
        "s6": [{"operator": "O", "bearer": "reviewer", "action": "examine every rejection",
                "condition": "before it is sent", **blank}],
    }


def test_produce_is_pure_and_deterministic():
    ctx = {"source": {"jurisdiction": "EU"}}
    before = copy.deepcopy(ctx)
    a = dplane.produce(CREDIT["s6"], ctx)
    b = dplane.produce(CREDIT["s6"], None)
    assert a == b and ctx == before
    json.dumps(a)  # serialisable


# ── the formal grammar is unchanged ──────────────────────────────
def test_formal_statements_go_through_parse_unchanged():
    src = "if [processing is carried out] then O(controller : implement TOMs) unless [Art.11]"
    (claim,) = dplane.produce(src)
    assert claim["method"] == dplane.METHOD_PARSE
    assert claim["statement"] == deontic.project(deontic.parse(src))
    with pytest.raises(deontic.DeonticSyntaxError):
        deontic.parse(CREDIT["s3"])  # parse still accepts only the formal grammar
    assert dplane.produce("X(controller : act)") == []  # malformed formal: no claim


# ── rule 4: round-trip over every published example ─────────────
def test_examples_cover_every_published_vector():
    names = {e["name"] for e in dplane.examples()}
    statement_vectors = {v["name"] for v in deontic.conformance_manifest()["vectors"]
                         if v["kind"] == "statement"}
    prose_vectors = {v["name"] for v in load_json("conformance", "prose.json")["vectors"]}
    assert names == statement_vectors | prose_vectors


@pytest.mark.parametrize("example", dplane.examples(), ids=lambda e: e["name"])
def test_round_trip_examples_via_produce(example):
    got = dplane.produce(example["sentence"])
    assert got == example["expected"]


def test_round_trip_reproduces_conformance_expected_field_for_field():
    for vec in deontic.conformance_manifest()["vectors"]:
        if vec["kind"] != "statement":
            continue
        base = artifact_path("conformance", "vectors", vec["name"])
        sentence = base.joinpath("input.deo").read_text(encoding="utf-8").strip()
        expected = load_json("conformance", "vectors", vec["name"], "expected.json")
        (claim,) = dplane.produce(sentence)
        assert claim["statement"] == expected
        for field, value in expected.items():
            if field != "negated" and value:
                assert claim["coordinates"][field] == value
        assert claim["coordinates"]["negated"] is expected["negated"]
