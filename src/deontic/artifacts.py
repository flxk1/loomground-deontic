# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Load packaged deontic language artifacts without interpreting their semantics.

Mirrors ``loomground_governance.artifacts``: a data-only loader over the
packaged ``deontic/artifacts/`` tree (the deontic-statement grammar, the JSON
schema, the modal + incident vocabulary, the language card, the conformance
manifest). Reading a file is not interpreting it — the semantics live in the
language modules.
"""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

__all__ = [
    "artifact_path", "load_json", "language_card", "language_version",
    "language_status", "grammar", "vocabulary", "schema", "conformance_manifest",
    "llms",
]


def artifact_path(*parts: str):
    """Return a traversable path inside the packaged artifact tree.

    Resolves to the installed package data; falls back to the repo's
    ``src/deontic/artifacts`` tree when running from a source checkout.
    """
    packaged = files("deontic").joinpath("artifacts")
    path = packaged if packaged.is_dir() else Path(__file__).resolve().parent / "artifacts"
    for part in parts:
        path = path.joinpath(part)
    return path


def load_json(*parts: str) -> Any:
    return json.loads(artifact_path(*parts).read_text(encoding="utf-8"))


def language_card() -> dict:
    return load_json("deontic-card.json")


def language_version() -> str:
    return str(language_card()["version"])


def language_status() -> str:
    return str(language_card()["status"])


def grammar(name: str = "deontic.ebnf") -> str:
    return artifact_path("grammar", name).read_text(encoding="utf-8")


def vocabulary(name: str) -> dict:
    return load_json("vocabulary", f"{name}.json")


def schema(name: str) -> dict:
    return load_json("schema", f"{name}.schema.json")


def conformance_manifest() -> dict:
    return load_json("conformance", "manifest.json")


def llms() -> str:
    """The compact LLM-facing guide to the language (llms.txt)."""
    return artifact_path("llms.txt").read_text(encoding="utf-8")
