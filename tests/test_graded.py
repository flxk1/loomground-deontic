# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Coverage for the graded (five-valued) deontic scale — O142.

The graded scale is an extension that *projects down* onto the base O/P/F triad
of :mod:`deontic.operators`. These tests pin: the projection of all five grades,
the total order on the chain, the supererogation of *mandūb*, that *wājib* vs
*ḥarām* project to a hard clash while *mandūb* vs *makrūh* do not, and that the
scale never shadows the base triad.

    python -m pytest tests/test_graded.py
"""
from __future__ import annotations

import itertools

import pytest

from deontic import graded, operators


def test_all_five_grades_project_down_to_the_base_triad():
    # wājib → O, ḥarām → F, and the middle three all collapse to P — the very
    # distinction the coarse triad cannot express.
    assert graded.project(graded.GRADE_WAJIB) == operators.OP_OBLIGATION
    assert graded.project(graded.GRADE_HARAM) == operators.OP_PROHIBITION
    assert graded.project(graded.GRADE_MUBAH) == operators.OP_PERMISSION
    assert graded.project(graded.GRADE_MANDUB) == operators.OP_PERMISSION
    assert graded.project(graded.GRADE_MAKRUH) == operators.OP_PERMISSION
    # every projection is a real base operator (the extension mints none)
    for g in graded.GRADED_SCALE:
        assert graded.project(g) in operators.VALID_OPERATORS


def test_middle_three_share_a_projection_but_differ_by_valence():
    # The refinement the triad loses: same base operator (P), distinct valence.
    assert graded.valence(graded.GRADE_MANDUB) == +1
    assert graded.valence(graded.GRADE_MUBAH) == 0
    assert graded.valence(graded.GRADE_MAKRUH) == -1
    assert graded.base_gloss(graded.GRADE_MANDUB) == "permitted"
    assert graded.base_gloss(graded.GRADE_MAKRUH) == "permitted"
    # the fine gloss keeps them apart
    assert graded.gloss(graded.GRADE_MANDUB) == "recommended"
    assert graded.gloss(graded.GRADE_MAKRUH) == "discouraged"


def test_total_order_is_the_ahkam_chain():
    # ḥarām < makrūh < mubāḥ < mandūb < wājib
    chain = [graded.GRADE_HARAM, graded.GRADE_MAKRUH, graded.GRADE_MUBAH,
             graded.GRADE_MANDUB, graded.GRADE_WAJIB]
    assert chain == list(graded.GRADED_SCALE)
    for lo, hi in zip(chain, chain[1:]):
        assert graded.compare(lo, hi) == -1
        assert graded.compare(hi, lo) == +1
        assert graded.compare(lo, lo) == 0
    # a strict total order: ranks are all distinct and cover 0..4
    assert sorted(graded.rank(g) for g in chain) == [0, 1, 2, 3, 4]


def test_mandub_is_supererogatory_and_it_is_the_only_one():
    # beyond duty: permitted, praiseworthy to do, not blameworthy to omit.
    assert graded.is_supererogatory(graded.GRADE_MANDUB)
    assert graded.is_praiseworthy_to_do(graded.GRADE_MANDUB)
    assert not graded.is_blameworthy_to_omit(graded.GRADE_MANDUB)
    # wājib is praiseworthy to do too, but omitting it *is* a breach — a duty,
    # not supererogation.
    assert graded.is_blameworthy_to_omit(graded.GRADE_WAJIB)
    assert not graded.is_supererogatory(graded.GRADE_WAJIB)
    # mandūb is the unique supererogatory grade
    supererog = [g for g in graded.GRADED_SCALE if graded.is_supererogatory(g)]
    assert supererog == [graded.GRADE_MANDUB]


def test_wajib_vs_haram_is_a_hard_clash_delegated_to_the_base_operators():
    assert graded.graded_clashes(graded.GRADE_WAJIB, graded.GRADE_HARAM)
    # and it is exactly the base O/F clash, not a new rule
    assert operators.clashes(operators.OP_OBLIGATION, operators.OP_PROHIBITION)
    assert graded.graded_clashes(graded.GRADE_HARAM, graded.GRADE_WAJIB)  # symmetric


def test_mandub_vs_makruh_is_a_soft_tension_not_a_hard_clash():
    # both project to P; clashes(P, P) is False — a valence tension, not a clash.
    assert not graded.graded_clashes(graded.GRADE_MANDUB, graded.GRADE_MAKRUH)
    assert not operators.clashes(operators.OP_PERMISSION, operators.OP_PERMISSION)
    # same grade never clashes with itself either
    for g in graded.GRADED_SCALE:
        assert not graded.graded_clashes(g, g)


def test_predicates_and_projection_helpers():
    assert graded.is_obligatory(graded.GRADE_WAJIB)
    assert graded.is_forbidden(graded.GRADE_HARAM)
    assert graded.is_discouraged(graded.GRADE_MAKRUH)
    assert not graded.is_obligatory(graded.GRADE_MANDUB)
    # base name/gloss delegate to the consumed base operators
    assert graded.base_name(graded.GRADE_WAJIB) == operators.name(operators.OP_OBLIGATION)
    assert graded.base_gloss(graded.GRADE_HARAM) == operators.gloss(operators.OP_PROHIBITION)


def test_aliases_normalize_to_canonical_grades():
    assert graded.normalize("Fard") == graded.GRADE_WAJIB
    assert graded.normalize("mustahabb") == graded.GRADE_MANDUB
    assert graded.normalize(" HARAM ") == graded.GRADE_HARAM
    assert graded.normalize("not-a-grade") == ""
    assert graded.is_grade("sunna") and not graded.is_grade("obligatory")


def test_unknown_grades_are_inert_never_clash_never_project():
    assert graded.project("nope") == ""
    assert graded.rank("nope") == -1
    assert graded.valence("nope") == 0
    assert not graded.graded_clashes("nope", graded.GRADE_HARAM)
    with pytest.raises(ValueError, match="unknown deontic grade"):
        graded.compare("nope", graded.GRADE_WAJIB)


def test_scale_does_not_shadow_or_mutate_the_base_triad():
    # The extension sits beside the triad: the base module is untouched.
    assert operators.VALID_OPERATORS == ("O", "P", "F")
    # graded clash is a pure delegation — it agrees with base clashes on projections
    for a, b in itertools.product(graded.GRADED_SCALE, repeat=2):
        assert graded.graded_clashes(a, b) == operators.clashes(
            graded.project(a), graded.project(b))


def test_describe_is_a_flat_audit_record():
    d = graded.describe(graded.GRADE_MANDUB)
    assert d["grade"] == "mandub"
    assert d["operator"] == "P"
    assert d["valence"] == 1
    assert d["supererogatory"] is True
    assert d["base_gloss"] == "permitted"
