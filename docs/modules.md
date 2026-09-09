<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# Module inventory

Moved verbatim from the README (introduction, "What's here", "Conformance").

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

Two further modules export through `deontic`: `deontic.intervention` (the
correctability profile over the existing incidents) and `deontic.contract` (the
composition surface a reasoner consumes; `CONTRACT_VERSION`).

The authoritative language artifacts ship as package data under
`src/deontic/artifacts/`: a compact LLM-facing guide (`llms.txt`, via
`deontic.llms()`), the grammar (`grammar/deontic.ebnf`), the JSON schema
(`schema/statement.schema.json`), the modal + incident vocabulary
(`vocabulary/`), the language card, and the conformance vectors.

## Conformance

```
python -m pytest
```

`deontic.run_conformance(impl)` runs every published vector against any object
exposing `parse`/`validate`/`project`. Passing the vectors is the acceptance gate
for a consumer.
