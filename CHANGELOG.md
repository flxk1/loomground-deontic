<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Changelog

## [0.2.3](https://github.com/flxk1/loomground-deontic/compare/loomground-deontic-v0.2.2...loomground-deontic-v0.2.3) (2026-09-29)


### Documentation

* **contract:** name the 5D cell algebra in solver-sync comments ([dd8ee96](https://github.com/flxk1/loomground-deontic/commit/dd8ee966bec2d02fc0f268bcff3b9aa3c4a92453))

## [0.2.2](https://github.com/flxk1/loomground-deontic/compare/loomground-deontic-v0.2.1...loomground-deontic-v0.2.2) (2026-09-28)


### Documentation

* correct stale claims; add How this is made ([b61aa94](https://github.com/flxk1/loomground-deontic/commit/b61aa94ab665401181c2f6996c6d3ba56843e62d))
* fix remaining stale statements found in review ([24dfb1d](https://github.com/flxk1/loomground-deontic/commit/24dfb1dbed8ac626b8727a8c9da8700217fa6901))
* fix stale version/tag claims; add How this is made ([a5930c7](https://github.com/flxk1/loomground-deontic/commit/a5930c70169edbc060411762fb0153fdb6d2150a))

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

* **deontic:** verifier round on the Phase 1 prose grammar (commit 2c48861) —
  `artifacts/gazetteer/exception.json` had dropped the "except"/"save where"
  exception leads, so an exception clause fell into `action` instead of
  `exception`; restored, plus "save as"/"without prejudice to" in
  `extraction.json`'s published `exception_lead` cue. `artifacts/gazetteer/
  modal_lexemes.json` gained "is prohibited from"/"is not permitted to" as
  forced-`F` modal phrases (a phrase may now carry its own `operator`,
  bypassing the lexeme/negation table). `artifacts/gazetteer/condition.json`
  gained "subject to" as a sentence-initial condition lead ("Subject to
  Article 6, the controller shall..." → `condition='Article 6'`,
  `bearer='controller'`, not a bearer that swallows the lead clause). The
  tokenizer (`deontic.prose_grammar._TOKEN_RE`) now tokenizes digits, so a
  number inside a condition/exception span (`"Article 6"`) is not dropped
  from the reconstructed surface text. Per-field certainty
  (`deontic.prose_grammar.analyze`) is computed, not a hard-coded constant: a
  bearer reached only by stripping the negative determiner "no" is `INFERRED`
  (not `CERTAIN`); a condition assembled from a trailing adverbial
  (`tail_leads`) is `INFERRED`, a sentence-initial condition lead is
  `CERTAIN`. Two negation adverbs/negating-interposed-phrases in one frame
  ("shall never not disclose...") now abstain `AMBIGUOUS_NEGATION` instead of
  silently collapsing to F. `deontic.prose_grammar`'s module docstring cites
  the real test files (`test_prose_grammar_dispatch.py` /
  `test_prose_grammar_phrases.py`), not a nonexistent `test_prose_grammar.py`.
  `extraction.json`'s `describes` field no longer claims `deontic.prose`
  reads its cues at runtime (Phase 1 replaced that with the gazetteer-driven
  `deontic.prose_grammar`); `tools/check_extraction.py` gained Gate F, which
  holds every gazetteer-published cue equal to (covered by) `extraction.json`'s
  regex, so the two published surfaces cannot drift apart again.
  `deontic.formula.DeonticFormula` (and `formula_from_fields`) gained an
  `exception_status` field, populated by `deontic.prose.extract` and
  `deontic.grammar.parse`, so a bare `DeonticFormula` reader (not only
  `deontic.plane.read_polarity`) never reports an operator without also
  carrying whether an exception was detected. `pyproject.toml`'s
  `package-data` gained `artifacts/gazetteer/*.json` — a built wheel was
  missing the gazetteers the parser loads at import time. `nd-system.json`
  gained a closed `exception_status` axis (`none_detected` /
  `internal_parsed` / `EXCEPTION_XREF_UNRESOLVED` /
  `EXCEPTION_EXTERNAL_UNRESOLVED`), matching the coordinate
  `deontic.plane.claim_for` already publishes. Tests:
  `tests/test_phase1_findings.py` (one test per point above).

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

* **deontic:** verifier round, findings L121/L122/COVERAGE on the Phase 1
  prose grammar. **L121 (negation):** `deontic.prose_grammar.analyze` now
  counts negation from every source a sentence can carry it in together —
  the adverb/negating-interposed run it already counted, plus a negative
  determiner on the subject ("No processor ...") and a modal phrase that
  itself already lexicalises a negated modal ("is prohibited from", "is not
  permitted to" — any `modal_lexemes.json` entry with the new `"negates":
  true`) — and the polarity check now runs *before* any forced-operator
  dispatch. Two or more negators from any combination of sources abstain
  `AMBIGUOUS_NEGATION`, never collapse to an operator: "The processor is
  prohibited from not disclosing the data.", "The controller is not
  permitted to not disclose the data.", and "No processor shall never
  disclose the data." all now abstain (previously two of the three silently
  dispatched to an operator). `modal_lexemes.json` also gained a forced-`P`
  phrase ("is authorised to", mirrored into `extraction.json`'s permission
  cue) so the fix's coverage spans forced-F, forced-P, and plain-modal
  phrasing alike. Tests: `tests/test_negation_matrix.py` (a 3×3×3 matrix over
  {forced-F, forced-P, plain modal} × {0, 1, 2 negators} × {adverb,
  determiner, lexical source}, plus the three fixtures above named
  individually).
* **deontic:** verifier round, **L122 (binding)** — `nd-system.json`'s
  `statement.exception_status` binding now resolves: `exception_status` is a
  real property of `artifacts/schema/statement.schema.json`, and
  `deontic.grammar.project` emits it (from the formula's own
  `exception_status` when set, else computed fresh from `exception` via
  `deontic.prose_grammar.classify_exception_status` — the same pure function
  `deontic.plane.claim_for` already used for its own coordinate, so the two
  never drift). Every published conformance vector's `expected.json` /
  `artifacts/conformance/prose.json` entry gained the field. Test:
  `tests/test_binding_slots_resolve.py` (resolves every shipped binding;
  fails on an injected bogus `form_slot` or an unreasoned `null` one).
* **deontic:** verifier round, **COVERAGE** — abstention in
  `deontic.prose_grammar.analyze` is now **per field** (`operator`/modality,
  `bearer`, `action`, `action_head`, `exception_status`), published on the new
  `ProseFrame.field_reasons` map: a sentence with a clear modal now yields a
  modality even when its bearer or its action cannot be grounded (each
  unresolved field carries its own typed reason instead of the whole sentence
  collapsing to one guess). `ProseFrame.accepted`/`.reason` keep their
  pre-existing whole-frame meaning (`True` only when operator, bearer, and
  action all resolved — the three fields a `DeonticFormula` requires) for
  every existing caller (`deontic.prose`, `deontic.ledger`); a caller that
  wants every field's own outcome reads `field_reasons` directly, always
  populated. New output field **`action_head`**: the action's governing verb
  lemma (stdlib rule-based, deterministic — `artifacts/gazetteer/
  verb_lemma.json`'s surface-form exceptions table plus a regular-suffix
  fallback; never a verb inside a subordinate complement — "ensure that the
  data is disclosed" heads on "ensure", never "disclosed"), published
  alongside the unchanged full-span `action`; it abstains into
  `field_reasons["action_head"]` (`ACTION_HEAD_INDETERMINATE`, or the
  `action` field's own reason when `action` itself abstained) rather than
  guess. `action_head` is a `ProseFrame`/ledger-record field, not a
  `statement.schema.json`/`nd-system.json` axis — the deontic language's
  5D-facing surface is unchanged; only the prose producer's own richer
  reader grew. Tests: `tests/test_action_head.py` (per-field coverage plus
  `action_head` over 12 distinct constructions, including a phrasal
  complement, a causative passive, a forced-F/forced-P modal phrase, and a
  bare-passive abstention).
* **deontic:** `artifacts/gazetteer/exception.json`'s `xref_markers` gained
  `"chapter"` — "under Chapter II" is as much an unresolved cross-reference as
  "under Article 6" or "under Annex I". Test:
  `tests/test_action_head.py::test_chapter_is_an_xref_marker`.
* **deontic:** verifier round, **L128 (negative-quantifier subjects and
  coordinated negation)** — a subject opening with "none of", "neither" (the
  "Neither X nor Y ..." coordination), "nobody", or "no one"
  (`artifacts/gazetteer/negation.json`'s new `subject_leads`, checked ahead of
  `lexicon.json`'s single-word `negative_determiner`) now forces the frame to
  F exactly like a bare "no" does — but, unlike "No X ...", none of these
  names one resolvable noun phrase, so `bearer` abstains
  (`AMBIGUOUS_SUBJECT`) rather than guess one side of an unresolved
  coordination or a quantified set as if it were the bearer:
  "None of the processors shall disclose the data." and "Neither the
  controller nor the processor shall disclose the data." now both lower to
  `F` with an abstained bearer, never a guessed one. A coordinated action
  ("The processor shall neither disclose nor sell the data.") is a second,
  orthogonal fix: "neither" there is now recognised by the `negation?`
  production too (`negation.json`'s new `coordinated_negators`, merged with
  `adverbs` at the point `deontic.prose_grammar.analyze` walks that
  production — deliberately kept out of `adverbs` itself so
  `tools/check_extraction.py`'s Gate F sync probe, which reads `adverbs`
  against `extraction.json`'s published prohibition cue, is unaffected),
  consumed before `action` opens — `action_head` resolves to `disclose`, the
  first coordinated verb, never the coordinator word "neither" itself. A new
  closed-class stoplist, `artifacts/gazetteer/function_words.json`, is now
  consulted by `deontic.prose_grammar._action_head` as a defensive backstop:
  a resolved lemma that lands in the stoplist (a determiner, negator,
  coordinator, copula, or preposition) abstains `ACTION_HEAD_INDETERMINATE`
  rather than publish it as if it were a governing verb. Tests:
  `tests/test_neither_none_of.py`; `tests/test_negation_matrix.py` gained the
  L128 rows plus two stoplist-invariant tests (over the full negation matrix,
  and over every sentence this round's new test modules introduce).
* **deontic:** verifier round, **scope/effect (constitutive) statements** — a
  sentence whose action opens on a scope/effect verb phrase about an
  instrument or provision ("apply to", "apply from", "affect", "preclude",
  "be without prejudice to" — the new `artifacts/gazetteer/scope_verbs.json`,
  the sole source of this list) now abstains the whole frame
  (`SCOPE_STATEMENT`, a new typed reason in `ABSTAIN_REASONS`): no operator,
  no bearer, no action_head — the sentence states what the instrument does or
  covers, not a bearer's duty. "This Regulation shall not apply to
  processing carried out by a natural person.", "This Article shall [not]
  affect the application of Regulation (EU) 2016/679.", "This Chapter shall
  be without prejudice to the powers of supervisory authorities.", "This
  Regulation shall [not] preclude Member State law.", and "This Regulation
  shall apply from 25 May 2018." all now abstain this way, in both their
  negated and positive forms; "The controller shall apply appropriate
  measures." (an ordinary duty — "apply" alone, not "apply to"/"apply from",
  is not a scope verb) is unaffected and still yields `O` with a bearer. An
  exception after the scope phrase is still detected and typed ("... shall not
  apply to processing unless required by Union law." keeps
  `EXCEPTION_EXTERNAL_UNRESOLVED`); only a scope phrase that is itself an
  exception lead ("be without prejudice to") is not an exception. The
  grammar's `action` production names the scope branch. Test:
  `tests/test_scope_statements.py`.

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
