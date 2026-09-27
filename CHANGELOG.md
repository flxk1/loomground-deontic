<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Changelog

## [Unreleased]

### Features

* **deontic:** Phase 1 prose grammar — the regex "modal cue" walk in
  `deontic.prose` is replaced by a stdlib-only, deterministic recursive-descent
  parser (`deontic.prose_grammar`), compiled from and kept in sync with a new
  `modal_frame` production appended to `artifacts/grammar/deontic.ebnf`:
  `modal_frame = subject, modal_head, interposed*, negation?, action`, with
  `condition`/`exception` as sibling constituents of the frame. Every
  language-specific surface — modal lexemes, interposed material ("under any
  circumstances", "at any time", "at no time"), negation adverbs, condition
  and exception leads, and the exception content markers — is a JSON
  gazetteer under the new `artifacts/gazetteer/` tree, not a literal in the
  parser. The grammar's operator dispatch is one truth table,
  `deontic.prose_grammar._NEGATED_MODAL` (`(lexeme, negated) -> O/P/F`).
  `deontic.prose.extract` (and the public name `deontic.extract_prose`) keep
  their pre-Phase-1 signature as a thin compatibility layer; `deontic.prose.parse`
  is the new richer reader.
* **deontic:** every field the prose grammar emits (operator, bearer, action,
  condition, exception_status) carries a certainty in `{CERTAIN, INFERRED,
  AMBIGUOUS}`; abstention is per field, with a typed reason code (at least
  `ACTION_IMPLICIT`, `NO_MODAL`, `AMBIGUOUS_NEGATION`, `AMBIGUOUS_SUBJECT`,
  `EXCEPTION_XREF_UNRESOLVED`, `EXCEPTION_EXTERNAL_UNRESOLVED`), written to a
  new append-only JSONL ledger (`deontic.ledger`, opened `'a'` only — never
  truncated or rewritten) with the invariant `accepted + abstained == input`.
* **deontic:** exception detection ("unless", "save as", "subject to",
  "without prejudice to", "except where", "in accordance with Article N") now
  classifies the clause as `none_detected` / `internal_parsed` /
  `EXCEPTION_XREF_UNRESOLVED` / `EXCEPTION_EXTERNAL_UNRESOLVED` — no
  cross-reference resolver is built. The status is carried on the claim's
  coordinate next to the operator (`deontic.plane.claim_for`); the new typed
  reader `deontic.plane.read_polarity` / `deontic.read_polarity` returns
  operator and exception_status together, so a consumer cannot read a norm's
  polarity without its exception status.

### Bug Fixes

* **deontic:** prose lowering — "shall never"/"must never"/"shall at no
  time"/"must at no time" now lower to F (prohibition) with the negation token
  consumed by the matched cue, consistent with the existing "must not"/"shall
  not" handling (`action` carries no leftover negation token; `negated` stays
  `False`, matching `nd-system.json`/`llms.txt`'s "carried by the operator"
  convention). Round-5 defect (a). Fix: `src/deontic/artifacts/extraction.json`
  `modal_cues` (prohibition pattern); producer: `deontic.prose.extract`
  (`src/deontic/prose.py`); tests:
  `tests/test_prose_never_at_no_time.py::test_never_and_at_no_time_lower_to_prohibition`,
  `tests/test_prose_never_at_no_time.py::test_must_not_and_shall_not_are_not_regressed`.

* **deontic:** prose lowering — the negation-adverb-after-modal cue is
  generalised beyond the three Round-5 defect (a) phrasings to cover "may
  never", a comma-set adverb ("shall, at no time,"), and an interposed phrase
  between commas ("shall never, under any circumstances,"). Same convention:
  the negation adverb and any interposed phrase are consumed by the matched
  cue, so `action` is exactly the verb phrase that follows and `negated` stays
  `False`. "must not"/"shall not" and the positive `shall`/`must` → O, `may` →
  P readings are unchanged. Fix: `src/deontic/artifacts/extraction.json`
  `modal_cues` (prohibition pattern); producer: `deontic.prose.extract`
  (`src/deontic/prose.py`); tests:
  `tests/test_prose_negation_adverbs.py::test_negation_adverb_variants_lower_to_prohibition`,
  `tests/test_prose_negation_adverbs.py::test_must_not_shall_not_and_positive_modals_are_unchanged`.

## [0.2.1](https://github.com/flxk1/loomground-deontic/compare/loomground-deontic-v0.2.0...loomground-deontic-v0.2.1) (2026-09-10)


### Documentation

