# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — reactor-domain manifest validator

"""Fail closed when the reactor-domain manifest violates its contract.

The validator enforces the ``scpn.reactor-domain.v1`` schema, the
maturity-independent boundary invariants of the SCPN reactor family
repository standard (empty claims inventory, ``not_federated`` Studio
state, no adapter implementation, empty solver seams), the per-state
capability rules (empty at ``architecture_only``; the ratified item shape
with resolvable evidence pointers and the ADR 0002 ceiling rule at every
implemented state), the review-only SPO profile, the no-direct-actuation
adapter boundary, and the machine-protection final-veto declaration. With
``--map`` it additionally proves exact agreement with the portfolio machine
map: project membership, the assigned configuration set, and the pinned
source-registry version and digest.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Final

from manifest_io import load_json_object

SCHEMA: Final = "scpn.reactor-domain.v1"
SCHEMA_VERSION: Final = "1.0.0"
GROUP_IDENTITY: Final = "SCPN-REACTOR-SYSTEMS"
LICENSE_IDENTIFIER: Final = "AGPL-3.0-or-later"
EVIDENCE_STATES: Final = (
    "architecture_only",
    "computational_prototype",
    "benchmark_validated",
    "external_code_parity",
    "experiment_correlated",
    "control_research_ready",
)
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER: Final = re.compile(r"^[a-z][a-z0-9_]*$")


def _require_string(
    manifest: dict[str, Any], field: str, findings: list[str]
) -> str | None:
    """Return one required non-empty string field or record a finding.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    field
        Dotted path of the field inside the manifest.
    findings
        Mutable finding sink.

    Returns
    -------
    str or None
        The value when present and valid, otherwise ``None``.
    """
    node: Any = manifest
    for part in field.split("."):
        if not isinstance(node, dict) or part not in node:
            findings.append(f"{field}: missing required field")
            return None
        node = node[part]
    if not isinstance(node, str) or not node:
        findings.append(f"{field}: must be a non-empty string")
        return None
    return node


def _validate_configurations(
    manifest: dict[str, Any], findings: list[str]
) -> list[str]:
    """Validate the configuration list and return it.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    findings
        Mutable finding sink.

    Returns
    -------
    list[str]
        The declared configuration identifiers (possibly empty on failure).
    """
    value = manifest.get("configurations")
    if not isinstance(value, list) or not value:
        findings.append("configurations: must be a non-empty list")
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or IDENTIFIER.fullmatch(item) is None:
            findings.append(f"configurations: invalid identifier {item!r}")
            continue
        result.append(item)
    if len(result) != len(set(result)):
        findings.append("configurations: identifiers must be unique")
    if result != sorted(result):
        findings.append("configurations: identifiers must be sorted")
    return result


def _validate_boundary_invariants(
    manifest: dict[str, Any], findings: list[str]
) -> None:
    """Enforce the boundary rules that hold at every maturity state.

    The claims inventory stays empty until a claims contract exists, the
    adapter implementation stays null until the CONTROL adapter lane
    lands, the Studio state stays ``not_federated`` until federation
    gates pass, solver seams stay empty until the family migration gate
    proves an exact replacement, and the non-claims list never empties.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    findings
        Mutable finding sink.
    """
    if manifest.get("claims") != []:
        findings.append("claims: must be [] until a claims contract exists")
    adapter = manifest.get("control_adapter")
    if isinstance(adapter, dict) and adapter.get("implementation") is not None:
        findings.append(
            "control_adapter.implementation: must be null until the "
            "CONTROL adapter lane lands"
        )
    studio = manifest.get("studio_integration")
    if not isinstance(studio, dict) or studio.get("state") != "not_federated":
        findings.append(
            "studio_integration.state: must be not_federated until "
            "federation gates pass"
        )
    non_claims = manifest.get("non_claims")
    if not isinstance(non_claims, list) or not non_claims:
        findings.append("non_claims: must be a non-empty list")
    seams = manifest.get("fusion_solver_seams")
    if not isinstance(seams, dict) or seams.get("active") != []:
        findings.append(
            "fusion_solver_seams.active: must be [] until the family "
            "migration gate proves an exact replacement"
        )


def _validate_capabilities(
    manifest: dict[str, Any],
    maturity: str,
    manifest_dir: Path,
    findings: list[str],
) -> None:
    """Validate the populated capability inventory of an implemented state.

    Enforces the ratified capability item shape, identifier hygiene and
    uniqueness, implemented-state enumeration, evidence pointers that
    resolve to committed files, and the ADR 0002 ceiling rule: the
    repository-level maturity equals the highest per-capability state.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    maturity
        Repository-level evidence-maturity state.
    manifest_dir
        Directory the evidence pointers resolve against.
    findings
        Mutable finding sink.
    """
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        findings.append(f"capabilities: must be a non-empty list at {maturity}")
        return
    allowed_keys = {
        "identifier",
        "evidence_maturity",
        "evidence_pointer",
        "contract_version",
    }
    implemented_states = EVIDENCE_STATES[1:]
    identifiers: list[str] = []
    highest = -1
    for index, item in enumerate(capabilities):
        if not isinstance(item, dict):
            findings.append(f"capabilities[{index}]: must be an object")
            continue
        unknown = sorted(set(item) - allowed_keys)
        if unknown:
            findings.append(f"capabilities[{index}]: unknown fields {unknown!r}")
        identifier = item.get("identifier")
        if not isinstance(identifier, str) or IDENTIFIER.fullmatch(identifier) is None:
            findings.append(
                f"capabilities[{index}].identifier: invalid identifier {identifier!r}"
            )
        else:
            identifiers.append(identifier)
        state = item.get("evidence_maturity")
        if state not in implemented_states:
            findings.append(
                f"capabilities[{index}].evidence_maturity: must be one of "
                f"{implemented_states!r}, got {state!r}"
            )
        else:
            highest = max(highest, EVIDENCE_STATES.index(state))
        pointer = item.get("evidence_pointer")
        if not isinstance(pointer, str) or not pointer:
            findings.append(
                f"capabilities[{index}].evidence_pointer: must be a non-empty string"
            )
        elif not (manifest_dir / pointer.split("#", maxsplit=1)[0]).is_file():
            findings.append(
                f"capabilities[{index}].evidence_pointer: no committed file "
                f"behind {pointer!r}"
            )
        contract = item.get("contract_version")
        if contract is not None and (not isinstance(contract, str) or not contract):
            findings.append(
                f"capabilities[{index}].contract_version: must be a "
                "non-empty string when present"
            )
    if len(identifiers) != len(set(identifiers)):
        findings.append("capabilities: identifiers must be unique")
    if highest >= 0 and EVIDENCE_STATES.index(maturity) != highest:
        findings.append(
            "evidence_maturity: must equal the highest capability state "
            f"{EVIDENCE_STATES[highest]!r} (ADR 0002 ceiling rule)"
        )


def _validate_safety(manifest: dict[str, Any], findings: list[str]) -> None:
    """Enforce the safety and authority boundary declarations.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    findings
        Mutable finding sink.
    """
    profile = manifest.get("spo_semantic_profile")
    if not isinstance(profile, dict):
        findings.append("spo_semantic_profile: missing required object")
    else:
        if profile.get("mode") != "review_only":
            findings.append("spo_semantic_profile.mode: must be review_only")
        if profile.get("actionable") is not False:
            findings.append("spo_semantic_profile.actionable: must be false")
        if profile.get("control_intent_contract") is not None:
            findings.append(
                "spo_semantic_profile.control_intent_contract: must be null"
            )
    adapter = manifest.get("control_adapter")
    if not isinstance(adapter, dict):
        findings.append("control_adapter: missing required object")
    elif adapter.get("direct_actuation") is not False:
        findings.append("control_adapter.direct_actuation: must be false")
    protection = manifest.get("machine_protection")
    if not isinstance(protection, dict):
        findings.append("machine_protection: missing required object")
    else:
        if protection.get("final_veto") != "independent":
            findings.append("machine_protection.final_veto: must be independent")
        statement = protection.get("statement")
        if not isinstance(statement, str) or not statement:
            findings.append("machine_protection.statement: must be a non-empty string")


def _validate_excluded_domains(manifest: dict[str, Any], findings: list[str]) -> None:
    """Validate the excluded-domain ownership table.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    findings
        Mutable finding sink.
    """
    value = manifest.get("excluded_domains")
    if not isinstance(value, list) or not value:
        findings.append("excluded_domains: must be a non-empty list")
        return
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            findings.append(f"excluded_domains[{index}]: must be an object")
            continue
        for key in ("domain", "owner"):
            field = entry.get(key)
            if not isinstance(field, str) or not field:
                findings.append(
                    f"excluded_domains[{index}].{key}: must be a non-empty string"
                )


def _validate_registry_pin(
    manifest: dict[str, Any], findings: list[str]
) -> tuple[str | None, str | None]:
    """Validate the SPO registry pin and return ``(version, digest)``.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    findings
        Mutable finding sink.

    Returns
    -------
    tuple of (str or None, str or None)
        Declared registry version and digest where valid.
    """
    version = _require_string(manifest, "spo_registry.version", findings)
    digest = _require_string(manifest, "spo_registry.digest_sha256", findings)
    if digest is not None and HEX_DIGEST.fullmatch(digest) is None:
        findings.append(
            "spo_registry.digest_sha256: must be 64 lowercase hexadecimal characters"
        )
        digest = None
    _require_string(manifest, "spo_registry.source_path", findings)
    return version, digest


def _cross_check_map(
    manifest: dict[str, Any],
    map_path: Path,
    configurations: list[str],
    registry: tuple[str | None, str | None],
    findings: list[str],
) -> None:
    """Prove exact agreement with the portfolio machine map.

    Parameters
    ----------
    manifest
        Decoded manifest object.
    map_path
        Canonical machine map location.
    configurations
        Declared configuration identifiers.
    registry
        Declared ``(version, digest)`` registry pin.
    findings
        Mutable finding sink.
    """
    try:
        machine_map = load_json_object(map_path)
    except (OSError, ValueError) as exc:
        findings.append(f"map: cannot load {map_path}: {exc}")
        return
    project = manifest.get("project")
    planned = machine_map.get("planned_repositories", [])
    existing = machine_map.get("existing_repositories", [])
    if project not in [*planned, *existing]:
        findings.append(f"map: project {project!r} is not a mapped repository")
        return
    assignments = machine_map.get("configuration_assignments", {})
    assigned = sorted(
        identifier for identifier, owner in assignments.items() if owner == project
    )
    if configurations != assigned:
        findings.append(
            f"map: configurations {configurations!r} != assigned {assigned!r}"
        )
    source = machine_map.get("source_registry", {})
    version, digest = registry
    if version is not None and version != source.get("version"):
        findings.append(
            f"map: registry version {version!r} != map {source.get('version')!r}"
        )
    if digest is not None and digest != source.get("digest_sha256"):
        findings.append("map: registry digest does not match the machine map")


def validate_manifest(manifest_path: Path, map_path: Path | None) -> list[str]:
    """Validate one reactor-domain manifest and return the findings.

    Parameters
    ----------
    manifest_path
        Manifest file to validate.
    map_path
        Optional canonical machine map for the ecosystem cross-check.

    Returns
    -------
    list[str]
        Human-readable findings; empty when the manifest is valid.
    """
    findings: list[str] = []
    try:
        manifest = load_json_object(manifest_path)
    except (OSError, ValueError) as exc:
        return [f"manifest: {exc}"]
    if manifest.get("schema") != SCHEMA:
        findings.append(f"schema: must be {SCHEMA!r}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version: must be {SCHEMA_VERSION!r}")
    _require_string(manifest, "project", findings)
    _require_string(manifest, "device_family", findings)
    _require_string(manifest, "confinement_family", findings)
    _require_string(manifest, "research_group.display_name", findings)
    group = _require_string(manifest, "research_group.coordination_identity", findings)
    if group is not None and group != GROUP_IDENTITY:
        findings.append(
            f"research_group.coordination_identity: must be {GROUP_IDENTITY!r}"
        )
    if manifest.get("license") != LICENSE_IDENTIFIER:
        findings.append(f"license: must be {LICENSE_IDENTIFIER!r}")
    maturity = manifest.get("evidence_maturity")
    _validate_boundary_invariants(manifest, findings)
    if maturity not in EVIDENCE_STATES:
        findings.append(f"evidence_maturity: unknown state {maturity!r}")
    elif maturity == "architecture_only":
        if manifest.get("capabilities") != []:
            findings.append("capabilities: must be [] at architecture_only")
    else:
        _validate_capabilities(manifest, maturity, manifest_path.parent, findings)
    owned = manifest.get("owned_domains")
    if not isinstance(owned, list) or not owned:
        findings.append("owned_domains: must be a non-empty list")
    _validate_excluded_domains(manifest, findings)
    configurations = _validate_configurations(manifest, findings)
    registry = _validate_registry_pin(manifest, findings)
    _validate_safety(manifest, findings)
    if map_path is not None:
        _cross_check_map(manifest, map_path, configurations, registry, findings)
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run the reactor-domain validator command-line interface.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when the manifest is valid, ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--map",
        type=Path,
        default=None,
        help="canonical portfolio machine map for the ecosystem cross-check",
    )
    args = parser.parse_args(argv)
    findings = validate_manifest(args.manifest, args.map)
    if findings:
        print(f"reactor-domain: FAIL findings={len(findings)}")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("reactor-domain: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
