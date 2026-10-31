# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — installed-wheel contract check

"""Exercise the installed package from outside the source checkout.

The installed-wheel workflow builds the wheel, installs it into a clean
environment and runs this script with ``python -I`` from a directory
outside the checkout. The script fails closed unless the package was
imported from the environment rather than the checkout, ships its
``py.typed`` marker, reports matching installed metadata with the pinned
kernel dependency, and serves the public path from canonical configuration
and geometry documents through level-0 physics to the tessellated device
model, and one B-rep model must be built and exported (the CAD back-end is
a required dependency of this package).
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from pathlib import Path
from typing import Final

DISTRIBUTION: Final = "scpn-z-pinch-core"
PACKAGE: Final = "scpn_z_pinch_core"
KERNEL_REQUIREMENT: Final = "scpn-reactor-kernels"

CONFIGURATION_DOCUMENT: Final = (
    b'{"column":{"column_length_m":0.5,"column_radius_m":0.01},"discharge":'
    b'{"ion_line_density_per_m":1e+18,"peak_current_ma":0.5},'
    b'"flow_shear_per_s":10000000.0,"identifier":"sheared_flow_z_pinch",'
    b'"registry":{"digest_sha256":'
    b'"786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090",'
    b'"version":"1.0.0"}}\n'
)
"""A synthetic canonical configuration; it describes no real machine."""

GEOMETRY_DOCUMENT: Final = (
    b'{"acceleration_region_length_m":1.0,"assembly_region_length_m":0.6,'
    b'"chamber_inner_radius_m":0.15,"chamber_wall_thickness_m":0.01,'
    b'"end_wall_thickness_m":0.02,"inner_electrode_radius_m":0.05,'
    b'"outer_electrode_inner_radius_m":0.1,"outer_electrode_wall_thickness_m":0.01}\n'
)
"""A synthetic canonical device geometry in metres."""


def layout_findings(package_dir: Path, checkout: Path) -> list[str]:
    """Check where the package was imported from and what it ships.

    Parameters
    ----------
    package_dir
        Directory of the imported package.
    checkout
        Source checkout the installed package must not come from.

    Returns
    -------
    list[str]
        Findings; empty when the package lies outside the checkout and
        carries its ``py.typed`` marker.
    """
    return failed(
        [
            (
                not package_dir.resolve().is_relative_to(checkout.resolve()),
                f"{PACKAGE} imported from the checkout: {package_dir}",
            ),
            (
                (package_dir / "py.typed").is_file(),
                f"{PACKAGE} ships no py.typed marker",
            ),
        ]
    )


def failed(checks: list[tuple[bool, str]]) -> list[str]:
    """Return the messages of the checks that did not hold.

    Parameters
    ----------
    checks
        Pairs of an outcome and the finding reported when it is false.

    Returns
    -------
    list[str]
        Findings in check order.
    """
    return [message for holds, message in checks if not holds]


def metadata_findings(
    version: str,
    distribution_name: str = DISTRIBUTION,
    required: str = KERNEL_REQUIREMENT,
) -> list[str]:
    """Check the installed distribution metadata.

    Parameters
    ----------
    version
        ``__version__`` of the imported package.
    distribution_name
        Installed distribution to read.
    required
        Requirement the distribution must declare.

    Returns
    -------
    list[str]
        Findings; empty when the distribution is installed with the same
        version and declares the required dependency.
    """
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return [f"{distribution_name} is not installed"]
    requirements = distribution.requires or []
    return failed(
        [
            (
                distribution.version == version,
                f"installed version {distribution.version} != package {version}",
            ),
            (
                any(item.startswith(required) for item in requirements),
                f"{distribution_name} does not require {required}",
            ),
        ]
    )


def public_path_findings() -> list[str]:
    """Serve the public path through the installed package.

    Returns
    -------
    list[str]
        Findings; empty when every promised capability works.
    """
    from scpn_z_pinch_core import configuration_from_bytes
    from scpn_z_pinch_core.geometry import (
        DEFAULT_REFERENCE_MESH_SEGMENTS,
        build_device_cad,
        build_device_model,
        geometry_from_bytes,
    )
    from scpn_z_pinch_core.physics import (
        DEUTERON_MASS_KG,
        IDEAL_MONATOMIC_ADIABATIC_INDEX,
        ModelInputs,
        level0_physics,
    )

    configuration = configuration_from_bytes(CONFIGURATION_DOCUMENT)
    geometry = geometry_from_bytes(GEOMETRY_DOCUMENT)
    inputs = ModelInputs(
        ion_mass_kg=DEUTERON_MASS_KG,
        mean_ion_charge=1.0,
        axial_wavenumber_per_m=200.0,
        adiabatic_index=IDEAL_MONATOMIC_ADIABATIC_INDEX,
        coulomb_logarithm=10.0,
        kadomtsev_radius_ratio=1.0,
    )
    segments = DEFAULT_REFERENCE_MESH_SEGMENTS
    record = level0_physics(configuration, inputs).canonical_bytes()
    model = build_device_model(configuration, geometry, segments).digest_sha256()
    cad = build_device_cad(configuration, geometry)
    return failed(
        [
            (
                configuration.canonical_bytes() == CONFIGURATION_DOCUMENT,
                "configuration did not round-trip byte for byte",
            ),
            (
                geometry.canonical_bytes() == GEOMETRY_DOCUMENT,
                "geometry did not round-trip byte for byte",
            ),
            (
                record == level0_physics(configuration, inputs).canonical_bytes(),
                "level-0 record is not deterministic",
            ),
            (
                model
                == build_device_model(
                    configuration, geometry, segments
                ).digest_sha256(),
                "tessellated model is not deterministic",
            ),
            (bool(cad.step_data), "CAD model exported no STEP data"),
            (
                cad.configuration_digest_sha256 == configuration.digest_sha256(),
                "CAD model is bound to another configuration",
            ),
        ]
    )


def check_installed(checkout: Path) -> list[str]:
    """Run every installed-package check for one environment.

    Parameters
    ----------
    checkout
        Source checkout the package must not be imported from.

    Returns
    -------
    list[str]
        All findings; empty when the installed package meets its contract.
    """
    package = importlib.import_module(PACKAGE)
    package_dir = Path(package.__file__ or "").parent
    findings = layout_findings(package_dir, checkout)
    findings += metadata_findings(str(package.__version__))
    findings += public_path_findings()
    return findings


def report(findings: list[str]) -> int:
    """Print the outcome of one environment and return its exit status.

    Parameters
    ----------
    findings
        Findings of :func:`check_installed`.

    Returns
    -------
    int
        ``0`` without findings, else ``1``.
    """
    if findings:
        print("installed-package: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print("installed-package: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the installed-package check from the command line.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when the installed package meets its contract, else ``1``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args(argv)
    return report(check_installed(args.checkout))


if __name__ == "__main__":
    sys.exit(main())
