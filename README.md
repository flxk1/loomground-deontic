<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-deontic

The general **deontic language and algebra** for the Loomground family: the
formal vocabulary of norms, a grammar for a deontic statement, the formula
representation, and the **algebra** over those terms that lets a reasoner combine
deontic content with governance and any other language.

It is a **parallel nD language pack, structured like `loomground-governance`** —
not a reasoning library. Governance is the nD language for AI-oversight; deontic
is the nD language for general norms. Both are consumed *by*
[`loomground-solver`](https://github.com/flxk1/loomground-solver), which composes
them. Deontic is foundational: it imports no solver, no rule extractor, and no
reasoning layer — it defines the language, and a reasoner does the inference.

## What's here

| Module | Role |
|---|---|
| `deontic.operators` | The three SDL modals `O`/`P`/`F` (one primitive `O`; `F≡O¬`, `P≡¬O¬`) and their relations (duality, square of opposition, clash). "Right" is not a modality — it lives in the incident layer. |
| `deontic.incidents` | The eight Hohfeld positions in four correlative pairs, the correlative/opposite relations, and the deterministic classifiers. |
| `deontic.formula` | The formula carrier, canonical rendering, groundedness predicate, and candidate-conflict flagging. |
| `deontic.grammar` | `parse` / `validate` / `project` over the canonical statement — also the reference implementation of the conformance protocol. |
| `deontic.algebra` | Carrier, operators (duality, contrary-to-duty, bilateral liberty / the *optional*), the laws as checkable predicates, the composition surface, and `system_health` (the structural utopia/dystopia diagnostic). |
| `deontic.artifacts` | Data-only loader for the packaged language artifacts. |
| `deontic.conformance` | Vectors and the acceptance runner. |
| `deontic.protocol` | The neutral protocol any runtime implements. |

The authoritative language artifacts ship as package data under
`src/deontic/artifacts/`: a compact LLM-facing guide (`llms.txt`, via
`deontic.llms()`), the grammar (`grammar/deontic.ebnf`), the JSON schema
(`schema/statement.schema.json`), the modal + incident vocabulary
(`vocabulary/`), the language card, and the conformance vectors.

## Install

```bash
pip install "loomground-deontic @ git+https://github.com/flxk1/loomground-deontic"
```

Zero runtime dependencies; Python 3.10+. Not yet on PyPI — install from the public
repository by URL, or pin a tag (e.g. `@loomground-deontic-v0.1.3`) for reproducibility.

## Example

```python
import deontic

f = deontic.parse("if [processing is carried out] then O(controller : implement TOMs) unless [Art.11]")
f.operator            # "O"
f.dual()              # "¬P(¬ implement TOMs)"
deontic.project(f)    # structured statement (statement.schema.json shape)

# The algebra combines deontic content, flagging candidate conflicts, never resolving them.
a = deontic.formula_from_fields("obligation", "processor", "notify")
b = deontic.formula_from_fields("prohibition", "processor", "notify")
deontic.compose([a, b]).conflicts   # one flagged O/F clash
```

## Conformance

```
python -m pytest
```

`deontic.run_conformance(impl)` runs every published vector against any object
exposing `parse`/`validate`/`project`. Passing the vectors is the acceptance gate
for a consumer.

## Status and open decisions

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
