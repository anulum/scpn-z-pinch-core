# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — maintained-surface enrollment tests

"""Every tracked file belongs to exactly one gated surface.

The surface table below is the repository's surface-to-gate matrix. A new
tracked file that matches no surface — a new top-level root, a new
language, a new kind of asset — fails this module until the change that
introduces it also names its surface and the gates that check it. Python
source outside the typed cohort is allowed only as a named exception with
its reason.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

TYPED_PYTHON_ROOTS = ("src/", "tools/", "tests/", "benchmarks/")
TYPED_PYTHON_FILES = frozenset({"conftest.py"})


@dataclass(frozen=True)
class Surface:
    """One maintained surface and the gates that check it.

    Attributes
    ----------
    name
        Stable surface identifier.
    patterns
        Patterns over repository-relative POSIX paths: ``*`` and ``?``
        stay inside one path segment, ``**/`` spans any number of
        directories.
    gates
        Gate names that check every file of the surface.
    """

    name: str
    patterns: tuple[str, ...]
    gates: tuple[str, ...]


SURFACES: tuple[Surface, ...] = (
    Surface(
        "package",
        ("src/scpn_z_pinch_core/**/*.py", "src/scpn_z_pinch_core/py.typed"),
        ("ruff", "mypy", "tests+coverage", "codeql"),
    ),
    Surface("tools", ("tools/*.py",), ("ruff", "mypy", "tests+coverage", "codeql")),
    Surface("tests", ("tests/*.py", "tests/data/*.json"), ("ruff", "mypy", "pytest")),
    Surface("pytest-config", ("conftest.py",), ("ruff", "mypy")),
    Surface("benchmarks", ("benchmarks/*.py",), ("ruff", "mypy")),
    Surface(
        "benchmark-results",
        ("benchmarks/results/*.local.json",),
        ("reuse",),
    ),
    Surface(
        "native-crate",
        ("rust/Cargo.toml", "rust/Cargo.lock", "rust/pyproject.toml", "rust/src/*.rs"),
        ("cargo-fmt", "cargo-clippy", "cargo-doc", "cargo-test", "native-parity"),
    ),
    Surface(
        "header-generator",
        ("docs/assets/generate_header.py",),
        ("ruff", "codeql"),
    ),
    Surface("header-images", ("docs/assets/*.png",), ("reuse", "large-files")),
    Surface(
        "documentation",
        ("*.md", "docs/*.md", "docs/adr/*.md", "papers/**/*.md"),
        ("docs-links", "typos", "reuse"),
    ),
    Surface(
        "domain-manifests",
        ("reactor-domain.json", "capability-inventory.json", "studio/*.json"),
        ("reactor-domain", "studio-descriptor", "capability-inventory"),
    ),
    Surface(
        "workflows",
        (".github/workflows/*.yml", ".github/workflow-inventory.json"),
        ("workflows", "actionlint", "pre-commit"),
    ),
    Surface(
        "github-metadata",
        (
            ".github/CODEOWNERS",
            ".github/FUNDING.yml",
            ".github/dependabot.yml",
            ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/*.yml",
        ),
        ("repository-contract", "check-yaml", "reuse"),
    ),
    Surface(
        "dependency-locks",
        ("requirements-*.in", "requirements-*.txt"),
        ("dependency-locks", "pip-audit"),
    ),
    Surface(
        "build-config",
        (
            "pyproject.toml",
            "Makefile",
            ".pre-commit-config.yaml",
            "_typos.toml",
            "REUSE.toml",
            ".editorconfig",
            ".gitattributes",
            ".gitignore",
        ),
        ("local-ci-parity", "check-toml", "repository-contract"),
    ),
    Surface(
        "legal",
        ("LICENSE", "LICENSES/*.txt", "NOTICE", "NOTICE.license"),
        ("reuse", "repository-contract"),
    ),
    Surface("citation", ("CITATION.cff", ".zenodo.json"), ("repository-contract",)),
)

UNTYPED_PYTHON_EXCEPTIONS = {
    "docs/assets/generate_header.py": (
        "generation-time artwork script; needs numpy and matplotlib, which are "
        "deliberately outside the pinned development lock; ruff-checked, not "
        "imported by the package"
    ),
}


def path_matches(path: str, pattern: str) -> bool:
    """Match one path against one segment-aware pattern.

    Parameters
    ----------
    path
        Repository-relative POSIX path.
    pattern
        Pattern where ``*`` and ``?`` never cross ``/`` and ``**/`` matches
        zero or more whole directories.

    Returns
    -------
    bool
        Whether the whole path matches.
    """
    regex = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            regex += "(?:[^/]+/)*"
            index += 3
        elif pattern[index] == "*":
            regex += "[^/]*"
            index += 1
        elif pattern[index] == "?":
            regex += "[^/]"
            index += 1
        else:
            regex += re.escape(pattern[index])
            index += 1
    return re.fullmatch(regex, path) is not None


def tracked_files(root: Path) -> list[str]:
    """List the tracked files of a repository.

    Parameters
    ----------
    root
        Repository root.

    Returns
    -------
    list[str]
        Repository-relative POSIX paths from ``git ls-files``.
    """
    git = shutil.which("git")
    assert git is not None, "git is required to list the tracked tree"
    result = subprocess.run(
        [git, "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def surfaces_of(path: str) -> list[str]:
    """Return the names of every surface whose patterns match a path.

    Parameters
    ----------
    path
        Repository-relative POSIX path.

    Returns
    -------
    list[str]
        Matching surface names; exactly one is expected.
    """
    return [
        surface.name
        for surface in SURFACES
        if any(path_matches(path, pattern) for pattern in surface.patterns)
    ]


def enrollment_findings(paths: list[str]) -> list[str]:
    """Report every path that breaks the enrollment rules.

    Parameters
    ----------
    paths
        Repository-relative POSIX paths to check.

    Returns
    -------
    list[str]
        One finding per unenrolled, doubly enrolled or untyped Python path.
    """
    findings: list[str] = []
    for path in paths:
        matched = surfaces_of(path)
        if len(matched) != 1:
            findings.append(f"{path}: matches surfaces {matched!r}, expected one")
        typed = path.startswith(TYPED_PYTHON_ROOTS) or path in TYPED_PYTHON_FILES
        if path.endswith(".py") and not typed and path not in UNTYPED_PYTHON_EXCEPTIONS:
            findings.append(f"{path}: Python outside the mypy cohort")
    return findings


def test_every_tracked_file_has_exactly_one_gated_surface() -> None:
    """The tracked tree is fully enrolled in the surface-to-gate matrix."""
    assert enrollment_findings(tracked_files(REPO)) == []


def test_every_surface_names_gates_and_is_populated() -> None:
    """No surface is empty or ungated, so the matrix carries no dead rows."""
    paths = tracked_files(REPO)
    for surface in SURFACES:
        assert surface.gates, surface.name
        assert any(surfaces_of(path) == [surface.name] for path in paths), surface.name


def test_untyped_python_exceptions_are_tracked_and_reasoned() -> None:
    """Every named exception exists and states why it is outside mypy."""
    paths = set(tracked_files(REPO))
    for path, reason in UNTYPED_PYTHON_EXCEPTIONS.items():
        assert path in paths, path
        assert len(reason) > 40, path


@pytest.mark.parametrize(
    "path",
    [
        "scripts/new_tool.py",
        "src/scpn_z_pinch_core/kernel.rs",
        "docs/assets/new_diagram.svg",
        "src/scpn_z_pinch_core/catalogue.json",
    ],
)
def test_new_unenrolled_path_is_refused(path: str) -> None:
    """A new root, language or asset kind fails until it is enrolled."""
    assert enrollment_findings([path])


@pytest.mark.parametrize(
    ("path", "pattern"),
    [
        ("README.md", "*.md"),
        (
            "src/scpn_z_pinch_core/physics/level0.py",
            "src/scpn_z_pinch_core/**/*.py",
        ),
        ("src/scpn_z_pinch_core/errors.py", "src/scpn_z_pinch_core/**/*.py"),
        ("LICENSES/AGPL-3.0-or-later.txt", "LICENSES/*.txt"),
        ("NOTICE.md", "NOTICE.m?"),
    ],
)
def test_pattern_matches_inside_its_segments(path: str, pattern: str) -> None:
    """Wildcards match within segments and ``**/`` spans directories."""
    assert path_matches(path, pattern)


@pytest.mark.parametrize(
    ("path", "pattern"),
    [
        ("docs/ARCHITECTURE.md", "*.md"),
        ("src/other/errors.py", "src/scpn_z_pinch_core/**/*.py"),
        ("NOTICE.md", "NOTICE"),
    ],
)
def test_pattern_does_not_cross_segments(path: str, pattern: str) -> None:
    """A single wildcard never crosses ``/`` and the match is whole-path."""
    assert not path_matches(path, pattern)


def test_python_outside_the_typed_cohort_is_refused() -> None:
    """Python placed where mypy does not look is a finding by itself."""
    findings = enrollment_findings(["docs/helper.py"])
    assert any("outside the mypy cohort" in finding for finding in findings)
