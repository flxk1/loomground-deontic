<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# Status and open decisions

Moved verbatim from the README.

`0.1.3`, draft. Two boundary decisions are set with foundational defaults, open
to revision before `1.0`:

- **Distribution/import name.** `loomground-deontic` (dist) with `deontic`
  (import). Change before `1.0` if a bare core-language name is wanted.
- **Grammar substrate.** Deontic **stands alone** — `dependencies = []`, no
  dependency on the core Loomground language from governance. Revisit if the nD
  grammar substrate should be shared rather than restated.

The composition contract a reasoner consumes is defined in `deontic.contract`
(and summarised by `deontic.contract_surface()`), coupling to solver by string
agreement only. The exact `SolverProjection` mapping is co-designed with solver
before the surface is frozen.

## Licensing

The language-definition prose in this README and
`src/deontic/artifacts/llms.txt` is licensed under CC-BY-4.0. The Python
reference implementation, grammar, schemas, vocabulary data, `.deo` tooling,
conformance vectors, examples, and repository tooling are licensed under
Apache-2.0. See `LICENSES/CC-BY-4.0.txt`,
`LICENSES/Apache-2.0.txt`, and `REUSE.toml` for the per-file boundary.
