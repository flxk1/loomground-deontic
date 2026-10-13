# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The permission modal cue list ("is entitled to" / "is authorised to") did
not carry the "shall be" forms real EU legislation also uses: "The Digital
Services Coordinator ... shall be entitled to ..." (DSA Art. 60(4)) and "The
Commission shall be empowered to adopt delegated acts ..." (GDPR Art. 12(8))
matched the bare obligation lexeme "shall" at the earliest token position and
read as O, not P.

Fix: "shall be entitled to" / "are entitled to" / "shall be empowered to" /
"shall be authorised to" / "shall be authorized to" / "shall have the power
to" are now modal_lexemes.json entries mapped to the plain "may" lexeme (the
same route "is entitled to" already takes) — the parser's own longest-match-
first dispatch at the modal's own start position already prefers the longer
phrase over the bare "shall" at that same position, so no separate ordering
rule is needed once the phrase is published. Each of these six also carries
"requires_verb_complement": true: the match is only accepted when the word
right after it is, case-insensitively, a member of a closed POSITIVE list of
base-form verbs (artifacts/gazetteer/complement_verbs.json, derived from the
digital-law corpus — see that file's own describes field) — a determiner
lead ("shall be authorised to THE EXTENT that ..."), a bare noun or
adjective complement ("are entitled to COMPENSATION", "shall be entitled to
FAIR compensation", "shall be entitled to PAID annual leave"), a gerund
("shall be entitled to RECEIVING compensation" — not the bare verb
"receive"), and a possessive lead ("shall have the power to ITS own
investigative powers") are all rejected by the SAME check, since none of
them is spelled exactly like a listed verb. A single bare verb is enough on
its own ("shall have the power to INTERVENE.", "are entitled to OBJECT."):
no minimum complement length is imposed. When the check fails the parser
falls back to the shorter alternative at that same position, which then
abstains on its own terms exactly as it did before these six phrases
existed — never a NEW accepted frame base did not have.

"empower"/"empowers"/"empowered"/"empowering" and the phrase alternative
"(?:have|has) the power to" are new deontic.incidents power-verb cues
(mirrored into extraction.json and the bundled skill engine) so "shall be
empowered to"/"shall have the power to" read as a Hohfeldian power
regardless of which verb follows (adopt, order, impose, require, ...), not
only a bare permission; "authorised to"/"authorized to" already reached
power through the pre-existing authoris/authoriz cues, and "entitled to"
carries no power-verb cue of its own and stays a privilege.

    python -m pytest tests/test_entitled_cues.py
"""
from __future__ import annotations

import pytest

from deontic import incidents, prose_grammar

_MODAL_TO_OP = {"obligation": "O", "permission": "P", "prohibition": "F"}
_OP_TO_MODAL = {"O": "obligation", "P": "permission", "F": "prohibition"}


# ── the operator misread: bare "shall" must not win over the longer phrase ──
@pytest.mark.parametrize("sentence,bearer", [
    ("The Digital Services Coordinator of establishment shall be entitled "
     "to request any information necessary for the performance of its "
     "tasks.", "Digital Services Coordinator of establishment"),
    ("The Commission shall be empowered to adopt delegated acts in order to "
     "supplement this Regulation.", "Commission"),
    ("The supervisory authority shall be authorised to conduct an "
     "investigation.", "supervisory authority"),
    ("The authority shall be authorized to issue a fine.", "authority"),
    ("Member States are entitled to adopt additional measures.",
     "Member States"),
])
def test_shall_be_entitled_forms_read_as_permission_not_obligation(sentence, bearer):
    # Before this fix, every one of these sentences read operator == "O"
    # (the bare "shall"; "are entitled to" produced no modal match at all)
    # instead of "P".
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"
    assert frame.bearer == bearer


def test_bare_shall_without_a_permission_cue_is_still_obligation():
    # The fix must not swallow an ordinary obligation: "shall" alone, with
    # no "entitled"/"empowered"/"authorised"/"power" phrase following, still
    # reads O.
    frame = prose_grammar.analyze("The controller shall notify the authority.")
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "O"


# ── "shall have the power to": added because a probe shows it is missed
#    otherwise (it previously read O/duty regardless of the governing verb) ─
def test_shall_have_the_power_to_reads_as_permission():
    frame = prose_grammar.analyze(
        "The national regulatory authority shall have the power to require "
        "compliance.")
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"


# ── the Hohfeldian incident for each new cue, the behaviour the published
#    describes fields state: "empowered to"/"have the power to" -> power;
#    "entitled to" -> privilege, regardless of the governing verb ────────
@pytest.mark.parametrize("sentence,expected_incident", [
    ("The Digital Services Coordinator of establishment shall be entitled "
     "to request any information necessary for the performance of its "
     "tasks.", "privilege"),
    ("The Commission shall be empowered to adopt delegated acts in order "
     "to supplement this Regulation.", "power"),
    ("The supervisory authority shall be authorised to conduct an "
     "investigation.", "power"),
    ("The authority shall be authorized to issue a fine.", "power"),
    ("The national regulatory authority shall have the power to require "
     "compliance.", "power"),
    ("Member States are entitled to adopt additional measures.", "privilege"),
])
def test_new_cues_classify_the_expected_hohfeld_incident(sentence, expected_incident):
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    modal = _OP_TO_MODAL[frame.operator]
    incident = incidents.classify_incident(modal, frame.action, sentence)
    assert incident == expected_incident


# "shall have the power to" must read as a power EVEN WHEN the governing
# verb itself is not a power_verb and is not an active "require" — a bare
# "require"-verb probe would mask this gap, since "require" is independently
# a power cue of its own.
@pytest.mark.parametrize("sentence", [
    "The national regulatory authority shall have the power to impose fines.",
    "The national regulatory authority shall have the power to order the "
    "controller to comply.",
    "The Commission shall have the power to adopt delegated acts.",
])
def test_shall_have_the_power_to_is_a_power_regardless_of_the_verb(sentence):
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"
    incident = incidents.classify_incident("permission", frame.action, sentence)
    assert incident == "power"
    assert "require" not in frame.action.lower()


# ── a determiner/clause-marker lead after "to" is a scope qualifier, not an
#    infinitival action: the new cues must not fire, and the sentence
#    abstains exactly as it does without the new cues published at all ────
@pytest.mark.parametrize("sentence", [
    "Processing shall be authorised to the extent that it is necessary "
    "for that purpose.",
    "The measure shall be authorised to that effect.",
])
def test_determiner_led_complement_is_not_an_infinitival_action(sentence):
    frame = prose_grammar.analyze(sentence)
    assert not frame.accepted
    assert frame.operator != "P"


# ── a multi-word NOUN phrase (no determiner at all) after "entitled to"/
#    "have the power to" is a claim-object, not a liberty/power to act —
#    the positive verb-list check rejects every one of them because their
#    first word is never spelled like a listed base-form verb; checking
#    only for a determiner/clause-marker lead or a single bare word would
#    not catch any of these ─────────────────────────────────────────────
@pytest.mark.parametrize("sentence", [
    "The data subject shall be entitled to fair compensation.",
    "Applicants are entitled to legal aid from the State.",
    "Data subjects are entitled to data portability.",
    "Workers shall be entitled to paid annual leave.",
    "Workers are entitled to equal treatment.",
    "The victims are entitled to full compensation.",
    "The data subject shall be entitled to reasonable fees.",
    "The data subject shall be entitled to information about the processing.",
    "The providers are entitled to compensation.",
    "Each supervisory authority shall have the power to its own "
    "investigative powers.",
    "The supervisory authority shall have the power to investigative powers.",
])
def test_noun_phrase_complement_abstains(sentence):
    frame = prose_grammar.analyze(sentence)
    assert frame.operator != "P"


# ── a gerund ("receiving") is not the bare verb form ("receive") an
#    infinitive complement requires — the sentence abstains, not a wrong P ─
def test_gerund_complement_abstains():
    frame = prose_grammar.analyze(
        "The data subject shall be entitled to receiving compensation.")
    assert frame.operator != "P"


def test_verb_object_after_entitled_to_still_reads_permission():
    frame = prose_grammar.analyze(
        "The data subject shall be entitled to receive compensation.")
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"
    assert frame.action == "receive compensation"


# ── a single bare verb is enough — no minimum complement length ───────────
@pytest.mark.parametrize("sentence,bearer", [
    ("The Member States shall have the power to intervene.", "Member States"),
    ("They are entitled to object.", "They"),
    ("The Member States shall be entitled to object.", "Member States"),
])
def test_single_word_verb_complement_reads_permission(sentence, bearer):
    # A complement check that imposed a minimum word count would fall back
    # to the bare obligation lexeme here and read O/duty instead of P; a
    # single listed verb ("intervene"/"object") is a complete action on
    # its own, with nothing else required to follow it.
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"
    assert frame.bearer == bearer


def test_single_word_verb_complement_power_incident():
    sentence = "The Member States shall have the power to intervene."
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    incident = incidents.classify_incident("permission", frame.action, sentence)
    assert incident == "power"


# ── "empower" is word-anchored against the noun "empowerment", the same way
#    authoris/authoriz are already anchored against "authorisation" ───────
def test_empowerment_noun_is_not_a_power_verb():
    assert incidents._POWER_VERBS.search("empowerment") is None


@pytest.mark.parametrize("verb", ["empower", "empowers", "empowered", "empowering"])
def test_empower_verb_forms_match(verb):
    assert incidents._POWER_VERBS.search(verb) is not None


@pytest.mark.parametrize("phrase", ["have the power to", "has the power to"])
def test_have_the_power_to_phrase_matches(phrase):
    assert incidents._POWER_VERBS.search(phrase) is not None


def test_engine_power_verb_cues_include_empower_and_match_package():
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "deontic"))
    import deontic_engine as eng  # noqa: E402
    assert eng._POWER_VERBS.pattern == incidents._POWER_VERBS.pattern
    for probe in ("empower", "empowers", "empowered", "empowering", "empowerment",
                  "have the power to", "has the power to"):
        assert bool(eng._POWER_VERBS.search(probe)) == bool(incidents._POWER_VERBS.search(probe))


# ── the gazetteer and extraction.json stay in sync (Gate F / Gate G / Gate H) ─
def test_new_modal_phrases_are_covered_by_extraction_json():
    import json
    import re
    from pathlib import Path

    ex = json.loads((Path(__file__).resolve().parent.parent / "src" / "deontic"
                      / "artifacts" / "extraction.json").read_text(encoding="utf-8"))
    pattern = next(c["pattern"] for c in ex["modal_cues"] if c["modal"] == "permission")
    for phrase in ("shall be entitled to", "are entitled to",
                   "shall be empowered to", "shall be authorised to",
                   "shall be authorized to", "shall have the power to"):
        assert re.search(pattern, phrase, re.I), phrase


# ── extraction.json carries the SAME verb-complement condition the parser
#    applies, so a plain, code-free consumer reaches the same answer ──────
def test_extraction_json_carries_the_complement_verb_cue():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    ex = json.loads((root / "src" / "deontic" / "artifacts" / "extraction.json")
                     .read_text(encoding="utf-8"))
    gaz = json.loads((root / "src" / "deontic" / "artifacts" / "gazetteer"
                       / "complement_verbs.json").read_text(encoding="utf-8"))
    cue = ex["complement_verb_cue"]
    assert set(cue["verbs"]) == set(gaz["verbs"])
    assert "intervene" in cue["verbs"]
    assert "reopen" in cue["verbs"]
    assert "compensation" not in cue["verbs"]
    assert set(cue["applies_to_modal_cues"]) == {
        "shall be entitled to", "are entitled to", "shall be empowered to",
        "shall be authorised to", "shall be authorized to", "shall have the power to",
    }
    assert set(cue["noun_markers"]) == set(gaz["noun_markers"]) == {"of", "for"}
    assert cue["verb_specific_noun_markers"] == gaz["verb_specific_noun_markers"] == {"access": ["to"]}
    assert cue["no_fallback_modal_cue"] == "shall have the power to"


# ── homograph guard: a listed verb immediately followed by a noun-marker
#    is that word's NOUN reading, not its verb one — the sentence abstains
#    rather than publish a misleading P frame ─────────────────────────────
@pytest.mark.parametrize("sentence", [
    "Data subjects are entitled to access to the file.",
    "The data subject shall be entitled to use of the facilities.",
    "The controller shall be entitled to control of the data.",
    "The recipient shall be entitled to transfer of the data.",
    "Citizens are entitled to process of law.",
    "The judge shall be entitled to charge of the case.",
    "The authority shall have the power to order of the court.",
    "The data subject shall be entitled to record of the processing.",
    "The victim shall be entitled to claim of compensation.",
    "Partners are entitled to share of the profits.",
    "The party shall be entitled to address for service.",
    "The authority shall be entitled to act of.",
    "The authority shall be entitled to request of.",
])
def test_homograph_noun_complement_abstains(sentence):
    frame = prose_grammar.analyze(sentence)
    assert frame.operator != "P"


# ── the same verb immediately followed by something other than a
#    noun-marker is the genuine verb reading, and still reads permission ──
@pytest.mark.parametrize("sentence", [
    "Data subjects are entitled to access their personal data.",
    "The authority shall be empowered to request access to the premises.",
    "The Commission shall be empowered to supplement this Regulation.",
])
def test_real_verb_use_with_an_object_still_reads_permission(sentence):
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"


# ── "inspect"/"withdraw" are not in the closed verb list (the corpus
#    snapshot this list was derived from does not attest either one
#    directly after one of the six cues): a safe abstention, not a wrong
#    reading, is the correct and expected outcome here ────────────────────
@pytest.mark.parametrize("sentence", [
    "The authority shall be authorised to inspect premises.",
    "The authority shall be entitled to withdraw consent.",
])
def test_unlisted_verb_abstains_safely(sentence):
    frame = prose_grammar.analyze(sentence)
    assert frame.operator != "P"


# ── "order the controller to comply" keeps working: "order" followed by
#    "the", never a noun-marker ───────────────────────────────────────────
def test_order_the_controller_to_comply_still_reads_permission():
    frame = prose_grammar.analyze(
        "The supervisory authority shall have the power to order the "
        "controller to comply.")
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"


# ── "shall have the power to" has NO fallback: a failed complement check
#    must abstain the whole sentence, never fall back to a wrongly
#    accepted O/duty reading (its own "shall"-alone fallback does not
#    abstain on its own terms, unlike the other five entries) ────────────
@pytest.mark.parametrize("sentence", [
    "The authority shall have the power to audit the controller.",
    "The authority shall have the power to inspect the premises.",
    "National competent authorities shall have the power to temporarily "
    "or permanently suspend the testing.",
    "The Lead Overseer shall have the power to:",
])
def test_have_the_power_to_abstains_without_fallback(sentence):
    frame = prose_grammar.analyze(sentence)
    assert not frame.accepted
    assert frame.operator != "O"


# ── the other five cues are UNCHANGED: a failed check still falls back to
#    the bare obligation lexeme, which then abstains on its own terms ─────
def test_other_five_cues_still_fall_back_and_abstain():
    frame = prose_grammar.analyze(
        "The authority shall be empowered to investigate the matter.")
    assert not frame.accepted
    assert frame.operator != "P"
