<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# ADR 001: Corrigibility is a Hohfeld relation, not a fourth modality

- Status: Accepted
- Date: 2026-08-17
- Decision owner: product owner
- Scope: `deontic.intervention` — the intervention profile and its diagnostic

## Context

Whether one party can still pause, correct, constrain or terminate another is
normally posed as a question about *disposition*: will the party comply when
intervened upon? Posed that way it is not a language question, and this plane
has nothing to say about it.

Posed as a question about *position* it is already answerable in the vocabulary
this package ships. Two of the four correlative pairs in `deontic.incidents` are
the formal statement of correctability:

| Position held | Correlative | Reading |
|---|---|---|
| intervener holds a **power** | addressee bears a **liability** | the addressee is susceptible to being changed |
| addressee holds an **immunity** | intervener bears a **disability** | intervention is unavailable against it |

The second row is the case worth naming, and it already has a name. An
addressee immune to correction is not an addressee with unusual permissions; it
is one holding an immunity, and `deontic.correlative` already says what that
makes of the other side.

Nothing was missing from the vocabulary. What was missing was a way to say
*which statements are about intervention*, and a diagnostic that surfaces the
immunity case rather than leaving a reader to notice it.

## Decision

### 1. No new vocabulary — the profile is a reading

The profile adds **no incident, no operator and no correlative pair**. It
contributes a verb family (`pause` / `correct` / `constrain` / `terminate`), a
classifier that composes `classify_incident` rather than restating it, and a
flag-only diagnostic. `INTERVENTION_POSITIONS` is a gloss over four incidents
that already exist, and a test asserts its keys are a subset of `INCIDENTS`.

Corrigibility is explicitly **not** a fourth operator beside `O`/`P`/`F`, for
the same reason a right is not one. An obligation to remain interruptible is an
ordinary `O`; the position that makes intervention possible is an incident. The
existing "right is not a modality" discipline settles this without amendment.

### 2. The intervener's position is computed, never restated

`intervention_exposure` reports the counterparty position by calling
`deontic.correlative`. A second table mapping immunity to disability would be a
place for the two to drift; there is none, and a test asserts the reported value
equals `correlative(incident)`.

### 3. The passive-protection cue is scoped to the profile

`incidents._IMMUNITY_CUES` recognises the *varied / amended / modified /
assigned* family only, so an immunity over an intervention verb ("may not be
terminated") was unreachable — the very case the profile exists to surface.

Two options: widen the general classifier, or recognise the intervention reading
of the same shape locally. **Widening was rejected.** It would change what
`classify_incident` returns for statements outside this profile, altering an
established contract to serve a new reading. The cue therefore lives in
`intervention.py`, applies only to intervention acts, and a test pins that
`classify_incident` is unchanged.

### 4. Diagnostics flag; they never resolve

`intervention_exposure` returns exactly `interventions`, `immune` and `flags` —
no verdict, no severity, no resolution. This matches the register of candidate
conflicts elsewhere in the algebra, and a test asserts no verdict-shaped key
appears.

Two flags are defined. `intervention-immunity` says some addressee holds an
immunity over an intervention act. `intervention-unheld` says the set names
intervention acts but confers a power over none. **Neither is a defect on its
own** — an entrenched protection is an immunity too, and a silent set is not a
closed one.

### 5. `system_health` is left alone

The existing `immunity-absent` pathology asks whether any power is checked. The
profile asks the converse and narrower question: whether intervention itself is
available. Folding it into `system_health` would have changed that function's
output contract; it is a separate entry point instead.

## Consequences

**Gained.** Corrigibility becomes a structural property of a stated norm-set,
classifiable and testable, rather than an aspiration. A consuming reasoner can
ask whether a delegation leaves anyone uncorrectable and get a grounded,
abstention-respecting answer.

**Given up.** The profile can be reached only through the intervention verb
family, which is a seed. A statement that protects a party in wording the cues
do not cover abstains rather than flagging — deliberately, since a
misclassified position misstates who may correct whom.

**Boundary, stated because it is easy to over-read.** This classifies *stated
positions*. It cannot say whether a party will comply with an intervention, and
a norm-set carrying no flag is not thereby well-behaved — only un-flagged.
Compliance is conduct; this is position. Any consumer summarising a clean result
as "corrigible" has overstated it.

**Open.** Whether contrary-to-duty structure covers the case of a party that has
already diverged and is then subject to a corrective duty is unsettled, and
should be decided by writing vectors rather than by argument. Not addressed here.
