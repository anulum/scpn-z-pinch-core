# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — repository-level truth tests

"""Repository-level contract tests: the scaffold stays truthful."""

from __future__ import annotations

from pathlib import Path

import pytest

from manifest_io import load_json_object

REPO = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    ".editorconfig",
    ".gitattributes",
    ".github/CODEOWNERS",
    ".github/FUNDING.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".zenodo.json",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "GOVERNANCE.md",
    "LICENSE",
    "Makefile",
    "NOTICE.md",
    "README.md",
    "REUSE.toml",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
    "VALIDATION.md",
    "capability-inventory.json",
    "docs/ARCHITECTURE.md",
    "docs/CONTROL_ADAPTER_SPECIFICATION.md",
    "docs/THREAT_MODEL.md",
    "docs/adr/0001-repository-boundary.md",
    "pyproject.toml",
    "reactor-domain.json",
    "requirements-dev.txt",
    "studio/portfolio-descriptor.json",
    "tools/preflight.py",
)

REQUIRED_IGNORE_LINES = (
    "/BACKUP/",
    "/ARCHIVE/",
    "/.coordination/",
    "/04_ARCANE_SAPIENCE/",
)

FORBIDDEN_BADGE_MARKERS = (
    "[![",
    "api.reuse.software/badge/",
    "api.scorecard.dev/projects/",
    "bestpractices.dev/projects/",
    "pypi.org/project/",
)


@pytest.mark.parametrize("relative", REQUIRED_PATHS)
def test_required_path_exists_and_is_not_empty(relative: str) -> None:
    """Every Tier-0 and reactor-standard surface exists with content."""
    path = REPO / relative
    assert path.is_file(), relative
    assert path.stat().st_size > 0, relative


def test_gitignore_carries_defensive_lines() -> None:
    """The ignore rules keep agent-state and backup trees out."""
    lines = {
        line.strip()
        for line in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    for required in REQUIRED_IGNORE_LINES:
        assert required in lines, required


def test_readme_carries_no_unearned_badge() -> None:
    """No badge appears before its live evidence exists."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for marker in FORBIDDEN_BADGE_MARKERS:
        assert marker not in readme, marker


def test_changelog_starts_unreleased() -> None:
    """The changelog carries an Unreleased section and no invented release."""
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "[Unreleased]" in changelog


def test_manifest_declares_exact_configuration_assignment() -> None:
    """The manifest owns exactly its mapped registry configurations."""
    manifest = load_json_object(REPO / "reactor-domain.json")
    assert manifest["project"] == "SCPN-Z-PINCH-CORE"
    assert manifest["configurations"] == [
        "sheared_flow_z_pinch",
        "z_pinch",
    ]
    assert manifest["evidence_maturity"] == "architecture_only"
    assert manifest["capabilities"] == []
    assert manifest["claims"] == []


def test_descriptor_and_inventory_embed_current_manifest_digest() -> None:
    """Derived artefacts point at the exact committed manifest bytes."""
    from manifest_io import sha256_of_file

    digest = sha256_of_file(REPO / "reactor-domain.json")
    descriptor = load_json_object(REPO / "studio" / "portfolio-descriptor.json")
    inventory = load_json_object(REPO / "capability-inventory.json")
    assert descriptor["source"]["manifest_sha256"] == digest
    assert inventory["source"]["manifest_sha256"] == digest
    assert descriptor["lifecycle"]["state"] == "not_federated"
    assert inventory["implemented_capability_count"] == 0


def test_no_agent_state_trees_exist() -> None:
    """Forbidden agent-state paths are absent from the repository."""
    for forbidden in (
        ".coordination",
        "04_ARCANE_SAPIENCE",
        "BACKUP",
        "ARCHIVE",
    ):
        assert not (REPO / forbidden).exists(), forbidden
