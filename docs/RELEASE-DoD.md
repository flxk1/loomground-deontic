<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Release definition of done

This is the normative release contract for this language pack. A release is done
only when every applicable requirement below is satisfied and
`python3 tools/release_gate.py` exits zero from the exact commit to be tagged.
Review, a green unit-test job, or a successfully built wheel is not a substitute
for the aggregate gate.

## Acceptance rule

The release candidate must satisfy all four layers:

1. **Source integrity** — metadata, version axes, vocabulary, licensing,
   changelog, ownership, security policy, and release automation are coherent.
2. **Semantic integrity** — unit/property tests, extraction drift, companion
   drift, schema validation, and all published conformance vectors pass.
3. **Independent implementability** — the isolated reference implementation
   imports no product code and passes the published contract.
4. **Distribution integrity** — one sdist and one wheel build; required public
   artifacts are present; the wheel installs without runtime dependencies in a
   fresh environment and works outside the source tree.

The aggregate gate is authoritative because it checks the source and the actual
artifacts that will be published. CI runs it on every push and pull request. The
publishing workflow runs it again and publishes the same verified files from
`dist/`; it does not rebuild after verification.

### Gate map

| Requirement | Executable check |
|---|---|
| Metadata, URLs, zero runtime dependencies, O/P/F vocabulary | `tools/release_gate.py` source contract |
| Package, card, manifest, contract, and guide coherence | `tools/check_versions.py` |
| Language/extraction artifact equality | `tools/check_extraction.py` |
| Product behavior and algebraic laws | `python3 -m pytest` |
| Skill engine parity, including signed conflicts | `tools/check_companion.py` |
| Published vector/schema agreement | `tools/check_vectors.py` |
| Third-party implementability | `tools/check_reference_isolation.py` and `examples/conformance.py` |
| SPDX/REUSE compliance | `reuse lint` |
| Wheel/sdist contents and clean installation | `tools/release_gate.py` distribution checks |

Unchecked prose below is a defect in the gate when it can be automated. A
manual-only item must name the human decision and cannot silently be presented as
machine-verified.

## 1. Package metadata

- [ ] The build file declares a homepage, a repository URL, and an issue tracker URL.
- [ ] A `readme` field points at the repository's README.
- [ ] `authors` names the human author(s). Generative-AI tools that assisted are
      acknowledged in prose (NOTICE, README), never listed as an author.

## 2. Versioning and the version-coherence gate

- [ ] Every genuinely stale version string (a bundled grammar's own metadata, a
      companion tool's manifest, and similar) is bumped to match the current release.
- [ ] A checker — run in CI on every push and pull request — asserts that the
      package/release version is identical everywhere it is declared (build
      metadata, any machine-readable summary card, any conformance or compatibility
      manifest, any bundled sub-artifact that carries its own version field).
- [ ] If the repository has more than one genuinely independent version axis (for
      example: the package/release version, a frozen contract/protocol version, and a
      companion plugin/distribution version), the gate keeps each axis internally
      consistent but never asserts equality *across* axes. State the axes explicitly,
      in a comment or docstring, so a future contributor does not "fix" the deliberate
      difference.
- [ ] The gate is wired into CI, not just runnable by hand.

## 3. Licensing

- [ ] The REUSE (or equivalent SPDX) package name matches the repository's actual
      package name.
- [ ] `reuse lint` (or the project's equivalent license-compliance check) passes.
- [ ] Every new file this checklist adds carries a license header, in whichever form
      (inline comment, or a REUSE.toml annotation for formats with no comment syntax)
      the rest of the repository already uses.

## 4. Changelog

- [ ] A `CHANGELOG.md` exists in keep-a-changelog style, with an `## [Unreleased]`
      section and a dated entry for the current release summarizing what that release
      actually contains, in the repository's own vocabulary (not generic filler).
- [ ] Any known, load-bearing limitation of the current release is stated in that
      entry, not left to be discovered later.

## 5. CI gates

- [ ] Every third-party GitHub Action referenced by `uses:` is pinned to a full commit
      SHA, with a trailing comment naming the tag it corresponds to (so a reviewer can
      still tell what version is pinned).
- [ ] Every ad hoc tool invocation in CI (an `npx` package, a `pip install` of a tool
      not already pinned by a lockfile) names an explicit version.
- [ ] All pre-existing CI gates (whatever domain-specific consistency, drift, or
      discipline checks the repository already had) keep passing — hardening supply
      chain and versioning must not silently drop coverage.

## 6. Governance files

- [ ] Dependabot (or equivalent) is configured for both the CI-action ecosystem and
      the language's package ecosystem, on a low-noise (e.g. weekly, grouped) schedule.
- [ ] The RVND governance lane is the declared automated release owner for the
      repository and applies stricter policy to normative/contract-bearing paths,
      package metadata, and release automation. No human-review dependency is implied.
- [ ] A `SECURITY.md` states the supported-versions policy and how to report a
      vulnerability privately.
- [ ] Release automation configuration (for example, a Release-Please config and
      manifest) matches the repository's actual package name and tagging scheme —
      copy conventions from a sibling repository only where they actually apply; do
      not carry over a sibling's repo-specific quirks (a component-prefixed tag
      scheme, a different release-type) that do not fit this repository.
- [ ] A release workflow creates the release pull request and, once merged, publishes
      using Trusted Publishing (OIDC) to the package index, gated by a protected
      environment — never a long-lived credential committed to the repository.

## 7. Standalone documentation

- [ ] A `RELEASING.md` at the repository root is self-contained: a reader does not
      need any other document open to understand the versioning rule(s), the release
      pull-request flow, and how publishing is authorized.
- [ ] This checklist itself is present (`docs/RELEASE-DoD.md` or equivalent),
      repository-agnostic, and safe to copy into sibling repositories unchanged.

## 8. Installability

- [ ] The package builds (source distribution and wheel) from a clean checkout.
- [ ] The built wheel installs into a fresh environment and the package's public
      entry points (module import, declared version, or CLI, whichever the package
      exposes) work as expected.

## 9. Universality (third-party implementability)

A repository's interop contracts (companion vocabularies, wire schemas, and the
conformance vectors that define what conforming means) are checked for
implementability, not merely published and left on trust.

