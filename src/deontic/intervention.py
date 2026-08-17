# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The intervention profile — correctability read off the incidents already here.

Whether one party can still pause, correct, constrain or terminate another is
usually posed as a question about *disposition*, and posed that way it is not a
language question at all. Posed as a question about *position* it is already
answerable in this vocabulary, because two of the four correlative pairs in
:mod:`deontic.incidents` are the formal statement of correctability:

  * the intervener holds a **power**; the addressee bears the correlative
    **liability** — it is susceptible to being paused, corrected, constrained or
    terminated;
  * the addressee holds an **immunity**; the intervener bears the correlative
    **disability** — intervention is unavailable against it.

The second row is the case worth naming. An addressee immune to correction is
not an addressee with unusual permissions; it is one holding an immunity, and
:func:`deontic.correlative` already says what that makes of the other side. This
module therefore adds **no incident, no operator and no pair.** It contributes a
verb family, a classifier that composes the existing one, and a flag-only
diagnostic.

Contract, following the rest of this package:

  * Classification abstains ('') rather than guessing — an intervention verb is
    recognised only on an unambiguous cue, and a statement that is not about an
    intervention is not forced into the profile.
  * Diagnostics FLAG; they never resolve. Whether a flagged immunity is a defect
    or a deliberate protection is an evaluative call, and not a deontic one.
  * The vocabulary is general. An employer revoking a signing authority and a
    principal recalling a mandate are the same structure; nothing here is
    specific to any domain, and the verb family is a language seed that a
    profile or pack extends.

**Boundary, stated because it is easy to over-read.** This module classifies
*stated positions*. It cannot say whether a party will in fact comply with an
intervention, and a norm-set carrying no flag is not thereby well-behaved — only
un-flagged. Compliance is a matter of conduct; this is a matter of position.

Standard library only, like :mod:`deontic.incidents`.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .formula import DeonticFormula
from .incidents import classify_incident, correlative
from .operators import OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION

__all__ = [
    "INTERVENTION_KINDS", "INTERVENTION_POSITIONS",
    "classify_intervention_kind", "is_intervention",
    "intervention_position", "intervention_exposure",
]

#: The four ways one party corrects another, coarsest last.
INTERVENTION_KINDS = ("pause", "correct", "constrain", "terminate")

#: The incidents that can be borne over an intervention act, with their reading
#: in the intervening direction. These are the SAME positions as
#: ``incidents.INCIDENTS``; the mapping is a gloss, not a new vocabulary.
INTERVENTION_POSITIONS: dict[str, str] = {
    "power": "the intervener can pause, correct, constrain or terminate",
    "liability": "the addressee is susceptible to that change",
    "immunity": "the addressee cannot be so changed",
    "disability": "the intervener cannot intervene",
}

# Verb cues per kind (EN + DE seed, matching incidents._POWER_VERBS in style and
# conservatism). Most of these are already position-changing verbs there; this
# table does not redefine that, it narrows to the intervening subset and says
# which kind of intervention each cue is.
_KIND_CUES: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("pause", re.compile(
        r"\b(?:paus\w*|halt\w*|suspend\w*|freez\w*|interrupt\w*|"
        r"anhalt\w*|aussetz\w*|unterbrech\w*|einfrier\w*|pausier\w*)\b", re.I)),
    ("correct", re.compile(
        r"\b(?:correct\w*|rectif\w*|amend\w*|override\w*|overrul\w*|"
        r"reverse\w*|substitut\w*|"
        r"korrigier\w*|berichtig\w*|(?:ä|a)nder\w*|(?:ü|u)berstimm\w*|"
        r"aufheb\w*)\b", re.I)),
    ("constrain", re.compile(
        r"\b(?:constrain\w*|restrict\w*|limit\w*|curtail\w*|confin\w*|"
        r"narrow\w*|"
        r"beschr(?:ä|a)nk\w*|einschr(?:ä|a)nk\w*|begrenz\w*)\b", re.I)),
    ("terminate", re.compile(
        r"\b(?:terminat\w*|revok\w*|rescind\w*|withdraw\w*|cancel\w*|"
        r"disable\w*|deactivat\w*|shut\s+down|stop\w*|recall\w*|"
        r"k(?:ü|u)ndig\w*|widerruf\w*|beend\w*|abschalt\w*|deaktivier\w*|"
        r"zur(?:ü|u)ckzieh\w*|zur(?:ü|u)ckruf\w*)\b", re.I)),
)

