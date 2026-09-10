<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-deontic — language card

Values from `src/deontic/artifacts/grammar/deontic.ebnf`, `artifacts/vocabulary/*.json` and `artifacts/schema/statement.schema.json` (0.1.3). Every statement below was run through `deontic.parse` before this card was written; the outputs are pasted from that run.

## Grammar, complete (8 rules)

```
statement   = [ condition ] core [ exception ] ;
condition   = "if" "[" text "]" "then" ;
exception   = "unless" "[" text "]" ;
core        = operator "(" bearer ":" proposition ")" ;
proposition = [ "¬" ] text ;
operator    = "O" | "P" | "F" ;
bearer      = text ;   action = text ;
text        = one or more characters, none of ( ) : [ ] and no leading ¬
```

## Operators

| operator | reading | definition |
|---|---|---|
| `O` | obligatory | primitive |
| `P` | permitted | ¬O(¬a) |
| `F` | forbidden | O(¬a) |

The deontic square holds: O and F are contraries, P is the dual of F.

## Structured fields

Beside the surface (`statement.schema.json`): `incident`, `counterparty`, `deadline`, `cross_references`, `sanction`, `language`, `confidence`, `raw_sentence`.

## Incidents (Hohfeld, four correlative pairs)

`claim` ↔ `duty` · `privilege` ↔ `no-right` · `power` ↔ `liability` · `immunity` ↔ `disability`. Correlatives and opposites are checkable relations (`deontic.correlative`, `deontic.opposite`).

## Statement forms and readings

```
O(operator : delete personal data)                           the operator must delete personal data
F(operator : transfer personal data outside the EU)          the operator must not transfer personal data outside the EU
P(operator : retain invoices)                                the operator may retain invoices
if [contract ended] then O(operator : delete personal data)  the duty applies once the contract has ended
O(operator : delete personal data) unless [legal hold]       the duty is defeated by a legal hold
O(operator : ¬disclose)                                      the operator must not disclose (negated action)
```

Parsed (`operator · bearer · action · condition · exception · negated`):

```
O · operator · delete personal data · '' · '' · False
F · operator · transfer personal data outside the EU · '' · '' · False
P · operator · retain invoices · '' · '' · False
O · operator · delete personal data · contract ended · '' · False
O · operator · delete personal data · '' · legal hold · False
O · operator · disclose · '' · '' · True
```

## Functions

`parse(text) → DeonticFormula` · `validate(formula) → {ok, errors}` · `project(formula) → dict` · `formula.render() → str` · `contract.conflict_candidates([f, g])`.

```
conflict_candidates([O(operator : delete personal data), F(operator : delete personal data)])
→ [{'kind': 'deontic-conflict', 'bearer': 'operator', 'action': 'delete personal data',
    'operator_a': 'O', 'operator_b': 'F', 'resolution': 'candidate-escalate',
    'predicate': 'may-conflict-with', 'confidence': 0.0, ...}]
```

## Round trip

A formula renders to a string the grammar parses back to the same formula: `parse(f.render()) == f` held for all six statements above.

## Outside the language

Who wins a conflict, ordering in time, jurisdiction, who the norm's author is. Those belong to `loomground-norm`, `loomground-legal`, `loomground-topos`.
