# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Version-coherence gate.

The repository carries two independent version axes; this gate keeps each one
internally consistent and never asserts equality across them (see RELEASING.md).

  Axis 1 — package/release. The single source `src/deontic/_version.py` (which
    `pyproject.toml` reads), `deontic-card.json`, the conformance `manifest.json`,
    and the release-please tracker `.release-please-manifest.json` must all carry
    the same number. A release bumps these together.
  Axis 2 — contract. `CONTRACT_VERSION` in `contract.py` versions the composition
    surface; it moves independently. The gate only checks that the self-describing
    `contract_surface()` does not lie: it reports the package version as its
    `language_version` and `CONTRACT_VERSION` as its `contract_version`.

Also gated (llms.txt discoverability, §10): the language card records the
`llms.txt` location and the file exists; and the card's operator/incident lists
match the code, so the shipped summaries never drift from the vocabulary.

Run standalone: python3 tools/check_versions.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ART = SRC / "deontic" / "artifacts"

sys.path.insert(0, str(SRC))


def _read_version_py() -> str:
    text = (SRC / "deontic" / "_version.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise AssertionError("_version.py: no __version__ string")
    return m.group(1)


def _card() -> dict:
    return json.loads((ART / "deontic-card.json").read_text(encoding="utf-8"))


def _manifest() -> dict:
    return json.loads((ART / "conformance" / "manifest.json").read_text(encoding="utf-8"))


def _release_please_version() -> str:
    data = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
    return str(data.get(".", ""))


def check_package_axis() -> list[str]:
    pkg = _read_version_py()
    card = str(_card().get("version", ""))
    man = str(_manifest().get("version", ""))
    rel = _release_please_version()
    fails = []
    if card != pkg:
        fails.append(f"deontic-card.json version {card!r} != package version {pkg!r}")
    if man != pkg:
        fails.append(f"conformance manifest version {man!r} != package version {pkg!r}")
    if rel != pkg:
        fails.append(f".release-please-manifest.json version {rel!r} != package version {pkg!r}")
    return fails


def check_contract_axis() -> list[str]:
    import deontic
    surface = deontic.contract_surface()
    fails = []
    if surface["language_version"] != _read_version_py():
        fails.append(f"contract_surface language_version {surface['language_version']!r} "
                     f"!= package version {_read_version_py()!r}")
    if surface["contract_version"] != deontic.CONTRACT_VERSION:
        fails.append(f"contract_surface contract_version {surface['contract_version']!r} "
                     f"!= CONTRACT_VERSION {deontic.CONTRACT_VERSION!r}")
    return fails


def check_llms_and_card_sync() -> list[str]:
    import deontic
    fails = []
    card = _card()
    llms_ref = (card.get("artifacts") or {}).get("llms")
    if llms_ref != "llms.txt":
        fails.append(f"card artifacts.llms {llms_ref!r} != 'llms.txt'")
    elif not (ART / llms_ref).is_file():
        fails.append(f"card records llms {llms_ref!r} but the file is missing")
    if list(card.get("operators", [])) != list(deontic.VALID_OPERATORS):
        fails.append(f"card operators {card.get('operators')} != code {list(deontic.VALID_OPERATORS)}")
    if list(card.get("incidents", [])) != list(deontic.INCIDENTS):
        fails.append(f"card incidents drift from code {list(deontic.INCIDENTS)}")
    return fails


_CHECKS = (
    ("package axis (version.py = card = manifest = release-please)", check_package_axis),
    ("contract axis (surface is self-consistent)", check_contract_axis),
    ("llms.txt discoverable, card in sync with code", check_llms_and_card_sync),
)


def test_package_axis():
    assert not check_package_axis(), check_package_axis()


def test_contract_axis():
    assert not check_contract_axis(), check_contract_axis()


def test_llms_and_card_sync():
    assert not check_llms_and_card_sync(), check_llms_and_card_sync()


if __name__ == "__main__":
    total = 0
    print(f"version-coherence gate against {ROOT}\n")
    for label, fn in _CHECKS:
        fails = fn()
        total += len(fails)
        print(f"[{'PASS' if not fails else 'FAIL'}] {label}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{'ALL GREEN' if total == 0 else str(total) + ' version gap(s)'}")
    sys.exit(0 if total == 0 else 1)
