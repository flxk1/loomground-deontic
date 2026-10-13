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
#
# Word-anchored to explicit finite-verb forms rather than a stem+\w* wildcard
# wherever the bare stem's wildcard suffix also spells an unrelated common
# noun or adjective, so the derived noun/adjective form never matches:
# elect\w* matched "electronic"/"election"/"elector"/"electoral";
# withdraw\w* matched "withdrawal"; waive\w* matched "waiver"; approv\w*
# matched "approval"; authoris\w*/authoriz\w* matched "authorisation"/
# "authorization"; assign\w* matched "assignment"/"assignable"; renew\w*
# matched "renewal"; instruct\w* matched "instruction(s)"/"instructor".
# "authorised"/"authorized" is additionally excluded immediately before
# "representative(s)": the GDPR/NIS2 defined term ("an authorised
# representative") names a role, not an exercised power.
#
# Left unchanged, checked and found with no such collision: terminat\w*,
# rescind\w*, revoke\w*, consent\w*, suspend\w* ("terminal", "rescission",
# "revocation", "consensus", "suspension" all diverge from the verb stem
# before the shared prefix runs out). exercis\w* is left unchanged on
# purpose: English "exercise" is the identical spelling for the noun and the
# verb (zero-derivation), so no word-anchoring can separate them. The German
# stems (k(ü|u)ndig.../widerruf.../zur(ü|u)cktret.../verzicht.../
# zustimm.../genehmig.../abtret.../verl(ä|a)nger.../aus(ü|u)b.../anweis...)
# are also left unchanged: German nominalises most of these verbs by adding
# "-ung" to the same stem (Kündigung, Zustimmung, Genehmigung, Abtretung,
# Verlängerung, Ausübung, Anweisung collide the same way), and two of them
# (widerruf, verzicht) are zero-derivation like "exercise" — the bare noun
# ("Widerruf", "Verzicht") IS the verb stem, so even restricting to
# verb-only suffixes would still match the bare noun via \w*'s zero-width
# option; a pre-existing, documented, out-of-scope issue.
_POWER_VERBS = re.compile(
    r"\b(?:terminat\w*|rescind\w*|revoke\w*|"
    r"withdraw(?:s|ing)?|withdrew|withdrawn|"
    r"waive|waives|waived|waiving|"
    r"consent\w*|"
    r"approve|approves|approved|approving|"
    r"authoris(?:e|es|ing|ed(?!\s+representatives?\b))|"
    r"authoriz(?:e|es|ing|ed(?!\s+representatives?\b))|"
    r"assign|assigns|assigned|assigning|"
    r"renew|renews|renewed|renewing|"
    r"exercis\w*|"
    r"elect|elects|elected|electing|"
    r"suspend\w*|"
    r"instruct|instructs|instructed|instructing|"
    r"k(?:ü|u)ndig\w*|widerruf\w*|zur(?:ü|u)cktret\w*|verzicht\w*|"
    r"zustimm\w*|genehmig\w*|abtret\w*|verl(?:ä|a)nger\w*|aus(?:ü|u)b\w*|"
    r"anweis\w*)\b", re.I)

# "require": a permission to require something of another party is a
# Hohfeldian power ("The lender may require the borrower to provide
# additional security." -> power). It is deliberately NOT a _POWER_VERBS
# regex alternative: ONLY the active forms "require"/"requires"/"requiring"
# count — never "required" in any form, since a passive or reduced-relative
# "required" ("as required under Article 6", "information required to
# assess compliance", "the measures it considers required") would otherwise
# false-positive on real text, and there is no reliable surface cue that
# tells an active past-tense "required" apart from a passive one. Checked
# ONLY against `action`, never the whole raw sentence: a "require"/"requires"
# elsewhere in the sentence (a condition, a different clause) must not turn
# an unrelated permission into a power.
_REQUIRE_FORMS = frozenset({"require", "requires", "requiring"})
_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def _has_active_require(text: str) -> bool:
    """True iff ``text`` contains "require"/"requires"/"requiring". Scope
    this to the `action` text only; never the whole raw sentence."""
    words = {w.lower() for w in _WORD_RE.findall(text or "")}
    return bool(words & _REQUIRE_FORMS)

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
        if _POWER_VERBS.search(blob) or _has_active_require(action):
            return "disability"
        return "duty"
    if modal in ("permission", "right"):
        return "power" if (_POWER_VERBS.search(blob) or _has_active_require(action)) else "privilege"
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
