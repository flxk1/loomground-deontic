# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""L122: every ``nd-system.json`` binding's ``form_slot`` must resolve.

A ``form_slot`` is published as ``"statement.<field>"``: it must name a
property that actually exists on ``artifacts/schema/statement.schema.json``
(so a consumer that reads the binding can go find the slot it names), or be
``null`` with a ``"reason"`` string explaining why the slot has no schema
field of its own. ``statement.exception_status`` is the one binding this gate
used to fail on: ``exception_status`` was missing from the schema even though
the binding named it. It is now a real schema property (:func:`deontic.project`
emits it — see ``test_project_emits_exception_status``), so every binding in
the shipped ``nd-system.json`` resolves.

    python -m pytest tests/test_binding_slots_resolve.py
"""
from __future__ import annotations

import copy

import pytest

import deontic
from deontic import plane as dplane


def _statement_properties() -> set[str]:
    return set(deontic.schema("statement")["properties"])


def _resolve_binding(binding: dict, properties: set[str]) -> None:
    """Raise ``AssertionError`` if ``binding`` does not resolve.

    A non-null ``form_slot`` must be ``"statement.<field>"`` with ``<field>``
    a real ``statement.schema.json`` property. A ``null`` ``form_slot`` must
    carry a non-empty ``"reason"`` string instead — a silent null is not an
    honest abstention.
    """
    slot = binding.get("form_slot")
    if slot is None:
        reason = binding.get("reason")
        assert isinstance(reason, str) and reason.strip(), (
            f"binding {binding!r} has a null form_slot with no reason"
        )
        return
    assert isinstance(slot, str) and slot.startswith("statement."), (
        f"form_slot {slot!r} is not of the shape 'statement.<field>'"
    )
    field = slot[len("statement."):]
    assert field in properties, (
        f"form_slot {slot!r} does not resolve: {field!r} is not a property "
        f"of statement.schema.json (have: {sorted(properties)})"
    )


def test_every_shipped_binding_resolves():
    doc = dplane.nd_system()
    properties = _statement_properties()
    bindings = doc["bindings"]
    assert bindings, "nd-system.json must publish at least one binding"
    for binding in bindings:
        _resolve_binding(binding, properties)


def test_exception_status_binding_resolves_against_the_schema():
    doc = dplane.nd_system()
    properties = _statement_properties()
    (exc_status,) = [b for b in doc["bindings"] if b["form_slot"] == "statement.exception_status"]
    _resolve_binding(exc_status, properties)
    assert "exception_status" in properties


def test_project_emits_exception_status():
    # the binding resolves to a schema field project() actually fills, not
    # just a schema property that happens to exist unused.
    f = deontic.formula_from_fields(
        "obligation", "controller", "notify",
        exception="required by Article 6",
        exception_status=deontic.prose_grammar.classify_exception_status("required by Article 6"),
    )
    projected = deontic.project(f)
    assert projected["exception_status"] == deontic.prose_grammar.EXCEPTION_XREF_UNRESOLVED


def test_a_bogus_form_slot_fails_the_gate():
    doc = copy.deepcopy(dplane.nd_system())
    doc["bindings"].append({
        "form_slot": "statement.this_field_does_not_exist",
        "allowed_axes": ["operator"],
        "required": False,
    })
    properties = _statement_properties()
    with pytest.raises(AssertionError):
        for binding in doc["bindings"]:
            _resolve_binding(binding, properties)


def test_a_null_form_slot_without_a_reason_fails_the_gate():
    doc = copy.deepcopy(dplane.nd_system())
    doc["bindings"].append({
        "form_slot": None,
        "allowed_axes": ["operator"],
        "required": False,
    })
    properties = _statement_properties()
    with pytest.raises(AssertionError):
        for binding in doc["bindings"]:
            _resolve_binding(binding, properties)
