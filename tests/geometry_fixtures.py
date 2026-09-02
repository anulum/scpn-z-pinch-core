# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — shared synthetic fixtures of the geometry tests

"""Synthetic configuration and geometry shared by the geometry tests.

Every value is a test fixture; none describes a real machine.
"""

from __future__ import annotations

import struct

from scpn_z_pinch_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_z_pinch_core.geometry import DeviceGeometry
from scpn_z_pinch_core.parameters import Discharge, PinchColumn

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"


def reference_configuration() -> DeviceConfiguration:
    """Return the synthetic sheared-flow configuration of the geometry tests."""
    return DeviceConfiguration(
        identifier="sheared_flow_z_pinch",
        column=PinchColumn(column_radius_m=0.01, column_length_m=0.5),
        discharge=Discharge(peak_current_ma=0.5, ion_line_density_per_m=1.0e18),
        flow_shear_per_s=1.0e7,
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def reference_geometry() -> DeviceGeometry:
    """Return the synthetic coaxial geometry of the geometry tests."""
    return DeviceGeometry(
        inner_electrode_radius_m=0.05,
        outer_electrode_inner_radius_m=0.1,
        outer_electrode_wall_thickness_m=0.01,
        acceleration_region_length_m=1.0,
        assembly_region_length_m=0.6,
        chamber_inner_radius_m=0.15,
        chamber_wall_thickness_m=0.01,
        end_wall_thickness_m=0.02,
    )


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


def stream_bits(values: list[float]) -> bytes:
    """Return the concatenated bit patterns of a float stream."""
    return b"".join(bits(value) for value in values)
