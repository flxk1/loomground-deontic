# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Phase 1 acceptance gate: no `import re`-based modal lowering remains in the
prose path (regex is permitted only for tokenisation), and the prose path
imports no third-party package.

    python -m pytest tests/test_prose_no_regex_modal_lowering.py
"""
from __future__ import annotations

import ast
from pathlib import Path

import deontic

SRC = Path(deontic.__file__).resolve().parent
PROSE_PATH_MODULES = ("prose.py", "prose_grammar.py", "ledger.py")

_STDLIB_ALLOWED = {"__future__", "re", "json", "dataclasses", "typing", "pathlib"}


def test_prose_module_has_no_regex_import_at_all():
    src = (SRC / "prose.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    names = {a.name for n in imports for a in n.names} | {n.module for n in imports
                                                           if isinstance(n, ast.ImportFrom)}
    assert "re" not in names, "deontic.prose must not import re: modal lowering moved to " \
                               "deontic.prose_grammar, where regex is tokenisation-only"


def test_prose_grammar_uses_regex_only_for_tokenisation():
    src = (SRC / "prose_grammar.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    compiles = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "compile"
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "re"]
    # exactly one compiled pattern at module scope: the tokenizer
    assert len(compiles) == 1, f"expected exactly one re.compile (the tokenizer), found {len(compiles)}"


def test_prose_path_modules_import_no_third_party_package():
    for name in PROSE_PATH_MODULES:
        src = (SRC / name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in _STDLIB_ALLOWED or top == "deontic", \
                        f"{name} imports non-stdlib {alias.name!r}"
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import within the deontic package
                top = (node.module or "").split(".")[0]
                assert top in _STDLIB_ALLOWED, f"{name} imports non-stdlib {node.module!r}"