- [ ] For each such contract, the published artifact set (schema, any profile or
      choice-set document, and the conformance vectors) is sufficient on its own: a
      party with no access to this repository's product code can implement the
      contract from those files alone.
- [ ] A reference implementation proves this: it imports no product package (the
      language's own package, a solver, a store, or any other first-party
      implementation) — only the standard library and, where genuinely needed, a
      widely available third-party library such as a schema validator. It derives
      the schema, profile, and vectors it checks against by loading the published
      files, never by copying constants out of product source.
- [ ] The reference implementation runs both directions the contract defines,
      where both exist: a consumer side that accepts or rejects a candidate record,
      and a producer side that constructs one — the producer's output round-trips
      through the consumer's acceptance check.
- [ ] The reference implementation passes every published conformance vector: every
      vector marked valid is accepted, every vector marked invalid is rejected.
- [ ] The no-product-import property is itself enforced by a checker (an AST scan
      or equivalent), not left to reviewer attention — the reference's isolation
      would otherwise silently erode the first time someone "helpfully" imports a
      product convenience function into it.
- [ ] CI runs both the conformance check and the import-isolation check on every
      push and pull request; neither is a local-only or manual step.
- [ ] Where a repository's own adapters *select* among implementations of a
      contract (rather than merely implementing one), that selection logic is
      neutral: it carries no vendor-name special-casing, no hardcoded preference
      for a particular product's implementation over another conforming one. The
      selection criterion is the contract itself — conformance — not identity.

## 10. Agent-facing guide (`llms.txt`)

A repository whose product is a **language or algebra** — something an agent reads,
emits, or validates instances of in the pack's own notation (a policy graph, a
deontic statement, and the like) — publishes a compact machine-readable guide for
that audience, on the same terms as its other interop artifacts.

This is scoped to language/algebra packs. A reasoning engine, store, or ingestion
framework consumed through an API rather than authored in a notation is **out of
scope**: it may ship an `llms.txt`, but the release gate does not require one. The
test is whether an agent produces or checks artifacts *in the pack's notation*, not
whether the pack is agent-relevant (nearly everything is).

- [ ] An `llms.txt` (following the llms.txt convention) is published as a
      versioned package-data artifact — installed with the package, not only
      present in the source tree — and is loadable through the package's artifact
      accessor, so a party that installs the package can read it.
- [ ] It is self-contained and compact: the vocabulary, the statement/grammar
      shape, the algebra or contract surface, and the usage rules an agent needs to
      use the pack correctly — enough to read, emit, and validate from that file
      alone. It carries no build-process or planning narrative.
- [ ] Its filename and location are recorded in the machine-readable summary card,
      and its version is held to the package version by the version-coherence gate
      (§2), so it neither drifts nor goes undiscovered.
- [ ] Each pack owns its own `llms.txt`. An aggregating server that fronts several
      packs may publish one that links the pack-level files, but never in place of
      them: a single central file would drift from each independently-versioned
      pack.

## 11. Semantic integrity

- [ ] The public carrier rejects invalid primitive operators; fallback from
      ambiguous surface language occurs only in the explicit lowering helper and
      remains visible through confidence/provenance.
- [ ] Proposition polarity is preserved across rendering, duality, conflict
      detection, composition, the skill companion, and published guidance.
- [ ] Hohfeld incidents retain their distinct meanings: a claim is not counted as
      a privilege, and correlatives/opposites remain closed involutions.
- [ ] Every corrected defect has a regression test. The companion engine has a
      drift assertion for semantics it duplicates beyond the conformance vectors.
- [ ] The language pack remains dependency-free at runtime and imports no solver,
      ingester, store, renderer, or host-specific product.

## 12. Distribution integrity

- [ ] The release command produces exactly one wheel and one source distribution.
- [ ] The wheel contains the grammar, schema, vocabulary, extraction cues,
      language card, `llms.txt`, conformance manifest, and every published vector.
- [ ] The source distribution contains the README, changelog, releasing guide,
      security policy, license configuration, release DoD, package metadata, and
      release automation configuration required to audit or rebuild it.
- [ ] The wheel installs with `--no-deps` into a fresh virtual environment.
- [ ] From outside the checkout, the installed package imports, reports the
      release version, loads its language card and `llms.txt`, and passes its
      packaged conformance vectors.
- [ ] The publishing job uploads the exact `dist/` artifacts that passed the gate;
      no build occurs between verification and publication.
