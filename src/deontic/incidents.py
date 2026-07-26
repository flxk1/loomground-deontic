# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The Hohfeldian incidents — the jurisdiction-neutral layer beneath the modals.

Purpose: the eight fundamental jural positions in four correlative pairs, the
relations over them (jural correlative, jural opposite), and the deterministic
classifiers that read an incident from a norm's modal + surface. Pure language:
no statute is cited; the cue tables are the concept vocabulary every legal order
uses for these moves.

Contract:

  * The eight incidents and their pairings are fixed vocabulary
    (see artifacts/vocabulary/incidents.json — this module is the code mirror).
  * Classification abstains ('') rather than guessing. A misclassified incident
    would misstate who owes what, so unambiguous cues only.
  * Classification returns the incident borne by the norm-ADDRESSEE. The
    counterparty's position is its jural :func:`correlative`.

This module imports only the standard library. The facet-enrichment adapter that
mutates extracted rule objects in place is deliberately not here — it couples to
the surface extractor and stays in the reasoning layer.
"""

from __future__ import annotations

import re
from typing import Iterable

__all__ = [
    "INCIDENTS", "correlative", "opposite", "is_advantage",
    "classify_incident", "extract_counterparty", "classify_condition_kind",
]

# The eight positions, advantage side first in each pair.
INCIDENTS = (
    "claim", "duty",          # claim ↔ duty
    "privilege", "no-right",  # privilege (liberty) ↔ no-right
    "power", "liability",     # power ↔ liability
    "immunity", "disability",  # immunity ↔ disability
)

# Jural correlatives: the counterparty's position over the same act.
_CORRELATIVE: dict[str, str] = {
    "claim": "duty", "duty": "claim",
    "privilege": "no-right", "no-right": "privilege",
    "power": "liability", "liability": "power",
    "immunity": "disability", "disability": "immunity",
}

# Jural opposites: the negation of a position for the same party.
_OPPOSITE: dict[str, str] = {
    "claim": "no-right", "no-right": "claim",
    "duty": "privilege", "privilege": "duty",
    "power": "disability", "disability": "power",
    "immunity": "liability", "liability": "immunity",
}

_ADVANTAGE = frozenset({"claim", "privilege", "power", "immunity"})


def correlative(incident: str) -> str:
    """The counterparty's jural correlative of an incident ('' if unknown)."""
    return _CORRELATIVE.get(incident, "")


def opposite(incident: str) -> str:
    """The jural opposite of an incident for the same party ('' if unknown)."""
    return _OPPOSITE.get(incident, "")


def is_advantage(incident: str) -> bool:
    """True for the advantage side of a pair (claim/privilege/power/immunity)."""
    return incident in _ADVANTAGE


# --- deterministic classification -------------------------------------------

# Verbs whose exercise alters the parties' legal positions — the signature of a
# POWER. Concept words (EN + DE seed; language profiles and packs extend).
_POWER_VERBS = re.compile(
    r"\b(?:terminat\w*|rescind\w*|revoke\w*|withdraw\w*|waive\w*|"
    r"consent\w*|approv\w*|authoris\w*|authoriz\w*|assign\w*|"
    r"renew\w*|exercis\w*|elect\w*|suspend\w*|instruct\w*|"
    r"k(?:ü|u)ndig\w*|widerruf\w*|zur(?:ü|u)cktret\w*|verzicht\w*|"
    r"zustimm\w*|genehmig\w*|abtret\w*|verl(?:ä|a)nger\w*|aus(?:ü|u)b\w*|"
    r"anweis\w*)\b", re.I)

# Immunity signature: protection against another's unilateral change of
# positions ("may not be varied/amended/assigned except…"). Conservative.
_IMMUNITY_CUES = re.compile(
    r"\b(?:not\s+be\s+(?:varied|amended|modified|assigned)|"
    r"nicht\s+(?:ge(?:ä|a)ndert|abgetreten|(?:ü|u)bertragen)\s+werden)\b", re.I)

_SUSPENSIVE_CUES = re.compile(
    r"^\s*(?:if|where|when|provided\s+that|subject\s+to|in\s+the\s+event|"
    r"upon|wenn|falls|sofern|soweit|im\s+falle)\b", re.I)
# Resolutive (condition subsequent) cues. "until <…> revoked/terminated/…" allows
# a few intervening words so "until the licence is revoked" is caught, not only
# the bare "until revoked". Still verb-anchored — a bare temporal "until X" stays
# an abstention (the classifier marks only unambiguous resolutive phrasing).
_RESOLUTIVE_CUES = re.compile(
    r"\b(?:until\s+(?:\w+\s+){0,5}(?:revoked|terminated|rescinded|withdrawn|"
    r"expires?|expired|cancelled|canceled)"
    r"|condition\s+subsequent|aufl(?:ö|o)send"
    r"|bis\s+auf\s+widerruf"
    r"|bis\s+(?:\w+\s+){0,5}(?:widerrufen|beendet|aufgehoben))\b", re.I)


def classify_incident(modal: str, action: str, raw: str) -> str:
    """The incident borne by the norm-addressee; abstains ('') when unsure.

    An obligation places a duty on the addressee (correlative: the obligee's
    claim). A prohibition of conduct is likewise a duty ("must not disclose");
    a prohibition of the exercise of a power removes that power — a disability
    ("may not assign/terminate"); passive no-variation phrasing protects the
    other side — an immunity. A permission/right is a privilege (liberty), or a
    power when its verb changes legal positions.
    """
    blob = f"{action} {raw}"
    if modal == "obligation":
        return "duty"
    if modal == "prohibition":
        if _IMMUNITY_CUES.search(blob):
            return "immunity"
        if _POWER_VERBS.search(blob):
            return "disability"
        return "duty"
    if modal in ("permission", "right"):
        return "power" if _POWER_VERBS.search(blob) else "privilege"
    return ""


def extract_counterparty(action: str, raw: str, roles: Iterable[str]) -> str:
    """The correlative role when the norm names it — the claim-holder of a duty,
    the party exposed to a power. First role found in the action (preferred)
    then the sentence; '' when none (abstention, not 'unknown')."""
    for scope in (action, raw):
        low = " " + re.sub(r"[^a-zäöüß-]+", " ", (scope or "").lower()) + " "
        for role in sorted(roles, key=len, reverse=True):
            if f" {role} " in low or f" {role.replace('-', ' ')} " in low:
                return role
    return ""


def classify_condition_kind(condition: str) -> str:
    """suspensive | resolutive | '' (abstain). Marked only on unambiguous cues —
    a misclassified condition kind flips a norm's life cycle, which is
    silently-wrong territory."""
    c = (condition or "").strip()
    if not c:
        return ""
    if _RESOLUTIVE_CUES.search(c):
        return "resolutive"
    if _SUSPENSIVE_CUES.match(c):
        return "suspensive"
    return ""
