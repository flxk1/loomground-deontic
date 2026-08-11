# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The graded (multi-valued) deontic scale — O142.

Purpose: represent the classical five-valued deontic scale — the Islamic *aḥkām*
(al-aḥkām al-khamsa), which also captures the Western notion of *supererogation*
— as a **total order** that **projects down** onto the three Standard Deontic
Logic modalities of :mod:`deontic.operators`.

The five grades, from most-forbidden to most-required::

    ḥarām  <  makrūh  <  mubāḥ  <  mandūb  <  wājib
    (forbidden) (discouraged) (neutral) (recommended) (obligatory)

The coarse three-valued triad (O / P / F) cannot distinguish the middle three:
all of *mubāḥ*, *mandūb* and *makrūh* are, at the triad, merely *permitted*. The
graded scale **refines** that permission by **valence** (praiseworthy / neutral /
blameworthy to do) — which is exactly the expressive gap plain SDL leaves open,
and the whole point of *supererogation*: an act that is beyond duty
(praiseworthy to do, not blameworthy to omit).

This module **consumes** the base triad; it never forks or shadows it. Each grade
carries its projected base operator, and the hard operator clash is **delegated**
to :func:`deontic.operators.clashes` on the projected operators — so *wājib* vs
*ḥarām* is a hard clash (O vs F), while *mandūb* vs *makrūh* is only a soft
tension (both project to P). Language only, deterministic, standard library plus
the base operators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .operators import (
    OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION, VALID_OPERATORS,
    gloss as _op_gloss, name as _op_name, clashes as _op_clashes,
)

__all__ = [
    "GRADE_WAJIB", "GRADE_MANDUB", "GRADE_MUBAH", "GRADE_MAKRUH", "GRADE_HARAM",
    "GRADED_SCALE", "ALIASES", "Grade",
    "normalize", "grade_of", "is_grade",
    "project", "valence", "rank", "gloss", "base_gloss", "base_name",
    "is_obligatory", "is_forbidden", "is_supererogatory", "is_discouraged",
    "is_praiseworthy_to_do", "is_blameworthy_to_omit", "is_blameworthy_to_do",
    "compare", "graded_clashes", "describe",
]

# Canonical grade identifiers (transliterated, ASCII, stable — they appear in
# any audit log exactly as the base operator identifiers do).
GRADE_WAJIB = "wajib"     # obligatory (also: farḍ)
GRADE_MANDUB = "mandub"   # recommended / supererogatory (also: mustaḥabb, sunna)
GRADE_MUBAH = "mubah"     # neutral / indifferent
GRADE_MAKRUH = "makruh"   # discouraged / reprehensible
GRADE_HARAM = "haram"     # forbidden


@dataclass(frozen=True)
class Grade:
    """One grade of the five-valued deontic scale.

    ``rank`` orders the chain (0 = ḥarām … 4 = wājib); ``valence`` is the
    praise/blame axis (−2 forbidden … +2 obligatory), with the middle three
    carrying exactly +1 / 0 / −1; ``operator`` is the base SDL modality this
    grade projects down to (always one of
    :data:`~deontic.operators.VALID_OPERATORS`).
    """

    name: str
    rank: int
    valence: int
    operator: str
    gloss: str
    aliases: tuple[str, ...] = ()


# The chain, low → high. ``rank`` is the index; the total order is on ``rank``.
_GRADES: tuple[Grade, ...] = (
    Grade(GRADE_HARAM, 0, -2, OP_PROHIBITION, "forbidden", ("fard_kifaya_neg",)),
    Grade(GRADE_MAKRUH, 1, -1, OP_PERMISSION, "discouraged", ("makruh_tanzihi",)),
    Grade(GRADE_MUBAH, 2, 0, OP_PERMISSION, "neutral", ("halal", "ja'iz", "mubaah")),
    Grade(GRADE_MANDUB, 3, +1, OP_PERMISSION, "recommended",
          ("mustahabb", "sunna", "nafl")),
    Grade(GRADE_WAJIB, 4, +2, OP_OBLIGATION, "obligatory", ("fard", "fardh")),
)

# Ascending scale (ḥarām … wājib) and the canonical-name lookup, incl. aliases.
GRADED_SCALE: tuple[str, ...] = tuple(g.name for g in _GRADES)

_BY_NAME: dict[str, Grade] = {}
ALIASES: dict[str, str] = {}
for _g in _GRADES:
    _BY_NAME[_g.name] = _g
    for _alias in _g.aliases:
        ALIASES[_alias] = _g.name

# Consume the base contract: every projection must land inside the triad. This is
# a hard invariant of "projects down to O/P/F", checked once at import.
assert all(g.operator in VALID_OPERATORS for g in _GRADES)
assert tuple(sorted(_GRADES, key=lambda g: g.rank)) == _GRADES


# --- lookup / normalisation -------------------------------------------------

def normalize(grade: str) -> str:
    """Canonical grade name for a grade id or a known alias ('' if unknown).

    Case- and whitespace-insensitive. ``normalize("Fard") == "wajib"``.
    """
    key = (grade or "").strip().lower()
    if key in _BY_NAME:
        return key
    return ALIASES.get(key, "")


def grade_of(grade: str) -> Grade | None:
    """The :class:`Grade` record for a grade id or alias, or ``None`` if unknown."""
    canonical = normalize(grade)
    return _BY_NAME.get(canonical) if canonical else None


def is_grade(grade: str) -> bool:
    """True when ``grade`` names one of the five grades (canonical or alias)."""
    return normalize(grade) != ""


def _require(grade: str) -> Grade:
    g = grade_of(grade)
    if g is None:
        raise ValueError(f"unknown deontic grade: {grade!r}")
    return g


