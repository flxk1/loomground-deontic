# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The optional, additive carry fields — deadline, cross_references, sanction.

These close the "carry vs check" gap: the solver's norm_contract already CHECKS
typed temporal/deadline, cross-references, and sanctions, but the grammar carried
none of them. They are optional and additive: a norm that sets none of them must
serialise, validate, and render exactly as before, and the canonical statement
surface (operator over bearer:action with condition/exception) is unchanged.

    python -m pytest tests/test_carry_fields.py
"""
from __future__ import annotations

import re

import pytest

import deontic
from deontic import grammar


# -- defaults empty => existing behaviour is byte-for-byte unchanged ---------

def test_defaults_are_empty_and_absent_by_default():
    f = deontic.DeonticFormula("O", "controller", "notify")
    assert f.deadline == ""
    assert f.cross_references == []
    assert f.sanction == ""


def test_render_unchanged_when_no_carry_fields():
    # The canonical one-liner (with condition + exception) is exactly as before.
    f = deontic.DeonticFormula(
        operator="O", bearer="controller", action="implement TOMs",
        condition="processing is carried out", exception="Art.11",
    )
    assert f.render() == (
        "if [processing is carried out] then O(controller : implement TOMs) "
        "unless [Art.11]"
    )


def test_to_dict_carries_empty_fields_and_false_flags_by_default():
    d = deontic.DeonticFormula("O", "x", "act").to_dict()
    assert d["deadline"] == ""
    assert d["cross_references"] == []
    assert d["sanction"] == ""
    assert d["timebound"] is False
    assert d["cross_referenced"] is False
    assert d["sanctioned"] is False
    # the pre-existing derived flags are untouched
    assert d["conditional"] is False
    assert d["defeasible"] is False


def test_project_surface_is_unchanged_by_the_carry_fields():
    # project() is the canonical statement projection; it must not grow keys.
    f = deontic.formula_from_fields(
        "obligation", "controller", "notify",
        deadline="within 24 hours",
        cross_references=["Article 43"],
        sanction="a fine",
    )
    assert set(deontic.project(f)) == {
        "operator", "bearer", "action", "condition", "exception",
        "negated", "incident", "counterparty",
    }


def test_round_trip_of_canonical_core_still_holds_without_carry_fields():
    f = deontic.DeonticFormula("F", "processor", "engage a subprocessor",
                               condition="no instruction", exception="Art.28")
    again = deontic.parse(f.render())
    assert deontic.project(again) == deontic.project(f)


# -- round-trip of each new field: from_fields -> to_dict -> validate --------

def test_deadline_round_trips_and_validates():
    f = deontic.formula_from_fields(
        "obligation", "controller", "notify the authority",
        deadline="within 72 hours")
    assert f.deadline == "within 72 hours"
    d = f.to_dict()
    assert d["deadline"] == "within 72 hours"
    assert d["timebound"] is True
    assert "within [within 72 hours]" in d["formula"]
    assert grammar.validate(f)["ok"]


def test_cross_references_round_trip_and_validate():
    f = deontic.formula_from_fields(
        "prohibition", "processor", "transfer the data",
        cross_references=["Article 44", "Article 46"])
    assert f.cross_references == ["Article 44", "Article 46"]
    d = f.to_dict()
    assert d["cross_references"] == ["Article 44", "Article 46"]
    assert d["cross_referenced"] is True
    assert "in accordance with [Article 44; Article 46]" in d["formula"]
    assert grammar.validate(f)["ok"]


def test_sanction_round_trips_and_validates():
    f = deontic.formula_from_fields(
        "obligation", "controller", "keep records",
        sanction="a fine up to EUR 20 000 000")
    assert f.sanction == "a fine up to EUR 20 000 000"
    d = f.to_dict()
    assert d["sanction"] == "a fine up to EUR 20 000 000"
    assert d["sanctioned"] is True
    assert "on pain of [a fine up to EUR 20 000 000]" in d["formula"]
    assert grammar.validate(f)["ok"]


def test_all_three_render_in_order_after_the_canonical_statement():
    f = deontic.formula_from_fields(
        "obligation", "controller", "notify",
        condition="a breach occurs", exception="low risk",
        deadline="72 hours", cross_references=["Article 33"],
        sanction="an administrative fine")
    assert f.render() == (
        "if [a breach occurs] then O(controller : notify) unless [low risk] "
        "within [72 hours] in accordance with [Article 33] "
        "on pain of [an administrative fine]"
    )


def test_from_fields_does_not_share_the_default_list():
    a = deontic.formula_from_fields("obligation", "x", "act")
    b = deontic.formula_from_fields("obligation", "y", "act")
    a.cross_references.append("Article 1")
    assert b.cross_references == []


def test_validate_rejects_non_string_cross_references():
    f = deontic.DeonticFormula("O", "x", "act")
    f.cross_references = ["ok", ""]
    report = grammar.validate(f)
    assert not report["ok"]
    assert any("cross_references" in e for e in report["errors"])


# -- schema: the new fields are optional; old and new statements validate ----

def test_schema_accepts_minimal_and_extended_statements():
    jsonschema = pytest.importorskip("jsonschema")
    schema = deontic.schema("statement")
    # a minimal (pre-existing) statement still validates
    jsonschema.validate(
        {"operator": "O", "bearer": "controller", "action": "notify"}, schema)
    # a statement carrying all three new fields validates too
    jsonschema.validate({
        "operator": "O", "bearer": "controller", "action": "notify",
        "deadline": "within 24 hours",
        "cross_references": ["Article 43"],
        "sanction": "a fine",
    }, schema)


def test_schema_still_forbids_unknown_properties():
    jsonschema = pytest.importorskip("jsonschema")
    schema = deontic.schema("statement")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {"operator": "O", "bearer": "x", "action": "y", "surprise": 1},
            schema)


# -- the new published cues exist and compile as regex -----------------------

def test_new_extraction_cues_exist_and_compile():
    ex = deontic.load_json("extraction.json")
    for section in ("deadline_cues", "cross_reference_cues", "sanction_cues"):
        assert section in ex, f"missing extraction section: {section}"
        assert ex[section], f"empty extraction section: {section}"
        for name, pattern in ex[section].items():
            re.compile(pattern)  # raises re.error on a bad pattern


def test_deadline_cue_captures_a_relative_deadline():
    ex = deontic.load_json("extraction.json")
    m = re.search(ex["deadline_cues"]["relative"],
                  "the controller shall notify within 72 hours", re.I)
    assert m and m.group("deadline") == "72 hours"


def test_cross_reference_cue_captures_an_article():
    ex = deontic.load_json("extraction.json")
    m = re.search(ex["cross_reference_cues"]["instrument"],
                  "processed in accordance with Article 43", re.I)
    assert m and m.group("ref").startswith("Article 43")


def test_sanction_cue_captures_a_penalty_clause():
    ex = deontic.load_json("extraction.json")
    m = re.search(ex["sanction_cues"]["lead"],
                  "the operator shall be liable to a fine", re.I)
    assert m
