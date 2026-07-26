# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The single executable definition of done for a deontic release.

This gate checks the source contract, runs every semantic/conformance gate,
builds exactly one wheel and one sdist, inspects the wheel's public artifacts,
and installs that wheel into a fresh virtual environment for an import smoke
test. A release is done only when this command exits zero.

Run from the repository root:

    python3 tools/release_gate.py

Dependencies used by the gate are development tools, never runtime dependencies:
pytest, jsonschema, build, and reuse.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "src" / "deontic" / "artifacts"
REQUIRED_ROOT_FILES = (
    "README.md", "CHANGELOG.md", "RELEASING.md", "SECURITY.md", "NOTICE",
    "REUSE.toml", "MANIFEST.in", "pyproject.toml",
    "release-please-config.json", ".release-please-manifest.json",
    "docs/RELEASE-DoD.md",
)
REQUIRED_SDIST_FILES = REQUIRED_ROOT_FILES + (
    ".github/workflows/ci.yml",
    ".github/workflows/release-please.yml",
    "reference/deontic_reference.py",
    "reference/conformance.py",
    "skills/deontic/SKILL.md",
    "skills/deontic/deontic_engine.py",
    "tools/release_gate.py",
)
REQUIRED_WHEEL_ARTIFACTS = (
    "deontic/artifacts/deontic-card.json",
    "deontic/artifacts/extraction.json",
    "deontic/artifacts/grammar/deontic.ebnf",
    "deontic/artifacts/llms.txt",
    "deontic/artifacts/schema/statement.schema.json",
    "deontic/artifacts/vocabulary/operators.json",
    "deontic/artifacts/vocabulary/incidents.json",
    "deontic/artifacts/conformance/manifest.json",
)


def run(label: str, command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"\n==> {label}")
    subprocess.run(command, cwd=cwd, check=True)


def read_version() -> str:
    text = (ROOT / "src/deontic/_version.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise AssertionError("src/deontic/_version.py has no version")
    return match.group(1)


def check_source_contract() -> None:
    missing = [name for name in REQUIRED_ROOT_FILES if not (ROOT / name).is_file()]
    if missing:
        raise AssertionError(f"missing release files: {missing}")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if project["name"] != "loomground-deontic":
        raise AssertionError("project.name must be loomground-deontic")
    if project.get("dependencies") != []:
        raise AssertionError("the language pack must have no runtime dependencies")
    if set(project.get("urls", {})) != {"Homepage", "Repository", "Issues"}:
        raise AssertionError("project.urls must declare Homepage, Repository, and Issues")

    card = json.loads((ART / "deontic-card.json").read_text(encoding="utf-8"))
    if card.get("operators") != ["O", "P", "F"]:
        raise AssertionError("language card operators must be exactly O/P/F")
    well_formedness = " ".join(card.get("well_formedness", []))
    if re.search(r"\bR\b", well_formedness):
        raise AssertionError("language card still presents R as a modality")
    if re.search(r"\bO/P/F/R\b", project.get("description", "")):
        raise AssertionError("package description still presents R as a modality")

    version = read_version()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if "## [Unreleased]" not in changelog:
        raise AssertionError("CHANGELOG.md has no Unreleased section")
    if not re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.M):
        raise AssertionError(f"CHANGELOG.md has no dated entry for {version}")

    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            match = re.search(r"\buses:\s*[^@\s]+@([^#\s]+)", line)
            if match and not re.fullmatch(r"[0-9a-f]{40}", match.group(1)):
                raise AssertionError(
                    f"{workflow.relative_to(ROOT)}:{line_no}: action is not SHA-pinned")

    release_workflow = (ROOT / ".github/workflows/release-please.yml").read_text(
        encoding="utf-8")
    for required in ("id-token: write", "name: pypi", "gh-action-pypi-publish@"):
        if required not in release_workflow:
            raise AssertionError(f"release workflow missing {required!r}")


def build_and_check(dist_dir: Path) -> None:
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)
    run("build wheel and sdist", [
        sys.executable, "-m", "build", "--outdir", str(dist_dir),
    ])

    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise AssertionError(
            f"expected one wheel and one sdist, found {len(wheels)} and {len(sdists)}")

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
    missing = [name for name in REQUIRED_WHEEL_ARTIFACTS if name not in names]
    if missing:
        raise AssertionError(f"wheel is missing public artifacts: {missing}")
    vector_inputs = [name for name in names if name.endswith("/input.deo")]
    if len(vector_inputs) != 8:
        raise AssertionError(f"wheel contains {len(vector_inputs)} vectors, expected 8")

    with tarfile.open(sdists[0], "r:gz") as archive:
        names = archive.getnames()
    forbidden = [
        name for name in names
        if name.endswith(".DS_Store") or "/__pycache__/" in name
        or name.endswith((".pyc", ".pyo"))
    ]
    if forbidden:
        raise AssertionError(f"sdist contains generated/local files: {forbidden}")
    for required in REQUIRED_SDIST_FILES:
        if not any(name.endswith(f"/{required}") for name in names):
            raise AssertionError(f"sdist is missing {required}")

    with tempfile.TemporaryDirectory(prefix="deontic-release-") as temp:
        temp_path = Path(temp)
        venv = temp_path / "venv"
        run("create clean install environment", [sys.executable, "-m", "venv", str(venv)])
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run("install built wheel", [
            str(python), "-m", "pip", "install", "--no-deps", str(wheels[0]),
        ], cwd=temp_path)
        smoke = (
            "import deontic; "
            f"assert deontic.__version__ == {read_version()!r}; "
            "assert deontic.language_card()['operators'] == ['O', 'P', 'F']; "
            "assert deontic.run_conformance(deontic.grammar).ok; "
            "assert deontic.llms().strip()"
        )
        run("smoke-test installed wheel outside the source tree", [
            str(python), "-I", "-c", smoke,
        ], cwd=temp_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist-dir", type=Path, default=ROOT / "dist",
        help="directory in which to create the verified release artifacts",
    )
    args = parser.parse_args()

    print(f"release gate against {ROOT}")
    check_source_contract()
    print("[PASS] source release contract")

    commands = (
        ("supply-chain gate teeth",
         [sys.executable, "tools/supply_chain_gate.py", "--self-test"]),
        ("dependency licenses and CycloneDX SBOM",
         [sys.executable, "tools/supply_chain_gate.py"]),
        ("unit and property tests", [sys.executable, "-m", "pytest", "-q"]),
        ("version and artifact coherence", [sys.executable, "tools/check_versions.py"]),
        ("extraction artifact coherence", [sys.executable, "tools/check_extraction.py"]),
        ("companion skill coherence", [sys.executable, "tools/check_companion.py"]),
        ("vector schema validity", [sys.executable, "tools/check_vectors.py"]),
        ("reference import isolation", [sys.executable, "tools/check_reference_isolation.py"]),
        ("independent reference conformance", [sys.executable, "reference/conformance.py"]),
        ("REUSE licensing compliance", ["reuse", "--no-multiprocessing", "lint"]),
    )
    for label, command in commands:
        run(label, command)

    build_and_check(args.dist_dir.resolve())
    print("\nRELEASE GATE: PASS")
    print(f"verified artifacts: {args.dist_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, subprocess.CalledProcessError) as exc:
        print(f"\nRELEASE GATE: FAIL\n{exc}", file=sys.stderr)
        raise SystemExit(1)
