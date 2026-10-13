# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Gate C of tools/check_companion.py (power-verb cue parity) must be able to
fail: the skill engine carries its own copy of `_POWER_VERBS` and
`_has_active_require`, and nothing else keeps them equal to the package's.
These tests prove the gate catches that class of drift.

    python -m pytest tests/test_check_companion.py
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "check_companion.py"


def _checker():
    spec = importlib.util.spec_from_file_location("check_companion_under_test", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gate_c_passes_on_the_packaged_sources():
    ck = _checker()
    assert ck.check_power_verb_parity() == []
    assert ck.check_vocabulary() == []


def test_gate_c_fails_when_engine_pattern_drifts_from_the_package(monkeypatch):
    ck = _checker()
    original = ck.eng._POWER_VERBS
    try:
        ck.eng._POWER_VERBS = re.compile(r"\btotally_different\b")
        fails = ck.check_power_verb_parity()
        assert any("_POWER_VERBS" in f for f in fails), fails
    finally:
        ck.eng._POWER_VERBS = original


def test_gate_c_fails_when_engine_require_helper_drifts_from_the_package(monkeypatch):
    ck = _checker()
    original = ck.eng._has_active_require
    try:
        ck.eng._has_active_require = lambda text: False  # always disagrees on "require"
        fails = ck.check_power_verb_parity()
        assert any("_has_active_require" in f for f in fails), fails
    finally:
        ck.eng._has_active_require = original


def test_gate_c_cli_exits_nonzero_when_patterns_drift(monkeypatch, tmp_path):
    # Exercise the __main__ reporting path indirectly via the function surface
    # (the module's CLI has no --artifact-style override, so this calls the
    # functions directly rather than shelling out, unlike check_extraction's
    # equivalent test).
    ck = _checker()
    original = ck.eng._POWER_VERBS
    try:
        ck.eng._POWER_VERBS = re.compile(r"\bnonsense\b")
        total = len(ck.check_power_verb_parity())
        assert total > 0
    finally:
        ck.eng._POWER_VERBS = original
    assert ck.check_power_verb_parity() == []
