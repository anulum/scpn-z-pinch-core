# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Studio portfolio descriptor derivation

"""Derive the Studio portfolio descriptor from the reactor-domain manifest.

The descriptor is a deterministic projection: it copies scientific identity,
registry pins, authority boundaries, and the ``not_federated`` lifecycle
state from ``reactor-domain.json`` and embeds the manifest's SHA-256 so any
divergence between the two files is detectable. It never adds executable
verbs, evidence types, demos, health routes, pricing, or user-interface
modules — Studio must not be able to read more authority out of the
descriptor than the manifest grants. ``--check`` fails when the committed
descriptor differs byte-for-byte from a fresh derivation; ``--write``
regenerates it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Final

from manifest_io import canonical_json_bytes, load_json_object, sha256_of_file

DESCRIPTOR_SCHEMA: Final = "scpn.studio-portfolio-descriptor.v1"
DESCRIPTOR_SCHEMA_VERSION: Final = "1.0.0"


def derive_descriptor(manifest_path: Path) -> dict[str, Any]:
    """Build the descriptor object from one reactor-domain manifest.

    Parameters
    ----------
    manifest_path
        Manifest file to project.

    Returns
    -------
    dict[str, Any]
        The descriptor object, ready for canonical serialisation.

    Raises
    ------
    OSError
        If the manifest cannot be read.
    ValueError
        If the manifest is not a valid JSON object.
    """
    manifest = load_json_object(manifest_path)
    profile = manifest.get("spo_semantic_profile", {})
    adapter = manifest.get("control_adapter", {})
    studio = manifest.get("studio_integration", {})
    registry = manifest.get("spo_registry", {})
    return {
        "schema": DESCRIPTOR_SCHEMA,
        "schema_version": DESCRIPTOR_SCHEMA_VERSION,
        "source": {
            "manifest_path": manifest_path.name,
            "manifest_schema": manifest.get("schema"),
            "manifest_schema_version": manifest.get("schema_version"),
            "manifest_sha256": sha256_of_file(manifest_path),
        },
        "project": manifest.get("project"),
        "research_group": manifest.get("research_group"),
        "device_family": manifest.get("device_family"),
        "confinement_family": manifest.get("confinement_family"),
        "spo_registry": {
            "version": registry.get("version"),
            "digest_sha256": registry.get("digest_sha256"),
        },
        "configurations": manifest.get("configurations"),
        "evidence_maturity": manifest.get("evidence_maturity"),
        "capabilities": manifest.get("capabilities"),
        "control_adapter": {
            "identifier": adapter.get("identifier"),
            "contract_version": adapter.get("contract_version"),
        },
        "authority": {
            "allowed_action_authority": "none",
            "spo_semantic_mode": profile.get("mode"),
            "spo_actionable": profile.get("actionable"),
            "machine_protection_final_veto": True,
        },
        "non_claims": manifest.get("non_claims"),
        "lifecycle": {
            "state": studio.get("state"),
            "reason": studio.get("reason"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Run the descriptor derivation command-line interface.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` on success (in-sync check or completed write), ``1`` on
        drift or derivation failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("reactor-domain.json"))
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=Path("studio/portfolio-descriptor.json"),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        derived = canonical_json_bytes(derive_descriptor(args.manifest))
    except (OSError, ValueError) as exc:
        print(f"studio-descriptor: FAIL {exc}")
        return 1
    if args.write:
        args.descriptor.parent.mkdir(parents=True, exist_ok=True)
        args.descriptor.write_bytes(derived)
        print(f"studio-descriptor: wrote {args.descriptor}")
        return 0
    try:
        committed = args.descriptor.read_bytes()
    except OSError as exc:
        print(f"studio-descriptor: FAIL cannot read committed descriptor: {exc}")
        return 1
    if committed != derived:
        print("studio-descriptor: FAIL drift between manifest and descriptor")
        return 1
    print("studio-descriptor: PASS in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
