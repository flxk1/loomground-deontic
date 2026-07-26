<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Releasing

This document is self-contained: read it without needing any other file to
understand how a release of this repository happens.

## Version axes

This repository carries version numbers that look similar but answer different
questions, and none should be collapsed into another:

1. **Package/release** — `src/deontic/_version.py` (the single source `pyproject.toml`
   reads), `src/deontic/artifacts/deontic-card.json`, and
   `src/deontic/artifacts/conformance/manifest.json` share one number (currently
   `0.1.0`). This is the version PyPI installs and the version this document's
   release flow manages. `tools/check_versions.py` gates that the three stay equal
   and that the `llms.txt` guide is discoverable and in sync.
2. **Contract** — `CONTRACT_VERSION` in `src/deontic/contract.py`: the version of
   the composition surface a reasoner negotiates against. It is frozen independently
   of the package release and changes only when the composition contract itself
   changes, never as a side effect of a package release. `tools/check_versions.py`
   keeps this axis internally consistent (the self-describing `contract_surface()`
   reports the package version as its `language_version`) but never asserts it equals
   axis 1.
3. **Plugin/distribution** — `.claude-plugin/plugin.json` (currently `0.1.0`): the
   universal skill bundle's own version. Bumped by hand when the bundled skill
   changes; never needs to equal the package version. `tools/check_companion.py`
   gates that the bundled engine tracks the language (conformance + vocabulary),
   never that its version equals axis 1.

A release bumps axis 1. It must never bump axis 2, and it bumps axis 3 only if the
skill itself changed.

## Release flow (Release Please)

[Release Please](https://github.com/googleapis/release-please) turns conventional
commits on `main` into a reviewed release pull request:

- `fix:` increments the patch version.
- `feat:` increments the minor version.
- `feat!:` or a `BREAKING CHANGE:` footer increments the major version.
- `docs:`, `test:`, `ci:`, and `chore:` do not by themselves trigger a release.

Merging the generated release pull request updates the version and `CHANGELOG.md`,
and creates a plain tag of the form `vX.Y.Z` — no component prefix, because this
repository publishes a single package. Configuration lives in
`release-please-config.json` and `.release-please-manifest.json`; the workflow is
`.github/workflows/release-please.yml`.

Humans approve the version by approving the release pull request; automation only
performs the bookkeeping (computing the version, updating the changelog, creating the
tag).

## Publishing (PyPI Trusted Publishing)

Once the release pull request merges and the tag is created, the `publish` job in
`.github/workflows/release-please.yml` builds the source distribution and wheel once
and publishes them using
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — an OIDC
exchange (`id-token: write`) instead of a long-lived API token stored in the
repository. Publication runs only inside the protected `pypi` GitHub environment and
must pass the RVND governance lane before anything reaches PyPI.

## Local verification before tagging

```
python3 -m pip install "pytest==9.1.1" "jsonschema==4.26.0" "build==1.4.0" "reuse==6.2.0"
python3 tools/release_gate.py
```

This is the single executable definition of done. It runs every semantic and
conformance check, verifies licensing, builds one wheel and one sdist, inspects
their contents, and installs the wheel in a fresh environment. The verified files
remain in `dist/`.

The same gate runs in CI (`.github/workflows/ci.yml`) on every push and pull
request and again in the publishing job. The publishing job uploads the already
verified `dist/` files; it does not rebuild them. A release pull request must pass
the gate before it merges.