* llms.txt generated from README ([9f3bb07](https://github.com/flxk1/loomground-deontic/commit/9f3bb0785d145b44cea50bf0514094aeb333205a))

## [0.2.0](https://github.com/flxk1/loomground-deontic/compare/loomground-deontic-v0.1.3...loomground-deontic-v0.2.0) (2026-09-10)


### Features

* **intervention:** corrigibility as a Hohfeld relation ([df02107](https://github.com/flxk1/loomground-deontic/commit/df02107fc8423bb6d85f9c82c79e7632de56b369))
* optional typed deadline, cross-references, sanction + cues ([#9](https://github.com/flxk1/loomground-deontic/issues/9)) ([e346601](https://github.com/flxk1/loomground-deontic/commit/e346601a5d09d53cee410e22973ff1ec52246338))
* validity cues + clause-level deadline surface in extraction ([f53b243](https://github.com/flxk1/loomground-deontic/commit/f53b2434098ff2cb846c60e1ae75038cc4f8ea51))


### Bug Fixes

* **deontic:** companion reads negated-modal incident from operator ([5ada56b](https://github.com/flxk1/loomground-deontic/commit/5ada56ba05782c7b5038e7fe0fb5e63c239e0dc6))
* **deontic:** negated modals lower to F, unknown modal fails closed ([4a84d1c](https://github.com/flxk1/loomground-deontic/commit/4a84d1c0d90a92261ad2448c2dd538d3c4168847))
* make deontic skill discoverable by Codex ([85e7c6d](https://github.com/flxk1/loomground-deontic/commit/85e7c6d3c8a6e64cf06e333573cacfa6c671d0b2))


### Documentation

* add Install section; ignore ctrl scratch ledger ([3e9e4c8](https://github.com/flxk1/loomground-deontic/commit/3e9e4c88936686f1cf5c64c148968858804738f2))
* Problem, Example, Language sections; docs/language-card.md ([fac03e4](https://github.com/flxk1/loomground-deontic/commit/fac03e4ff75c365ed2f153ea0fa950eec5f4aa09))
* README to canon (300 words), description, Family ([24c1f8a](https://github.com/flxk1/loomground-deontic/commit/24c1f8a035c3e68ade28685928e5a432b17c220a))
* **roadmap:** corrigibility as a Hohfeld relation ([a071c43](https://github.com/flxk1/loomground-deontic/commit/a071c438510e5362ca8607e3c16d38cde0604682))
* **roadmap:** corrigibility as a Hohfeld relation ([5ba83d9](https://github.com/flxk1/loomground-deontic/commit/5ba83d9fab034db50a8a83444ad5db267dcc493a))

## [0.1.3] - 2026-08-01


### Documentation

* fix stale version, tag framing, and skill example ([c816200](https://github.com/flxk1/loomground-deontic/commit/c8162009e0f3679697db3421ff075eeb8dd56f96))
* fix stale version, tag framing, and skill example ([3eb0b60](https://github.com/flxk1/loomground-deontic/commit/3eb0b6057ecc3691b88489a57b62e85fb227e88d))

## [0.1.2] - 2026-07-26

- Publish the privacy-clean, license-split one-root snapshot.

All notable release changes are documented here. Versions follow Semantic
Versioning while the project is pre-1.0; a minor release may intentionally change
compatibility.

## [Unreleased]

## [0.1.1] - 2026-07-25

### Fixed

- Preserve proposition polarity across duality and conflict detection; reject
  invalid primitive operators instead of silently converting them to duties.
- Preserve generator inputs in composition and keep claim-rights distinct from
  privileges in structural-health diagnostics.

### Changed

- Define one executable release gate covering semantic, conformance, licensing,
  distribution-content, and clean-install checks. CI and Trusted Publishing run
  the same gate and publish the artifacts it verified.

## [0.1.0] - 2026-07-25

The first release: the general deontic language and algebra, packaged as a
data-only Python kit with its conformance vectors.

### Added

- `deontic.operators` — the three deontic modalities `O`/`P`/`F` (one primitive,
  two duals) and their relations: duality, the square of opposition, the operator
  clash. "Right" is not a modality; it reduces to the incident layer.
- `deontic.incidents` — the eight Hohfeldian positions in four correlative pairs,
  the jural correlative/opposite relations, and the deterministic classifiers.
- `deontic.formula` — the formula carrier, canonical rendering, groundedness, the
  `claim_right` constructor, and candidate-conflict flagging. No solver import and
  no rule extractor.
- `deontic.grammar` — `parse` / `validate` / `project` over the canonical deontic
  statement, and the reference implementation of the conformance protocol.
- `deontic.algebra` — carrier, operators (duality, contrary-to-duty, the bilateral
  liberty), the laws as checkable predicates, the composition surface, and
  `system_health` (the structural utopia/dystopia diagnostic).
- `deontic.contract` — the composition contract a reasoner consumes, coupling to
  solver by string agreement only.
- `deontic.artifacts` / `deontic.conformance` / `deontic.protocol` — the data-only
  loader, the acceptance runner, and the neutral protocol.
- Packaged artifacts (`src/deontic/artifacts/`): the grammar, the JSON schema, the
  modal + incident + dimension vocabulary, the language card, a compact agent-facing
  `llms.txt`, and 8 conformance vectors.
- A stdlib-only reference implementation (`reference/`) that loads the published
  artifacts and passes every vector, with an import-isolation gate.

### Known limitation

- The composition contract's exact `SolverProjection` mapping is co-designed with
  solver and not yet frozen; `deontic.algebra.compose` is the provisional surface.
