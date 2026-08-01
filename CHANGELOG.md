<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Changelog

## [0.1.3](https://github.com/flxk1/loomground-deontic/compare/loomground-deontic-v0.1.2...loomground-deontic-v0.1.3) (2026-08-01)


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
