<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2026 flxk1 -->
# loomground-deontic — language card

Values from `src/deontic/artifacts/grammar/deontic.ebnf`, `artifacts/vocabulary/*.json` and `artifacts/schema/statement.schema.json` (0.2.1). Canonical-statement examples below are `deontic.parse` inputs; prose examples are `deontic.parse_prose` inputs.

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

Parsed (`operator · bearer · action · condition · exception · exception_status · negated`):

```
O · operator · delete personal data · '' · '' · none_detected · False
F · operator · transfer personal data outside the EU · '' · '' · none_detected · False
P · operator · retain invoices · '' · '' · none_detected · False
O · operator · delete personal data · contract ended · '' · none_detected · False
O · operator · delete personal data · '' · legal hold · internal_parsed · False
O · operator · disclose · '' · '' · none_detected · True
```

`exception_status` (`deontic.prose_grammar.classify_exception_status`) is a pure
function of `exception`'s own text: `none_detected` when no exception clause is
present; otherwise `internal_parsed`, unless the clause's own words name an
unresolved cross-reference (`EXCEPTION_XREF_UNRESOLVED` — "Article", "Art.",
"Section", "Sec.", "Annex", "Paragraph", "Chapter", "§") or an external
instrument (`EXCEPTION_EXTERNAL_UNRESOLVED` — "law", "statute", "regulation",
"directive", "enactment"), per `artifacts/gazetteer/exception.json`. No
cross-reference is ever resolved — the status only names what kind of lookup a
reasoning layer would need to do.

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

## Registration and dimension

deontic is registered as an nD system on the versum index (the `loomground.planes` entry point, id `deontic`; see `artifacts/nd-system.json`). Its operators (O/P/F) carry no 5D dimension: a norm's content is an action-type entry linked to the norm by a structural `embeds` link, and the deontic `action` coordinate (`concept_reference`) merely references it.

## Negation after a modal

A negation adverb after a modal ("not", "never", "at no time"), with or without interposed commas or an interposed phrase (e.g. "shall never, under any circumstances,"), lowers the modal to F, with the negation adverb and any interposed phrase consumed by the matched cue so neither reaches `action` nor is duplicated onto `negated`. "neither" opening a coordinated action ("shall neither disclose nor sell the data") negates the same way; `action_head` is then the first coordinated verb ("disclose"), never the coordinator word itself.

## Negative-quantifier and coordinated-negation subjects

A subject opening with "none of", "neither" (the "Neither X nor Y ..." coordination), "nobody", or "no one" forces the frame to F exactly like a bare "no" does — but, unlike "No X ..." (which strips "no" and keeps the remaining noun phrase as the bearer, e.g. "No processor shall retain the record." → bearer `processor`), none of these names one resolvable noun phrase: "None of the processors ...", "Neither the controller nor the processor ...", "Nobody ...", and "No one ..." all abstain the bearer instead of guessing one side of an unresolved coordination or a quantified set. Example: `deontic.parse_prose("None of the processors shall disclose the data.")` → `operator='F'`, `bearer=''` (abstained), `action='disclose the data'`, `action_head='disclose'`.

A closed-class stoplist (`artifacts/gazetteer/function_words.json`) is a defensive backstop on `action_head`: a resolved lemma that is itself a determiner, negator, coordinator, copula, or preposition abstains rather than publish — so `action_head` is never, for example, the word "neither".

## Scope/effect (constitutive) statements

A sentence whose action opens on a scope/effect verb phrase about an instrument or provision — "apply to", "apply from", "affect", "preclude", "be without prejudice to" (`artifacts/gazetteer/scope_verbs.json`) — is constitutive, not a duty: it states what the instrument does or covers. The whole frame abstains with no operator, no bearer, and no action_head, in both the negated and the positive form: "This Regulation shall not apply to processing carried out by a natural person." and "This Regulation shall apply to processing carried out by a controller." both abstain this way, as do the "affect"/"preclude"/"be without prejudice to"/"apply from" patterns. An exception after the scope phrase is still detected and typed as usual ("This Regulation shall not apply to processing unless required by Union law." keeps `EXCEPTION_EXTERNAL_UNRESOLVED`); only the scope phrase itself ("be without prejudice to" opening the statement) is not read as an exception. An ordinary duty is unaffected: "The controller shall apply appropriate measures." ("apply" alone, not "apply to"/"apply from", is not a scope verb) still yields `O`, bearer `controller`, action_head `apply`.

## Outside the language

Who wins a conflict, ordering in time, jurisdiction, who the norm's author is. Those belong to `loomground-norm`, `loomground-legal`, `loomground-topos`.
