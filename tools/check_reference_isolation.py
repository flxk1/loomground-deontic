# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Prove the reference implementation is genuinely third-party.

`examples/` exists to prove the deontic contract is implementable by a party
with no access to this project's product code — only the published grammar,
schema, and conformance vectors. That is a checked property, not a claim, only if
something forbids the reference from quietly importing the product it is supposed
to be independent of.

This gate AST-parses every .py file under `examples/` and fails if any imports
`deontic`, `loomground_solver`, `loomground_governance`, or any submodule — by
`import x`, `import x.y`, or `from x import y`.

Run standalone: python3 tools/check_reference_isolation.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "examples"

BANNED_ROOTS = {"deontic", "loomground_solver", "loomground_governance", "loomground_norm"}


def _banned_root(module_name: str | None) -> str | None:
    if not module_name:
        return None
    top = module_name.split(".")[0]
    return top if top in BANNED_ROOTS else None


def check_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bad = _banned_root(alias.name)
                if bad:
                    failures.append(f"{path.name}: `import {alias.name}` imports banned product root {bad!r}")
        elif isinstance(node, ast.ImportFrom):
            bad = _banned_root(node.module)
            if bad:
                failures.append(f"{path.name}: `from {node.module} import ...` imports banned product root {bad!r}")
    return failures


def main() -> int:
    if not REFERENCE.is_dir():
        sys.exit(f"check_reference_isolation.py: no such directory: {REFERENCE}")
    failures: list[str] = []
    files = sorted(REFERENCE.rglob("*.py"))
    for path in files:
        failures.extend(check_file(path))
    print(f"reference isolation gate against {REFERENCE}\n")
    print(f"[{'FAIL' if failures else 'PASS'}] no product imports ({len(files)} files checked)")
    for f in failures:
        print(f"  {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
