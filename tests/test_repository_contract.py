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
    "conftest.py",
    "docs/adr/0002-device-configuration-model.md",
    "reactor-domain.json",
    "requirements-dev.txt",
    "src/scpn_z_pinch_core/__init__.py",
    "src/scpn_z_pinch_core/configuration.py",
    "src/scpn_z_pinch_core/errors.py",
    "src/scpn_z_pinch_core/parameters.py",
    "studio/portfolio-descriptor.json",
    "studio/portfolio-descriptor.schema.json",
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
    assert manifest["evidence_maturity"] == "computational_prototype"
    assert manifest["capabilities"] == [
        {
            "identifier": "device_configuration_model",
            "evidence_maturity": "computational_prototype",
            "evidence_pointer": "VALIDATION.md#device-configuration-model",
        }
    ]
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
    assert inventory["implemented_capability_count"] == 1


def test_no_agent_state_trees_exist() -> None:
    """Forbidden agent-state paths are absent from the repository."""
    for forbidden in (
        ".coordination",
        "04_ARCANE_SAPIENCE",
        "BACKUP",
        "ARCHIVE",
    ):
        assert not (REPO / forbidden).exists(), forbidden


def test_descriptor_matches_ratified_schema() -> None:
    """The committed descriptor matches the ratified 1.1.0 schema shape."""
    schema = load_json_object(REPO / "studio" / "portfolio-descriptor.schema.json")
    descriptor = load_json_object(REPO / "studio" / "portfolio-descriptor.json")
    assert schema["$id"].endswith("/studio-portfolio-descriptor/1.1.0")
    assert schema["additionalProperties"] is False
    assert sorted(schema["required"]) == sorted(descriptor)
    assert sorted(schema["properties"]) == sorted(descriptor)
    assert descriptor["schema_version"] == "1.1.0"


def test_package_agrees_with_manifest_truth() -> None:
    """The device model package matches the manifest's pins and ownership."""
    from scpn_z_pinch_core import OWNED_CONFIGURATIONS, RegistryBinding

    manifest = load_json_object(REPO / "reactor-domain.json")
    assert list(OWNED_CONFIGURATIONS) == manifest["configurations"]
    pin = manifest["spo_registry"]
    binding = RegistryBinding(
        version=pin["version"], digest_sha256=pin["digest_sha256"]
    )
    assert binding.version == pin["version"]
    assert binding.digest_sha256 == pin["digest_sha256"]


def test_typed_package_marker_exists() -> None:
    """The PEP 561 marker is present (empty by design, so no size check)."""
    assert (REPO / "src" / "scpn_z_pinch_core" / "py.typed").is_file()
