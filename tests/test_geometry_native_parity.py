# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device model parity against the library's native kernels

"""Bit-exact parity of the device model against the pinned library's native kernels.

The device model is composed on the Python floor of the shared kernel
library; this file proves that every body it builds agrees bit for bit
with the library's native tessellation and mesh measures, so the consumer
inherits the library's parity rather than re-proving the kernels. Skipped
hermetically when the library's optional native module is absent; when
present, every vertex coordinate, face index and measure is compared by
float64 bit pattern, never by tolerance. All inputs are synthetic.
"""

from __future__ import annotations

import pytest

from geometry_fixtures import (
    bits,
    reference_configuration,
    reference_geometry,
    stream_bits,
)
from scpn_z_pinch_core.geometry import build_device_model

native = pytest.importorskip("scpn_reactor_kernels_native")


def native_bodies(segments: int) -> list[tuple[list[float], list[int]]]:
    """Tessellate the six device bodies through the library's native kernels."""
    geometry = reference_geometry()
    column = reference_configuration().column
    z_end = geometry.acceleration_region_length_m
    z_device = geometry.device_length_m
    streams = (
        native.tessellate_cylinder(
            geometry.inner_electrode_radius_m, 0.0, z_end, segments
        ),
        native.tessellate_annular_tube(
            geometry.outer_electrode_inner_radius_m,
            geometry.outer_electrode_outer_radius_m,
            0.0,
            z_device,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.chamber_inner_radius_m,
            geometry.chamber_outer_radius_m,
            0.0,
            z_device,
            segments,
        ),
        native.tessellate_cylinder(
            geometry.chamber_outer_radius_m,
            0.0 - geometry.end_wall_thickness_m,
            0.0,
            segments,
        ),
        native.tessellate_cylinder(
            geometry.chamber_outer_radius_m,
            z_device,
            z_device + geometry.end_wall_thickness_m,
            segments,
        ),
        native.tessellate_cylinder(
            column.column_radius_m, z_end, z_end + column.column_length_m, segments
        ),
    )
    return [(list(vertices), list(faces)) for vertices, faces in streams]


@pytest.mark.parametrize("segments", [8, 32, 64])
def test_every_body_is_bit_exact_with_the_library_native_kernels(
    segments: int,
) -> None:
    """Vertices, faces, volume and area of all six bodies agree bit for bit."""
    model = build_device_model(
        reference_configuration(), reference_geometry(), segments
    )
    bodies = native_bodies(segments)
    for mesh, (vertices, faces) in zip(model.meshes, bodies, strict=True):
        floor = [c for v in mesh.vertices for c in v]
        assert stream_bits(floor) == stream_bits(vertices)
        assert [i for f in mesh.faces for i in f] == faces
        volume = native.mesh_volume(vertices, faces)
        assert bits(volume) == bits(mesh.signed_volume_m3())
        assert bits(native.mesh_area(vertices, faces)) == bits(mesh.surface_area_m2())
