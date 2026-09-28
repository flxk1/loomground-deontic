# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Regression tests for the six 'deontic' findings on commit 2c48861 (Phase 1
prose grammar) plus the versum nD-axis blocker, each named for the point it
covers so a revert of the matching fix fails the matching test:

  (1) test_exception_leads_except_and_save_where_are_restored
  (2a) test_prohibition_phrases_is_prohibited_from_and_is_not_permitted_to
  (2b) test_subject_to_condition_lead_extracts_condition_and_bearer
  (2c) test_bearer_and_condition_certainty_are_computed_not_hardcoded
  (2d) test_double_negation_never_not_abstains_ambiguous
  (3) test_check_extraction_gazetteer_sync_gate_passes
      test_extraction_describes_no_longer_claims_prose_reads_it_at_runtime
  (4) test_prose_grammar_docstring_cites_real_test_files
  (5) test_extract_prose_and_deontic_formula_carry_exception_status
  (6) test_pyproject_package_data_covers_every_gazetteer_file
  (nd-axis) test_nd_system_declares_exception_status_axis_and_produce_agrees
            test_every_produce_coordinate_key_is_a_declared_nd_axis
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

try:
    import tomllib  # stdlib, Python >= 3.11
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    tomllib = None

import pytest

import deontic
from deontic import plane as dplane
from deontic import prose
from deontic.prose_grammar import (
    analyze, AMBIGUOUS_NEGATION, CERTAIN, INFERRED, NONE_DETECTED,
)

ROOT = Path(deontic.__file__).resolve().parent.parent.parent
PKG_DIR = Path(deontic.__file__).resolve().parent
CHECKER_PATH = ROOT / "tools" / "check_extraction.py"


