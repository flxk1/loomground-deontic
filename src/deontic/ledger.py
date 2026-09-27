# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The append-only abstention ledger for the prose grammar.

One JSONL record per sentence a batch runs through :func:`deontic.prose.parse`:
accepted (with its per-field certainty) or abstained (with a typed reason
code, :mod:`deontic.prose_grammar`). The file is opened in append ('a') mode
only — :func:`append_record` never truncates or rewrites an existing ledger,
so a second run over the same path only grows it.

The invariant a governance consumer checks: for one batch, ``accepted +
abstained == input`` — every sentence fed in is accounted for exactly once,
never dropped and never double-counted. :func:`run_batch` returns the tally;
:func:`check_invariant` is the (trivial, but real) predicate a test asserts.

Standard library only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import prose_grammar

__all__ = ["append_record", "run_batch", "check_invariant", "read_records"]


def append_record(path: str | Path, record: dict[str, Any]) -> None:
    """Append one JSON record as a line. Opens ``path`` in 'a' mode only —
    never truncates or rewrites what is already there."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_records(path: str | Path) -> list[dict[str, Any]]:
    """The ledger's records, in append order; ``[]`` if the file does not exist."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def run_batch(sentences: list[str], path: str | Path) -> dict[str, int]:
    """Run :func:`deontic.prose_grammar.analyze` over every sentence, append
    one record per sentence to the ledger at ``path`` (append-only), and
    return the tally ``{"input", "accepted", "abstained"}``.

    A sentence whose core frame parses but whose exception clause is found
    unresolved (``EXCEPTION_XREF_UNRESOLVED`` / ``EXCEPTION_EXTERNAL_UNRESOLVED``)
    still counts as accepted at the sentence level: that status is recorded as
    a per-field abstention inside the record, not a whole-sentence abstention
    (no cross-reference resolver is built; the field is honestly marked
    unresolved rather than the sentence being dropped).
    """
    accepted = 0
    abstained = 0
    for sentence in sentences:
        frame = prose_grammar.analyze(sentence)
        record: dict[str, Any] = {"sentence": sentence, "accepted": frame.accepted}
        if frame.accepted:
            accepted += 1
            record["operator"] = frame.operator
            record["bearer"] = frame.bearer
            record["action"] = frame.action
            record["exception_status"] = frame.exception_status
            record["certainty"] = frame.certainty
            if frame.exception_status in (prose_grammar.EXCEPTION_XREF_UNRESOLVED,
                                          prose_grammar.EXCEPTION_EXTERNAL_UNRESOLVED):
                record["field_abstentions"] = [
                    {"field": "exception", "reason": frame.exception_status}
                ]
        else:
            abstained += 1
            record["reason"] = frame.reason
        append_record(path, record)
    return {"input": len(sentences), "accepted": accepted, "abstained": abstained}


def check_invariant(tally: dict[str, int]) -> bool:
    """``accepted + abstained == input`` for one batch's tally."""
    return tally["accepted"] + tally["abstained"] == tally["input"]
