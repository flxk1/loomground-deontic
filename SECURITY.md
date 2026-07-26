<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Security policy

## Supported versions

`loomground-deontic` is currently pre-1.0. Security fixes are made on the latest
release line only.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting for this repository. Include the affected version or commit,
reproduction steps, impact, and any suggested mitigation. Please allow the maintainer
time to investigate before public disclosure.

This repository ships a language and algebra as a data-only Python package — its
parsing and validation operate on plain strings and dicts, with no network service,
no evaluation of untrusted code, and no host adapter of its own. A vulnerability
report is most likely to concern the packaged conformance vectors, the build and
release pipeline, or a denial-of-service in the deterministic classifiers on
adversarial input; please say which is affected.
