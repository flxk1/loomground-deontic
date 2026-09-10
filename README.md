<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-deontic

Deontic language and algebra: O/P/F operators, the eight Hohfeld incidents, a statement grammar, and the composition surface a reasoner consumes.

## Problem

"Must", "may", "must not" stay prose; conflicts between duties go unnoticed. Parses obligations, permissions, prohibitions into formulas and flags conflicting pairs.

## Install

```
pip install "loomground-deontic @ git+https://github.com/flxk1/loomground-deontic@loomground-deontic-v0.1.3"
```

Import name `deontic`. Dependents pin `loomground-deontic>=0.1,<0.2`.

## Usage

```python
import deontic

f = deontic.parse("if [processing is carried out] then O(controller : implement TOMs) unless [Art.11]")
deontic.project(f)    # {"operator": "O", "bearer": "controller", ...}

a = deontic.formula_from_fields("obligation", "processor", "notify")
b = deontic.formula_from_fields("prohibition", "processor", "notify")
deontic.compose([a, b]).conflicts   # one O/F clash
```

## Example

```
in : deontic.parse("O(operator : delete personal data)")
out: DeonticFormula(operator='O', bearer='operator', action='delete personal data', condition='', exception='', negated=False, incident='', counterparty='', deadline='', cross_references=[], sanction='', language='en', raw_sentence='', confidence=0.0)
```

## Language

One norm as an operator over a bearer and an action, with an applicability condition and a defeasibility exception. Forms: `O` obligation · `P` permission · `F` prohibition · `if [c] then …` · `… unless [e]` · `¬action`; F ≡ O¬, P ≡ ¬O¬.

```
O(operator : delete personal data)                           must delete
F(operator : transfer personal data outside the EU)          must not transfer
P(operator : retain invoices)                                may retain
if [contract ended] then O(operator : delete personal data)  applies once the contract has ended
O(operator : delete personal data) unless [legal hold]       defeated by a legal hold
O(operator : ¬disclose)                                      negated action
```

`conflict_candidates` flags an O and an F over the same bearer and action. Full card: `docs/language-card.md`.

## Contracts

| Surface | Definition |
|---|---|
| Statement grammar | `src/deontic/artifacts/grammar/deontic.ebnf`; `deontic.parse` / `validate` / `project` |
| Statement shape | `artifacts/schema/statement.schema.json`: operator, bearer, action, condition, exception, negated, incident, counterparty |
| Vocabulary | `artifacts/vocabulary/`: O, P, F; claim, duty, privilege, no-right, power, liability, immunity, disability |
| Composition contract | `deontic.contract`, `CONTRACT_VERSION` 0.1.0: dimension affinity, `incident_vocabulary()`, `conflict_candidates()` |
| Protocol | `deontic.DeonticImplementation`; `deontic.run_conformance(impl)` over 8 vectors |
| Agent entry, reference | `artifacts/llms.txt`, `artifacts/deontic-card.json`, `skills/deontic/`; `examples/deontic_reference.py`, `examples/conformance.py` |

Module inventory: `docs/modules.md`.

## Family

Deontic language and algebra; language separate from inference. The package contains no inference; the algebra flags candidate conflicts for the consuming reasoner.

- Consumes: nothing at runtime (`dependencies = []`).
- Consumed by: `loomground-solver`, `loomground-versum`, `loomground-ingest`, `loomground-norm`.
- Siblings: `loomground-governance`, `loomground-epistemic`, over `loomground-factual`.
- Pipeline: `source → loomground-ingest → loomground-versum → loomground-solver → applied or diagnostic planes`; the norm vocabulary ingest lowers into, solver composes.

Open decisions: `docs/open-decisions.md`, `docs/decisions/`.

## Status

0.1.3 (draft) · contract 0.1.0 · 93 tests · 8 conformance vectors · version axes gated (`tools/check_versions.py`) · Python ≥ 3.10 (CI 3.10, 3.14).

## License

Apache-2.0 — `LICENSES/Apache-2.0.txt`. CC-BY-4.0 — `LICENSES/CC-BY-4.0.txt` (this README, `artifacts/llms.txt`). Boundary: `REUSE.toml`.
