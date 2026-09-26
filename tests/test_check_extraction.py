# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Gate B of tools/check_extraction.py must be able to fail.

Gate B holds ``extraction.json`` ``operator_axis`` to an expectation pinned in the
checker (decision D1), not to ``deontic.contract.dimension_affinity``, which reads
``operator_axis`` itself. These tests copy the artifact to a temporary directory,
make a wrong but schema-valid edit, and assert the gate fails on the copy while
passing on the packaged artifact.

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


def _mutated_copy(tmp_path: Path, **axis) -> Path:
    doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    doc["operator_axis"].update(axis)
    out = tmp_path / "extraction.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def test_gate_b_expectation_is_pinned_not_read_from_the_artifact():
    ck = _checker()
    assert ck.EXPECTED_OPERATOR_AXIS == {"O": "causal", "F": "causal", "P": "intentional"}
    assert "dimension_affinity(" not in CHECKER.read_text(encoding="utf-8")


def test_gate_b_passes_on_the_packaged_artifact():
    ck = _checker()
    assert ck.check_operator_mapping() == []
    assert ck.run() == []


@pytest.mark.parametrize("axis", [
    {"P": "causal"},                            # D1 inverted for permission
    {"O": "intentional", "P": "causal"},        # the versum's old misfit
    {"F": "temporal"},                          # a real dimension, wrong one
])
def test_gate_b_fails_on_a_wrong_but_valid_operator_axis(tmp_path, axis):
    ck = _checker()
    copy = _mutated_copy(tmp_path, **axis)
    fails = ck.check_operator_mapping(ck.load(copy))
    assert any("operator_axis" in f and "pinned D1" in f for f in fails), fails
    # every other gate still passes on the copy: only Gate B caught it
    others = [f for fn in (ck.check_incident_cues, ck.check_incident_rules,
                           ck.check_regex_validity, ck.check_validity_rules)
              for f in fn(ck.load(copy))]
    assert others == []


def test_gate_b_cli_exits_nonzero_on_the_mutated_copy(tmp_path):
    copy = _mutated_copy(tmp_path, P="causal")
    bad = subprocess.run([sys.executable, str(CHECKER), "--artifact", str(copy)],
                         capture_output=True, text=True)
    assert bad.returncode == 1, bad.stdout + bad.stderr
    assert "[FAIL] operator mapping" in bad.stdout
    good = subprocess.run([sys.executable, str(CHECKER)], capture_output=True, text=True)
    assert good.returncode == 0, good.stdout + good.stderr
    assert "ALL GREEN" in good.stdout
