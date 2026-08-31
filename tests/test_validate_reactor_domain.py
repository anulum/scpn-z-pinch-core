# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — reactor-domain validator tests

"""Contract tests for the reactor-domain manifest validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from manifest_io import load_json_object
from validate_reactor_domain import main, validate_manifest

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "reactor-domain.json"
MAP_RELATIVE = (
    Path("agentic-shared") / "configs" / "scpn_reactor_family_repository_map.json"
)
MACHINE_MAP = next(
    (
        parent / MAP_RELATIVE
        for parent in REPO.parents
        if (parent / MAP_RELATIVE).is_file()
    ),
    REPO.parent.parent / MAP_RELATIVE,
)


def write_manifest(tmp_path: Path, manifest: dict[str, Any]) -> Path:
    """Serialise one manifest object into a temporary file."""
    path = tmp_path / "reactor-domain.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def mutated(**overrides: Any) -> dict[str, Any]:
    """Return the repository manifest with top-level fields replaced."""
    manifest = load_json_object(MANIFEST)
    manifest.update(overrides)
    return manifest


def test_repository_manifest_is_valid() -> None:
    """The committed manifest passes manifest-internal validation."""
    assert validate_manifest(MANIFEST, None) == []


@pytest.mark.skipif(not MACHINE_MAP.is_file(), reason="canonical map not present")
def test_repository_manifest_agrees_with_machine_map() -> None:
    """The committed manifest passes the portfolio map cross-check."""
    assert validate_manifest(MANIFEST, MACHINE_MAP) == []


def test_missing_manifest_is_one_finding(tmp_path: Path) -> None:
    """An unreadable manifest fails closed with a single load finding."""
    findings = validate_manifest(tmp_path / "absent.json", None)
    assert len(findings) == 1
    assert findings[0].startswith("manifest:")


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"schema": "other"}, "schema:"),
        ({"schema_version": "9.9.9"}, "schema_version:"),
        ({"project": ""}, "project:"),
        ({"device_family": 7}, "device_family:"),
        ({"license": "MIT"}, "license:"),
        ({"evidence_maturity": "finished"}, "evidence_maturity:"),
        ({"capabilities": [{"name": "x"}]}, "capabilities[0]"),
        (
            {"evidence_maturity": "architecture_only"},
            "must be [] at architecture_only",
        ),
        ({"claims": ["fast"]}, "claims:"),
        ({"non_claims": []}, "non_claims:"),
        ({"owned_domains": []}, "owned_domains:"),
        ({"excluded_domains": []}, "excluded_domains:"),
        ({"excluded_domains": ["text"]}, "excluded_domains[0]:"),
        (
            {"excluded_domains": [{"domain": "", "owner": "X"}]},
            "excluded_domains[0].domain:",
        ),
        ({"configurations": []}, "configurations:"),
        ({"configurations": ["Bad-Name"]}, "invalid identifier"),
        (
            {"configurations": ["sheared_flow_z_pinch", "sheared_flow_z_pinch"]},
            "must be unique",
        ),
        (
            {"configurations": ["beta_case", "alpha_case"]},
            "must be sorted",
        ),
        ({"fusion_solver_seams": {"active": ["seam"]}}, "fusion_solver_seams.active:"),
        (
            {"studio_integration": {"state": "federated"}},
            "studio_integration.state:",
        ),
        (
            {"research_group": {"display_name": "X", "coordination_identity": "OTHER"}},
            "coordination_identity: must be",
        ),
        ({"research_group": {"coordination_identity": "X"}}, "display_name: missing"),
        ({"spo_registry": {"version": "1.0.0"}}, "digest_sha256: missing"),
        (
            {
                "spo_registry": {
                    "version": "1.0.0",
                    "digest_sha256": "ZZ",
                    "source_path": "x",
                }
            },
            "64 lowercase hexadecimal",
        ),
        ({"spo_semantic_profile": "review"}, "spo_semantic_profile: missing"),
        (
            {
                "spo_semantic_profile": {
                    "mode": "supervisory",
                    "actionable": True,
                    "control_intent_contract": "v1",
                }
            },
            "mode: must be review_only",
        ),
        ({"control_adapter": None}, "control_adapter: missing"),
        ({"machine_protection": None}, "machine_protection: missing"),
        (
            {"machine_protection": {"final_veto": "software", "statement": ""}},
            "final_veto: must be independent",
        ),
    ],
)
def test_defect_produces_finding(
    tmp_path: Path, overrides: dict[str, Any], fragment: str
) -> None:
    """Each contract violation yields a finding naming the failing field."""
    path = write_manifest(tmp_path, mutated(**overrides))
    findings = validate_manifest(path, None)
    assert any(fragment in finding for finding in findings), findings


def test_actionable_and_intent_contract_findings(tmp_path: Path) -> None:
    """A review-only profile cannot be actionable or carry an intent contract."""
    manifest = mutated(
        spo_semantic_profile={
            "mode": "review_only",
            "actionable": True,
            "control_intent_contract": "v1",
        }
    )
    findings = validate_manifest(write_manifest(tmp_path, manifest), None)
    assert any("actionable: must be false" in item for item in findings)
    assert any("control_intent_contract: must be null" in item for item in findings)


def test_direct_actuation_and_implementation_findings(tmp_path: Path) -> None:
    """The adapter can neither actuate nor claim an implementation."""
    adapter = dict(load_json_object(MANIFEST)["control_adapter"])
    adapter["direct_actuation"] = True
    adapter["implementation"] = "src/adapter.py"
    findings = validate_manifest(
        write_manifest(tmp_path, mutated(control_adapter=adapter)), None
    )
    assert any("direct_actuation: must be false" in item for item in findings)
    assert any("implementation: must be null" in item for item in findings)


def test_missing_protection_statement(tmp_path: Path) -> None:
    """The machine-protection statement must be a non-empty string."""
    manifest = mutated(machine_protection={"final_veto": "independent"})
    findings = validate_manifest(write_manifest(tmp_path, manifest), None)
    assert any("machine_protection.statement:" in item for item in findings)


def write_manifest_with_evidence(tmp_path: Path, manifest: dict[str, Any]) -> Path:
    """Serialise a manifest and satisfy its evidence pointers on disk."""
    (tmp_path / "VALIDATION.md").write_text("# evidence\n", encoding="utf-8")
    return write_manifest(tmp_path, manifest)


def test_populated_capabilities_pass_with_resolvable_evidence(
    tmp_path: Path,
) -> None:
    """A well-formed implemented-state inventory yields no findings."""
    path = write_manifest_with_evidence(tmp_path, mutated())
    assert validate_manifest(path, None) == []


@pytest.mark.parametrize(
    ("capabilities", "maturity", "fragment"),
    [
        ([], "computational_prototype", "must be a non-empty list"),
        (["text"], "computational_prototype", "capabilities[0]: must be an object"),
        (
            [
                {
                    "identifier": "device_configuration_model",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                    "surprise": 1,
                }
            ],
            "computational_prototype",
            "unknown fields",
        ),
        (
            [
                {
                    "identifier": "Bad-Name",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                }
            ],
            "computational_prototype",
            "invalid identifier",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "architecture_only",
                    "evidence_pointer": "VALIDATION.md#x",
                }
            ],
            "computational_prototype",
            "evidence_maturity: must be one of",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "",
                }
            ],
            "computational_prototype",
            "evidence_pointer: must be a non-empty string",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "ABSENT.md#x",
                }
            ],
            "computational_prototype",
            "no committed file behind",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                    "contract_version": "",
                }
            ],
            "computational_prototype",
            "contract_version",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                },
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                },
            ],
            "computational_prototype",
            "identifiers must be unique",
        ),
        (
            [
                {
                    "identifier": "model_a",
                    "evidence_maturity": "computational_prototype",
                    "evidence_pointer": "VALIDATION.md#x",
                }
            ],
            "benchmark_validated",
            "ceiling rule",
        ),
    ],
)
def test_capability_inventory_violations(
    tmp_path: Path,
    capabilities: list[Any],
    maturity: str,
    fragment: str,
) -> None:
    """Each capability-inventory violation yields its precise finding."""
    manifest = mutated(capabilities=capabilities, evidence_maturity=maturity)
    path = write_manifest_with_evidence(tmp_path, manifest)
    findings = validate_manifest(path, None)
    assert any(fragment in finding for finding in findings), findings


def test_architecture_only_with_empty_inventory_is_valid(tmp_path: Path) -> None:
    """An architecture-only manifest with empty capabilities passes."""
    manifest = mutated(
        evidence_maturity="architecture_only",
        capabilities=[],
        studio_integration={
            "state": "not_federated",
            "reason": "architecture_only: no implemented capability exists",
            "descriptor": "studio/portfolio-descriptor.json",
        },
    )
    findings = validate_manifest(write_manifest(tmp_path, manifest), None)
    assert findings == []


def test_valid_contract_version_is_accepted(tmp_path: Path) -> None:
    """A non-empty contract version on a capability item is valid."""
    manifest = mutated(
        capabilities=[
            {
                "identifier": "device_configuration_model",
                "evidence_maturity": "computational_prototype",
                "evidence_pointer": "VALIDATION.md#x",
                "contract_version": "1.0.0",
            }
        ]
    )
    path = write_manifest_with_evidence(tmp_path, manifest)
    assert validate_manifest(path, None) == []


def test_map_cross_check_rejects_unreadable_map(tmp_path: Path) -> None:
    """A missing map file fails the cross-check instead of skipping it."""
    findings = validate_manifest(MANIFEST, tmp_path / "absent-map.json")
    assert any(finding.startswith("map: cannot load") for finding in findings)


def test_map_cross_check_rejects_unmapped_project(tmp_path: Path) -> None:
    """A project outside the machine map is refused."""
    map_path = tmp_path / "map.json"
    map_path.write_text(
        json.dumps(
            {
                "planned_repositories": ["OTHER-CORE"],
                "existing_repositories": [],
                "configuration_assignments": {},
                "source_registry": {"version": "1.0.0", "digest_sha256": "0" * 64},
            }
        ),
        encoding="utf-8",
    )
    findings = validate_manifest(MANIFEST, map_path)
    assert any("is not a mapped repository" in finding for finding in findings)


def test_map_cross_check_rejects_assignment_and_pin_drift(tmp_path: Path) -> None:
    """Configuration and registry-pin drift against the map is refused."""
    map_path = tmp_path / "map.json"
    map_path.write_text(
        json.dumps(
            {
                "planned_repositories": ["SCPN-Z-PINCH-CORE"],
                "existing_repositories": [],
                "configuration_assignments": {
                    "conventional_tokamak": "SCPN-Z-PINCH-CORE"
                },
                "source_registry": {"version": "2.0.0", "digest_sha256": "0" * 64},
            }
        ),
        encoding="utf-8",
    )
    findings = validate_manifest(MANIFEST, map_path)
    assert any("!= assigned" in finding for finding in findings)
    assert any("registry version" in finding for finding in findings)
    assert any("digest does not match" in finding for finding in findings)


def test_main_pass_and_fail_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command-line interface reports PASS with 0 and FAIL with 1."""
    assert main([str(MANIFEST)]) == 0
    assert "reactor-domain: PASS" in capsys.readouterr().out
    broken = write_manifest(tmp_path, mutated(license="MIT"))
    assert main([str(broken)]) == 1
    output = capsys.readouterr().out
    assert "reactor-domain: FAIL" in output
    assert "- license:" in output