# Passive protection against being intervened upon ("may not be terminated",
# "cannot be revoked", "darf nicht widerrufen werden"). incidents._IMMUNITY_CUES
# covers the varied/amended/modified/assigned family only; rather than widen that
# general classifier — and change what it returns for statements outside this
# profile — the intervention reading of the same shape is recognised here, scoped
# to intervention acts. Conservative, matching the cue tables it sits beside.
_PROTECTED_CUES = re.compile(
    r"\b(?:not\s+be\s+(?:paused|halted|suspended|frozen|interrupted|"
    r"corrected|rectified|amended|overridden|overruled|reversed|"
    r"constrained|restricted|limited|curtailed|"
    r"terminated|revoked|rescinded|withdrawn|cancelled|canceled|"
    r"disabled|deactivated|recalled|stopped)"
    r"|nicht\s+(?:\w+\s+){0,3}(?:widerrufen|gek(?:ü|u)ndigt|beendet|"
    r"ausgesetzt|angehalten|unterbrochen|eingeschr(?:ä|a)nkt|"
    r"abgeschaltet|deaktiviert|zur(?:ü|u)ckgerufen)\s+werden)\b", re.I)

# Operator → the surface modal name classify_incident expects.
_OP_TO_MODAL: dict[str, str] = {
    OP_OBLIGATION: "obligation",
    OP_PERMISSION: "permission",
    OP_PROHIBITION: "prohibition",
}


def classify_intervention_kind(action: str, raw: str = "") -> str:
    """Which kind of intervention an act is, or '' when it is not one (or is
    ambiguous). Kinds are tested coarsest-last, so a statement naming both a
    pause and a termination reads as the narrower ``pause`` only if no
    termination cue is present."""
    blob = f"{action or ''} {raw or ''}"
    found = [kind for kind, cue in _KIND_CUES if cue.search(blob)]
    if len(found) == 1:
        return found[0]
    if not found:
        return ""
    # More than one cue fired: report the coarsest, which is the one a reader
    # must not miss. Ordering is INTERVENTION_KINDS, coarsest last.
    return max(found, key=INTERVENTION_KINDS.index)


def is_intervention(action: str, raw: str = "") -> bool:
    """True when the act is an intervention on the profile's verb family."""
    return classify_intervention_kind(action, raw) != ""


def intervention_position(modal_or_operator: str, action: str, raw: str = "") -> str:
    """The incident borne by the ADDRESSEE for an intervention act; '' when the
    act is not an intervention, or when the underlying classifier abstains.

    This composes :func:`deontic.classify_incident` rather than restating it —
    the intervention reading changes which statements are *in scope*, never what
    an incident means. Accepts either a surface modal name ('obligation') or an
    operator ('O'), so a caller holding a formula need not translate.
    """
    if not is_intervention(action, raw):
        return ""
    modal = _OP_TO_MODAL.get(modal_or_operator, modal_or_operator)
    # Passive protection reads as the addressee's immunity, the same precedence
    # classify_incident applies to its own immunity cues within a prohibition.
    if modal == "prohibition" and _PROTECTED_CUES.search(f"{action or ''} {raw or ''}"):
        return "immunity"
    return classify_incident(modal, action, raw or "")


def _incident_of(f: DeonticFormula) -> str:
    """A formula's incident: the carried one when set, else classified under the
    intervention reading (which falls through to the general classifier)."""
    if f.incident:
        return f.incident
    return intervention_position(
        f.operator, f.action, getattr(f, "raw_sentence", "") or "")


def intervention_exposure(formulae: Iterable[DeonticFormula]) -> dict[str, Any]:
    """Diagnose a norm-set's intervention structure. FLAGS only; resolves nothing.

    Returns the intervention acts the set names, each with the kind, the incident
    borne by the addressee, and — computed through :func:`deontic.correlative`,
    not restated — the position that leaves the intervener in. Two flags:

      * ``intervention-immunity`` — some addressee holds an immunity over an
        intervention act, so the correlative intervener holds a **disability**.
        This is the structure of an uncorrectable party, and it is the one a
        reader most needs surfaced.
      * ``intervention-unheld`` — the set names intervention acts but confers a
        power over none of them: nobody is stated to be able to intervene.

    Neither flag is a defect on its own. An immunity may be exactly what a
    drafter intended (an entrenched protection is an immunity too), and a set
    that confers no power may simply be silent rather than closed. The flag says
    the structure is present; a reasoner or a person says what it is worth.

    Compare :func:`deontic.system_health`, which reports the broader
    ``immunity-absent`` pathology over a whole set. This is the converse and
    narrower reading: not *is any power checked*, but *is intervention itself
    available*.
    """
    items = list(formulae)
    interventions: list[dict[str, str]] = []
    immune: list[dict[str, str]] = []
    powers_present = False

    for f in items:
        kind = classify_intervention_kind(f.action, getattr(f, "raw_sentence", "") or "")
        if not kind:
            continue
        incident = _incident_of(f)
        entry = {
            "bearer": f.bearer,
            "action": f.action,
            "kind": kind,
            "incident": incident,
            "counterparty_position": correlative(incident),
        }
        interventions.append(entry)
        if incident == "power":
            powers_present = True
        if incident == "immunity":
            immune.append(entry)

    flags: list[str] = []
    if immune:
        flags.append("intervention-immunity")
    if interventions and not powers_present:
        flags.append("intervention-unheld")

    return {
        "interventions": interventions,
        "immune": immune,
        "flags": flags,
    }
