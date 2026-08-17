<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Roadmap slice — the deontic language and agentic oversight

Status: **draft, not committed scope.** Non-normative.

A set of open problems in agentic oversight reaches this plane at exactly one
point: **corrigibility**. This slice records why that problem is already almost
expressible here, and the small amount of work that would finish it.

Everything below stays inside this plane's boundary. Deontic defines the
language and the algebra; a reasoner does the inference. Nothing proposed here
imports a solver, a rule extractor, or a reasoning layer.

---

## Corrigibility is a Hohfeld relation

The corrigibility problem is usually posed behaviourally: *will an agent
pursuing a long-horizon objective treat intervention as an obstacle?* Posed that
way it is not a language question at all.

But the *position* being asserted or denied — that a principal can pause,
correct, constrain or terminate an agent, and that the agent is susceptible to
this — is already in `deontic.incidents`, in full, as two of the four correlative
pairs:

| Position held | Correlative | Reading |
|---|---|---|
| principal holds a **power** | delegate under a **liability** | the principal can change the delegate's position; the delegate is susceptible |
| delegate holds an **immunity** | principal under a **disability** | the delegate cannot be so changed; the principal cannot intervene |

`correlative` and `opposite` already compute both directions, and
`is_advantage` already places `power` and `immunity` on the advantage side.
Corrigibility failure is precisely the second row holding between a delegate and
its principal.

Two consequences worth stating, because both fall straight out of the existing
model:

- **Corrigibility is not a modality.** It is not a fourth operator alongside
  `O`/`P`/`F`, any more than a right is. An obligation to remain interruptible is
  an ordinary `O`; the *position* that makes intervention possible is an
  incident. The existing discipline — "right is not a modality; it lives in the
  incident layer" — settles this without amendment.
- **The dangerous case has a name.** An agent immune to correction is not an
  agent with unusual permissions; it is an agent holding an **immunity** whose
  correlative is a principal holding a **disability**. That is a structural
  property of a stated position, and it is classifiable.

---

## Gaps

### D1 · No intervention-position profile

`classify_incident` decides `power` versus `privilege` by whether the verb
changes legal positions (`_POWER_VERBS`). The intervention verbs of agentic
oversight — pause, halt, correct, constrain, revoke, terminate — are exactly
position-changing verbs, but they are not recognised as a named family.

*Candidate shape.* A packaged **profile** over the existing vocabulary: the
intervention verb family, and the four positions each may occupy. Data plus a
classifier that composes the existing ones. No new incident, no new operator, no
new pair.

### D2 · No structural diagnostic for the immunity case

`algebra.system_health` reports the structural utopia/dystopia diagnostic over a
carrier. It does not report the narrower and more consequential structure: a
bearer holding an immunity over a position another bearer must be able to change.

*Candidate shape.* A predicate over a carrier — is any bearer immune with respect
to a declared intervention family — returned as a **flag**, in the same register
as `formula.candidate_conflict`: flagged, never resolved. Resolution is a
reasoner's job and a host's decision, not this plane's.

### D3 · Contrary-to-duty has an unexamined reading here

The algebra already carries contrary-to-duty structure. An agent that has
diverged, and is then subject to a corrective duty, is a contrary-to-duty
configuration — the secondary obligation that arises when the primary one is
already violated. Whether the existing operator covers the oversight reading
cleanly, or whether that reading strains it, is genuinely open and should be
settled by writing the vectors rather than by argument.

---

## What stays out

Explicitly, so the boundary does not drift under a topical problem:

- **No behavioural claim.** This plane can say that a position is immune. It
  cannot say that a system will comply with an intervention, and no profile added
  here should be read as saying so.
- **No enforcement, no monitoring, no escalation.** Those are a host's.
- **No governance vocabulary.** Grades, gates, verdicts and reservations belong
  to the AI-oversight language, not to the general norm language. A profile of
  intervention verbs is general — a company revoking a signing authority is the
  same structure — and is admissible only because it is general.
- **No fourth operator.** Under any pressure.

## Sequencing

| Step | Gap | Reach |
|---|---|---|
| 1 | D1 | `vocabulary/`, a classifier composing the existing ones, conformance vectors |
| 2 | D2 | `algebra`, flag-only, vectors covering the flagged and unflagged cases |
| 3 | D3 | vectors first; amend only if they show a genuine strain |

## Gates

`python -m pytest`, and `run_conformance(impl)` green against the published
vectors. A step that adds a position, an operator, or a pair to the eight
incidents has left this plane's boundary and is wrong by construction.