def _checker():
    spec = importlib.util.spec_from_file_location("check_extraction_under_test", CHECKER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── (1) exception leads 'except' / 'save where' restored ────────────────────
def test_exception_leads_except_and_save_where_are_restored():
    f1 = analyze("The processor shall not disclose the data, except with consent.")
    assert f1.accepted
    assert f1.operator == "F"
    assert f1.action == "disclose the data"
    assert f1.exception == "with consent"
    assert f1.exception_status != NONE_DETECTED

    f2 = analyze("The processor shall not disclose the data, save where required by law.")
    assert f2.accepted
    assert f2.operator == "F"
    assert f2.action == "disclose the data"
    assert f2.exception == "required by law"
    assert f2.exception_status != NONE_DETECTED


# ── (2a) 'is prohibited from' / 'is not permitted to' lower to F ────────────
def test_prohibition_phrases_is_prohibited_from_and_is_not_permitted_to():
    f1 = analyze("The controller is prohibited from disclosing the data.")
    assert f1.accepted and f1.operator == "F"

    f2 = analyze("The controller is not permitted to disclose the data.")
    assert f2.accepted and f2.operator == "F"


# ── (2b) 'Subject to X,' is a condition lead, not swallowed into bearer ─────
def test_subject_to_condition_lead_extracts_condition_and_bearer():
    f = analyze("Subject to Article 6, the controller shall delete the data.")
    assert f.accepted
    assert f.condition == "Article 6"
    assert f.bearer == "controller"


# ── (2c) certainty is computed, not a hard-coded constant ───────────────────
def test_bearer_and_condition_certainty_are_computed_not_hardcoded():
    # A cue-anchored bearer (subject immediately before the modal): CERTAIN.
    plain = analyze("The controller shall delete the data.")
    assert plain.accepted
    assert plain.certainty["bearer"] == CERTAIN

    # A bearer reached only by stripping the negative determiner "no" (the
    # determiner itself carried the clause's negation, not a plain article):
    # INFERRED, not CERTAIN.
    forced = analyze("No third party shall access the data.")
    assert forced.accepted
    assert forced.operator == "F"
    assert forced.certainty["bearer"] == INFERRED

    # A sentence-initial condition lead is a direct cue: CERTAIN.
    lead_cond = analyze("If the data subject objects, the controller shall stop processing.")
    assert lead_cond.accepted
    assert lead_cond.certainty["condition"] == CERTAIN

    # A trailing adverbial condition (tail_leads) is a weaker, non-anchoring
    # route: INFERRED.
    tail_cond = analyze("A reviewer shall examine every rejection before it is sent.")
    assert tail_cond.accepted
    assert tail_cond.condition
    assert tail_cond.certainty["condition"] == INFERRED

    # The certainty for these two different conditions must not collapse to
    # the same hard-coded value regardless of branch.
    assert lead_cond.certainty["condition"] != tail_cond.certainty["condition"]


# ── (2d) 'shall never not' is an ambiguous double negation, never collapsed ─
def test_double_negation_never_not_abstains_ambiguous():
    f = analyze("The processor shall never not disclose the data.")
    assert not f.accepted
    assert f.reason == AMBIGUOUS_NEGATION


# ── (3) extraction.json / check_extraction.py stay in sync with the gazetteer
def test_check_extraction_gazetteer_sync_gate_passes():
    ck = _checker()
    assert ck.check_gazetteer_sync() == []
    assert ck.run() == []


def test_extraction_describes_no_longer_claims_prose_reads_it_at_runtime():
    from deontic.artifacts import load_json
    describes = load_json("extraction.json")["describes"]
    assert "reads these same cues" not in describes
    assert "applies these same published modal and slot cues at runtime" not in describes
    assert "does NOT read this file at runtime" in describes


# ── (4) the docstring citation names real test files ────────────────────────
def test_prose_grammar_docstring_cites_real_test_files():
    import deontic.prose_grammar as pg
    doc = pg.__doc__
    assert "test_prose_grammar.py" not in doc
    assert "test_prose_grammar_dispatch.py" in doc
    assert "test_prose_grammar_phrases.py" in doc
    assert (ROOT / "tests" / "test_prose_grammar_dispatch.py").is_file()
    assert (ROOT / "tests" / "test_prose_grammar_phrases.py").is_file()


# ── (5) no public reader exposes bare polarity when an exception is detected
def test_extract_prose_and_deontic_formula_carry_exception_status():
    formulae = prose.extract(
        "The processor shall not disclose the data, except with consent.")
    assert len(formulae) == 1
    f = formulae[0]
    assert hasattr(f, "exception_status")
    assert f.exception == "with consent"
    assert f.exception_status not in ("", NONE_DETECTED)

    # A sentence with no exception still carries an explicit, non-bare status.
    plain = prose.extract("The controller shall delete the data.")[0]
    assert plain.exception_status == NONE_DETECTED

    # The claim-level reader already carries it too (produce -> claim_for).
    claim = dplane.produce(
        "The processor shall not disclose the data, except with consent.")[0]
    view = dplane.read_polarity(claim)
    assert view.exception_status not in ("", NONE_DETECTED)


# ── (6) package-data covers every artifact file, including the gazetteers ──
def _package_data_globs() -> list[str]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if tomllib is not None:
        doc = tomllib.loads(text)
        return doc["tool"]["setuptools"]["package-data"]["deontic"]
    # tomllib is unavailable before Python 3.11. Rather than skip the check,
    # extract the one array this test needs with stdlib-only tools (re +
    # ast.literal_eval): the TOML array-of-strings syntax used here is a
    # valid Python list literal, so this preserves the same assertion
    # without a third-party TOML parser.
    import ast
    match = re.search(
        r"\[tool\.setuptools\.package-data\]\s*\ndeontic\s*=\s*(\[.*?\])",
        text,
        re.DOTALL,
    )
    assert match, "could not locate [tool.setuptools.package-data] deontic array"
    return ast.literal_eval(match.group(1))


def test_pyproject_package_data_covers_every_gazetteer_file():
    import fnmatch
    globs = _package_data_globs()
    assert "artifacts/gazetteer/*.json" in globs
    gaz_files = sorted((PKG_DIR / "artifacts" / "gazetteer").glob("*.json"))
    assert gaz_files, "no gazetteer files found to check coverage against"
    for path in gaz_files:
        rel = path.relative_to(PKG_DIR).as_posix()
        assert any(fnmatch.fnmatch(rel, pat) for pat in globs), \
            f"{rel} not covered by any package-data glob"


def test_pyproject_package_data_covers_every_file_under_artifacts():
    """No file under artifacts/ is silently missing from a built wheel."""
    import fnmatch
    globs = _package_data_globs()
    artifacts_dir = PKG_DIR / "artifacts"
    uncovered = []
    for path in artifacts_dir.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(PKG_DIR).as_posix()
        if not any(fnmatch.fnmatch(rel, pat) for pat in globs):
            uncovered.append(rel)
    assert not uncovered, f"artifacts not covered by package-data globs: {uncovered}"


# ── (nd-axis blocker) exception_status is a declared nD axis ────────────────
def test_nd_system_declares_exception_status_axis_and_produce_agrees():
    d = dplane.plane()
    claims = d["produce"](
        "The controller must not make a solely automated decision on a "
        "credit application.")
    assert "exception_status" in claims[0]["coordinates"]
    assert "exception_status" in d["nd_system"]["axes"]


def test_every_produce_coordinate_key_is_a_declared_nd_axis():
    d = dplane.plane()
    axes = set(d["nd_system"]["axes"])
    sentences = [
        "The controller must not make a solely automated decision on a "
        "credit application.",
        "The processor shall not disclose the data, except with consent.",
        "Subject to Article 6, the controller shall delete the data.",
        "A reviewer shall examine every rejection before it is sent.",
    ]
    for sentence in sentences:
        for claim in d["produce"](sentence):
            assert set(claim["coordinates"]) <= axes, (
                f"produce() emitted a coordinate not declared as an nD axis "
                f"for {sentence!r}: {set(claim['coordinates']) - axes}")
