# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Cue-list fixes: condition leads, an exception lead, and the power-verb
cues.

  1. "by way of derogation from" is NOT an exception lead (it marks the
     opposite relation — the current rule overrides the referenced
     provision, not the other way round). Not modelled as anything else.
  2. power_verb "require" is narrowed to the active forms "require"/
     "requires"/"requiring" only, checked over the action span only, never
     the whole raw sentence, mirrored byte-for-byte into
     `skills/deontic/deontic_engine.py` and held equal by
     `tools/check_companion.py`.
  3. "at the request of" / "upon the request of" keep the lead's own words in
     the published condition (the request, not only the party). "in the case
     of" is not consumed as a lead at all — ambiguous between a real
     condition and a bare scope marker, and the parser cannot tell the two
     apart.
  4. "in such a case" publishes the phrase itself as the condition, never an
     empty string indistinguishable from an unconditional duty.
  5. power-verb stems are word-anchored to explicit finite-verb forms
     wherever a bare stem+\\w* wildcard also spelled an unrelated common
     noun/adjective (e.g. elect\\w* matched "electronic"); "authorised"/
     "authorized" is excluded immediately before "representative(s)".

    python -m pytest tests/test_cue_gaps.py
"""
from __future__ import annotations

import pytest

import deontic
from deontic import incidents, prose_grammar


# ── "by way of derogation from" is NOT an exception lead ───────────────────
def test_by_way_of_derogation_from_is_not_an_exception_lead():
    # Pinned to origin/main's own (pre-existing, unchanged) reading: the
    # derogation clause is not lifted into `exception`; it stays embedded in
    # `action`.
    sentence = "Member States may, by way of derogation from Article 5, provide for exemptions."
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.operator == "P"
    assert frame.bearer == "Member States"
    assert frame.exception == ""
    assert frame.action == "by way of derogation from Article 5, provide for exemptions"


def test_abweichend_von_is_not_a_gazetteer_exception_lead():
    # It has zero effect on the (English-only, Phase 1 scope) prose grammar.
    gaz = prose_grammar._load_gazetteer("exception")
    assert "abweichend von" not in gaz["lead_phrases"]
    assert "by way of derogation from" not in gaz["lead_phrases"]


# ── "require" power-verb: active forms only, action-scoped only ───────────
def test_require_is_not_a_power_verb_regex_alternative():
    assert incidents._POWER_VERBS.search("require the borrower to provide security") is None


@pytest.mark.parametrize("sentence", [
    "require the borrower to provide additional security",
    "requires the borrower to provide additional security",
    "requiring the borrower to provide additional security",
    "may require that the borrower provide additional security",
])
def test_active_require_forms_are_detected(sentence):
    assert incidents._has_active_require(sentence) is True


# "required", in every shape, must never count — only the active forms
# "require"/"requires"/"requiring" do.
@pytest.mark.parametrize("text", [
    "requirement",
    "requirements",
    "specific requirements laid down by this Regulation",
    "is required",
    "are required",
    "was required",
    "required",
    "data protection impact assessment is required",
    "required by Article 5",
    "unless required by Union law",
    "as required under Union law",
    "required pursuant to Article 6",
    "where required",
    "the information required to assess compliance",
    "the measures it considers required",
    "may not refuse the information required",
])
def test_require_false_positives_do_not_fire(text):
    assert incidents._has_active_require(text) is False


def test_permission_to_require_is_a_power():
    incident = incidents.classify_incident(
        "permission", "require the borrower to provide additional security",
        "The lender may require the borrower to provide additional security.")
    assert incident == "power"


def test_prohibition_to_require_is_a_disability():
    incident = incidents.classify_incident(
        "prohibition", "require additional security from the borrower",
        "The lender may not require additional security from the borrower.")
    assert incident == "disability"


def test_obligation_containing_require_is_still_a_duty_not_misread():
    incident = incidents.classify_incident(
        "obligation", "require the processor to delete the data",
        "The controller shall require the processor to delete the data.")
    assert incident == "duty"


# A permission whose action merely contains the NOUN "requirement(s)", or a
# passive/reduced-relative "required", must stay privilege.
@pytest.mark.parametrize("action,raw", [
    ("determine more precisely specific requirements for the storage",
     "Such provisions may determine more precisely specific requirements for the storage."),
    ("establish and make public a list of the processing operations for which "
     "no data protection impact assessment is required",
     "The supervisory authority may also establish and make public a list of the "
     "processing operations for which no data protection impact assessment is required."),
    ("adopt implementing acts laying down the requirements",
     "The Commission may adopt implementing acts laying down the requirements."),
    ("process data as required under Union law",
     "The controller may process data as required under Union law."),
    ("submit the documents required pursuant to Article 5",
     "The applicant may submit the documents required pursuant to Article 5."),
    ("store the data where required",
     "The controller may store the data where required."),
    ("request the information required to assess compliance",
     "The authority may request the information required to assess compliance."),
    ("adopt the measures it considers required",
     "The supervisory authority may adopt the measures it considers required."),
])
def test_require_false_positives_stay_privilege(action, raw):
    assert incidents.classify_incident("permission", action, raw) == "privilege"


def test_refuse_information_required_is_a_duty_not_a_disability():
    incident = incidents.classify_incident(
        "prohibition", "refuse the information required",
        "The provider may not refuse the information required.")
    assert incident == "duty"


def test_documents_required_by_article_5_is_not_a_power_or_disability():
    # "required by Article 5" sits in the SUBJECT, not the action.
    sentence = "The documents required by Article 5 may be submitted by post."
    action = "be submitted by post"
    incident = incidents.classify_incident("permission", action, sentence)
    assert incident == "privilege"


def test_supervisory_authority_may_require_is_a_power():
    sentence = "The supervisory authority may require the controller to provide additional information."
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    incident = incidents.classify_incident("permission", frame.action, sentence)
    assert incident == "power"


# The action-only scope, pinned directly through classify_incident (not only
# through the helper): an active "require" OUTSIDE the action (here, in the
# condition) must not turn an unrelated permission into a power.
def test_require_outside_the_action_does_not_leak_into_the_incident():
    sentence = "Where the law requires, the controller may store the data."
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert "requires" not in frame.action
    assert incidents.classify_incident("permission", frame.action, sentence) == "privilege"
    # Direct call, independent of the parser: the same action/raw pair must
    # not flip just because `raw` carries an unrelated "requires".
    incident = incidents.classify_incident(
        "permission", "store the data", "Where the law requires, the controller may store the data.")
    assert incident == "privilege"


def test_engine_and_package_power_verb_cues_agree():
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "deontic"))
    import deontic_engine as eng  # noqa: E402
    assert eng._POWER_VERBS.pattern == incidents._POWER_VERBS.pattern
    for probe in ("require", "requires", "requiring", "required", "is required",
                  "required by Article 5", "requirement", "requirements"):
        assert eng._has_active_require(probe) == incidents._has_active_require(probe)
    # The action-only scope must agree through classify_incident itself, not
    # only through the bare helper.
    action, raw = "store the data", "Where the law requires, the controller may store the data."
    assert (eng.classify_incident("permission", action, raw)
            == incidents.classify_incident("permission", action, raw)
            == "privilege")


# ── condition-lead text keeps the request/phrase ────────────────────────────
@pytest.mark.parametrize("sentence,condition,bearer", [
    ("At the request of the data subject, the controller shall provide a copy.",
     "At the request of the data subject", "controller"),
    ("Upon the request of the supervisory authority, the processor shall "
     "cooperate.", "Upon the request of the supervisory authority", "processor"),
    ("In the event of a conflict, the controller shall notify the authority.",
     "a conflict", "controller"),
])
def test_condition_leads_keep_the_request_text(sentence, condition, bearer):
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.condition == condition
    assert frame.bearer == bearer


def test_in_the_case_of_is_not_consumed_as_a_condition_lead():
    # Falls through to the pre-existing (unconsumed-lead) behaviour.
    gaz = prose_grammar._load_gazetteer("condition")
    phrases = {e["phrase"] if isinstance(e, dict) else e for e in gaz["lead_phrases"]}
    assert "in the case of" not in phrases
    sentence = "In the case of a data breach, the controller shall notify the authority."
    frame = prose_grammar.analyze(sentence)
    assert frame.condition != "a data breach"


# ── "in such a case" keeps the phrase as condition text ─────────────────────
def test_in_such_a_case_keeps_the_phrase_as_condition_not_empty():
    sentence = "In such a case, the controller shall notify the authority."
    frame = prose_grammar.analyze(sentence)
    assert frame.accepted, frame.field_reasons
    assert frame.condition == "In such a case"
    assert frame.condition != ""
    assert frame.bearer == "controller"


def test_condition_lead_still_only_matches_sentence_initial():
    # A condition-lead phrase appearing after the modal (inside the
    # interposed/action span) is NOT lifted into `condition` — not
    # recognised as a sibling constituent mid-frame.
    sentence = "The processor shall, at the request of the data subject, notify the authority."
    frame = prose_grammar.analyze(sentence)
    assert "at the request of" not in (frame.condition or "").lower()


# ── power-verb over-match class: noun/adjective collisions ─────────────────
@pytest.mark.parametrize("noun", [
    "electronic", "electric", "election", "elector", "electoral",
    "withdrawal", "waiver", "approval", "authorisation", "authorization",
    "assignment", "assignable", "renewal",
    "instruction", "instructions", "instructor",
])
def test_power_verb_noun_collisions_no_longer_match(noun):
    assert incidents._POWER_VERBS.search(noun) is None


@pytest.mark.parametrize("phrase", [
    "an authorised representative", "an authorized representative",
    "authorised representatives", "authorized representatives",
])
def test_authorised_representative_is_not_a_power_verb(phrase):
    assert incidents._POWER_VERBS.search(phrase) is None


@pytest.mark.parametrize("verb", [
    "terminate", "terminates", "terminated", "terminating",
    "rescind", "rescinds", "rescinded", "rescinding",
    "revoke", "revokes", "revoked",
    "withdraw", "withdraws", "withdrawing", "withdrew", "withdrawn",
    "waive", "waives", "waived", "waiving",
    "consent", "consents", "consented", "consenting",
    "approve", "approves", "approved", "approving",
    "authorise", "authorised", "authorises", "authorising",
    "authorize", "authorized", "authorizes", "authorizing",
    "assign", "assigns", "assigned", "assigning",
    "renew", "renews", "renewed", "renewing",
    "elect", "elects", "elected", "electing",
    "suspend", "suspends", "suspended", "suspending",
    "instruct", "instructs", "instructed", "instructing",
])
def test_power_verb_genuine_verb_forms_still_match(verb):
    assert incidents._POWER_VERBS.search(verb) is not None


def test_eprivacy_electronic_means_sentence_is_a_privilege_not_a_power():
    # A plain permission to use electronic means/communications must not
    # read as a power.
    action = "store information, or gain access to information already " \
             "stored, in the terminal equipment of a subscriber by electronic means"
    incident = incidents.classify_incident("permission", action, action)
    assert incident == "privilege"


def test_engine_power_verb_noun_collision_fix_matches_package():
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "deontic"))
    import deontic_engine as eng  # noqa: E402
    for probe in ("electronic", "withdrawal", "waiver", "approval", "instruction",
                  "an authorised representative"):
        assert eng._POWER_VERBS.search(probe) == incidents._POWER_VERBS.search(probe)


# Two real GDPR corpus sentences (Art. 61(6)/61(9)): "electronic means" no
# longer triggers elect\w*.
@pytest.mark.parametrize("action", [
    "by means of implementing acts, specify the format and procedures for "
    "mutual assistance referred to in this Article and the arrangements for "
    "the exchange of information by electronic means between supervisory "
    "authorities, and between supervisory authorities and the Board",
    "adopt implementing acts of general scope in order to specify the "
    "arrangements for the exchange of information by electronic means "
    "between supervisory authorities, and between supervisory authorities "
    "and the Board",
])
def test_gdpr_corpus_electronic_means_sentences_are_privilege_not_power(action):
    assert incidents.classify_incident("permission", action, action) == "privilege"


# A real GDPR corpus sentence (Art. 28(4)): "authorisation" (noun) no longer
# triggers authoris\w*, so an ordinary prohibition is no longer misread as
# removing a power the processor never had here.
def test_gdpr_corpus_authorisation_noun_sentence_is_a_duty_not_disability():
    action = "engage another processor without prior specific or general " \
             "written authorisation of the controller"
    raw = "The processor shall not engage another processor without prior " \
          "specific or general written authorisation of the controller."
    assert incidents.classify_incident("prohibition", action, raw) == "duty"


# A real GDPR corpus sentence (Art. 36(5)): "require" IS an active verb here
# and must read as a power.
def test_gdpr_corpus_member_state_law_may_require_is_a_power():
    action = ("require controllers to consult with, and obtain prior "
              "authorisation from, the supervisory authority")
    raw = ("Member State law may require controllers to consult with, and "
           "obtain prior authorisation from, the supervisory authority with "
           "regard to processing by a controller for the performance of a "
           "task carried out by the controller in the public interest.")
    assert incidents.classify_incident("permission", action, raw) == "power"