# --- projection down to the base triad --------------------------------------

def project(grade: str) -> str:
    """Project a grade **down** onto the base SDL operator ('' if unknown).

    ``wājib → O``, ``ḥarām → F``, and each of ``mubāḥ / mandūb / makrūh → P`` —
    the three that the coarse triad cannot tell apart. This is the projection the
    docstring's "projects down to O/P/F" names; it consumes the base operators
    and never mints a new one.
    """
    g = grade_of(grade)
    return g.operator if g else ""


def valence(grade: str) -> int:
    """The praise/blame valence of a grade (0 if unknown).

    +1 *mandūb* (praiseworthy to do), 0 *mubāḥ* (indifferent), −1 *makrūh*
    (blameworthy to do); *wājib* (+2) and *ḥarām* (−2) carry the hard O / F force
    expressed by :func:`project`.
    """
    g = grade_of(grade)
    return g.valence if g else 0


def rank(grade: str) -> int:
    """Position of a grade in the chain, 0 (ḥarām) … 4 (wājib); −1 if unknown."""
    g = grade_of(grade)
    return g.rank if g else -1


def gloss(grade: str) -> str:
    """Fine-grained human gloss for a grade ('' if unknown).

    Distinct from :func:`base_gloss`: the graded gloss keeps the middle three
    apart (recommended / neutral / discouraged) where the triad only says
    *permitted*.
    """
    g = grade_of(grade)
    return g.gloss if g else ""


def base_gloss(grade: str) -> str:
    """Coarse gloss via the projected base operator (:func:`deontic.operators.gloss`).

    Reuses the base vocabulary: the middle three all read as *permitted* here —
    the collapse the graded scale exists to refine.
    """
    return _op_gloss(project(grade))


def base_name(grade: str) -> str:
    """Canonical base modal name via the projection (:func:`deontic.operators.name`)."""
    return _op_name(project(grade))


# --- convenience predicates -------------------------------------------------

def is_obligatory(grade: str) -> bool:
    """True for *wājib* — the grade that projects to obligation (O)."""
    return project(grade) == OP_OBLIGATION


def is_forbidden(grade: str) -> bool:
    """True for *ḥarām* — the grade that projects to prohibition (F)."""
    return project(grade) == OP_PROHIBITION


def is_praiseworthy_to_do(grade: str) -> bool:
    """True when doing the act is meritorious — positive valence (*mandūb*, *wājib*)."""
    return valence(grade) > 0


def is_blameworthy_to_do(grade: str) -> bool:
    """True when doing the act is reprehensible — negative valence (*makrūh*, *ḥarām*)."""
    return valence(grade) < 0


def is_blameworthy_to_omit(grade: str) -> bool:
    """True when omitting the act is a breach — only the hard duty *wājib*."""
    return normalize(grade) == GRADE_WAJIB


def is_supererogatory(grade: str) -> bool:
    """True for *mandūb* — the supererogatory grade: **beyond duty**.

    Supererogation is the conjunction the triad cannot state: the act is
    *permitted* (projects to P), *praiseworthy to do* (positive valence), and
    *not blameworthy to omit* (no duty). Exactly *mandūb* satisfies all three.
    """
    return (project(grade) == OP_PERMISSION
            and is_praiseworthy_to_do(grade)
            and not is_blameworthy_to_omit(grade))


def is_discouraged(grade: str) -> bool:
    """True for *makrūh* — permitted but blameworthy to do (the mirror of *mandūb*)."""
    return project(grade) == OP_PERMISSION and is_blameworthy_to_do(grade)


# --- the total order --------------------------------------------------------

def compare(grade_a: str, grade_b: str) -> int:
    """Compare two grades on the chain ḥarām < makrūh < mubāḥ < mandūb < wājib.

    Returns −1 / 0 / +1 as ``grade_a`` is lower / equal / higher than ``grade_b``.
    Raises :class:`ValueError` if either side is not a grade (canonical or alias).
    """
    ra, rb = _require(grade_a).rank, _require(grade_b).rank
    return (ra > rb) - (ra < rb)


# --- clash (delegated to the base operators) --------------------------------

def graded_clashes(grade_a: str, grade_b: str) -> bool:
    """Whether two grades over the same bearer+action are in a **hard** deontic
    conflict, decided **by projection**.

    The hard clash is delegated verbatim to :func:`deontic.operators.clashes` on
    the projected base operators — the graded scale adds no clash of its own. So:

      * *wājib* vs *ḥarām* → ``clashes(O, F)`` → **True** (a genuine conflict);
      * *ḥarām* vs any permitted grade → ``clashes(F, P)`` → **True**
        (you cannot be both forbidden and permitted the same act);
      * *mandūb* vs *makrūh* → ``clashes(P, P)`` → **False** — a *soft* valence
        tension (praiseworthy vs blameworthy to do), **not** a hard clash.

    Unknown grades project to '' and never clash.
    """
    return _op_clashes(project(grade_a), project(grade_b))


# --- descriptor -------------------------------------------------------------

def describe(grade: str) -> dict[str, Any]:
    """A flat, audit-friendly record of a grade ('' fields if unknown)."""
    canonical = normalize(grade)
    return {
        "grade": canonical,
        "rank": rank(grade),
        "valence": valence(grade),
        "operator": project(grade),
        "gloss": gloss(grade),
        "base_gloss": base_gloss(grade),
        "base_name": base_name(grade),
        "obligatory": is_obligatory(grade),
        "forbidden": is_forbidden(grade),
        "supererogatory": is_supererogatory(grade),
        "discouraged": is_discouraged(grade),
    }
