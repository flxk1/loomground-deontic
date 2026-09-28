# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Gate B of tools/check_extraction.py must be able to fail.

Round 4 (deontic-is-ought correction): Gate B's rule is that no operator (O/P/F)
carries a 5D dimension anywhere in the published `extraction.json` — ought is
not a fact on the 5D manifold; only a norm's content, lowered through the
factual plane, can be. These tests copy the artifact to a temporary directory,
inject an operator->dimension mapping (the shape the language used to publish
under `operator_axis`, decision D1, now reversed), and assert the gate fails on
every injected copy while passing on the packaged (now binding-free) artifact.

    python -m pytest tests/test_check_extraction.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "check_extraction.py"
ARTIFACT = ROOT / "src" / "deontic" / "artifacts" / "extraction.json"


def _checker():
    spec = importlib.util.spec_from_file_location("check_extraction_under_test", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mutated_copy(tmp_path: Path, key: str, mapping: dict) -> Path:
    """The packaged artifact with ``mapping`` injected under ``key`` (a new or
    existing top-level key) — a schema-valid, otherwise-untouched copy."""
    doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    doc[key] = mapping
    out = tmp_path / "extraction.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def test_packaged_artifact_carries_no_operator_axis_key():
    doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "operator_axis" not in doc


def test_gate_b_passes_on_the_packaged_artifact():
    ck = _checker()
    assert ck.check_operator_mapping() == []
    assert ck.run() == []


@pytest.mark.parametrize("mapping", [
    {"O": "causal"},                              # single-operator mapping
    {"P": "intentional"},                         # single-operator mapping
    {"F": "causal"},                              # single-operator mapping
    {"O": "causal", "F": "causal", "P": "intentional"},  # the old D1 binding, restored
])
def test_gate_b_fails_on_any_injected_operator_dimension_mapping(tmp_path, mapping):
    ck = _checker()
    copy = _mutated_copy(tmp_path, "operator_axis", mapping)
    fails = ck.check_operator_mapping(ck.load(copy))
    assert any("operator->5D-dimension map" in f or "operator_axis" in f for f in fails), fails
    # every other gate still passes on the copy: only Gate B caught it
    others = [f for fn in (ck.check_incident_cues, ck.check_incident_rules,
                           ck.check_regex_validity, ck.check_validity_rules)
              for f in fn(ck.load(copy))]
    assert others == []


@pytest.mark.parametrize("mapping,key", [
    ({"O": "causal"}, "some_other_field"),
    ({"P": "intentional"}, "hints"),
    ({"F": "causal"}, "debug_only"),
])
def test_gate_b_fails_on_an_operator_dimension_mapping_under_any_key(tmp_path, mapping, key):
    """Gate B does not merely check the key ``operator_axis`` — it detects an
    operator->5D-dimension map under ANY key, since ought binds no 5D dimension
    regardless of where a stray mapping would be published."""
    ck = _checker()
    copy = _mutated_copy(tmp_path, key, mapping)
    fails = ck.check_operator_mapping(ck.load(copy))
    assert any("operator->5D-dimension map" in f for f in fails), fails


def test_gate_b_cli_exits_nonzero_on_the_mutated_copy(tmp_path):
    copy = _mutated_copy(tmp_path, "operator_axis", {"O": "causal", "P": "intentional"})
    bad = subprocess.run([sys.executable, str(CHECKER), "--artifact", str(copy)],
                         capture_output=True, text=True)
    assert bad.returncode == 1, bad.stdout + bad.stderr
    assert "[FAIL] operator mapping" in bad.stdout
    good = subprocess.run([sys.executable, str(CHECKER)], capture_output=True, text=True)
    assert good.returncode == 0, good.stdout + good.stderr
    assert "ALL GREEN" in good.stdout
