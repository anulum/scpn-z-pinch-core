# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device 3D model record

"""Tier-G1 device 3D model: analytic bodies of one validated design.

The model composes the validated configuration (plasma column) and the
validated device geometry (electrodes, chamber, end walls) into six named,
closed, outward-oriented triangle meshes on the device axis, regenerated
deterministically from the two records. Its canonical record carries the
schema identity, the units and axis convention, both source digests, the
segment count, a summary of every body (counts, volume, area, bounding
box, mesh digest) and fixed non-claims; the SHA-256 of that record
identifies the exact model. The meshes are analytic surfaces: the plasma
body is the configuration's column, not an equilibrium boundary, and no
body carries an engineering property. The unit circle, the primitives and
the mesh contract are consumed from the pinned shared kernel library
(``scpn_reactor_kernels.geometry``, ADR 0007); this module owns only the
device composition.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    annular_tube,
    cylinder_solid,
    require_segments,
)

from scpn_z_pinch_core.configuration import DeviceConfiguration
from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry.device import DeviceGeometry

MODEL_SCHEMA: Final = "scpn.z-pinch-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the device axis, increasing downstream",
    "origin": "upstream electrode face at z = 0 on the axis",
}
MODEL_NON_CLAIMS: Final = (
    "analytic surfaces tessellated from a synthetic configuration and geometry",
    "no body is an equilibrium boundary, a CAD solid or an engineering model",
    "no material property, load, field or neutronic quantity is carried",
    "no value describes or validates any real machine",
)

ROLE_ELECTRODE: Final = "electrode"
ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_PLASMA: Final = "plasma"
MATERIAL_ELECTRODE_CONDUCTOR: Final = "electrode_conductor"
MATERIAL_CHAMBER_WALL: Final = "chamber_wall"
MATERIAL_PLASMA: Final = "plasma"

BODY_INNER_ELECTRODE: Final = "inner_electrode"
BODY_OUTER_ELECTRODE: Final = "outer_electrode"
BODY_CHAMBER_WALL: Final = "chamber_wall"
BODY_END_WALL_UPSTREAM: Final = "end_wall_upstream"
BODY_END_WALL_DOWNSTREAM: Final = "end_wall_downstream"
BODY_PLASMA_COLUMN: Final = "plasma_column"
BODY_NAMES: Final = (
    BODY_INNER_ELECTRODE,
    BODY_OUTER_ELECTRODE,
    BODY_CHAMBER_WALL,
    BODY_END_WALL_UPSTREAM,
    BODY_END_WALL_DOWNSTREAM,
    BODY_PLASMA_COLUMN,
)


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    segments
        Circumferential segment count used for every body.
    meshes
        The six bodies in the fixed order of :data:`BODY_NAMES`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :data:`BODY_NAMES`.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    segments: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body inventory.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from :data:`BODY_NAMES`.
        """
        names = tuple(mesh.name for mesh in self.meshes)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, segment
            count and every body summary.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "segments": self.segments,
            "bodies": [mesh.summary_record() for mesh in self.meshes],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def build_device_model(
    configuration: DeviceConfiguration, geometry: DeviceGeometry, segments: int
) -> DeviceModel3D:
    """Tessellate the six bodies of a validated design.

    Parameters
    ----------
    configuration
        Validated device configuration (plasma column and discharge).
    geometry
        Validated device geometry (electrodes, chamber, end walls).
    segments
        Circumferential segments for every body; at least 8, multiple of 8.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid (the library's refusal is re-raised
        under the device error type with its message), if the plasma column
        does not fit inside the outer electrode bore, or if the column is
        longer than the assembly region.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    column = configuration.column
    if column.column_radius_m >= geometry.outer_electrode_inner_radius_m:
        raise DeviceGeometryError(
            "column.column_radius_m: must be smaller than "
            "outer_electrode_inner_radius_m, got "
            f"{column.column_radius_m!r} >= {geometry.outer_electrode_inner_radius_m!r}"
        )
    if column.column_length_m > geometry.assembly_region_length_m:
        raise DeviceGeometryError(
            "column.column_length_m: must not exceed assembly_region_length_m, got "
            f"{column.column_length_m!r} > {geometry.assembly_region_length_m!r}"
        )
    z_electrode_end = geometry.acceleration_region_length_m
    z_device_end = geometry.device_length_m
    bodies = (
        (
            BODY_INNER_ELECTRODE,
            ROLE_ELECTRODE,
            MATERIAL_ELECTRODE_CONDUCTOR,
            cylinder_solid(
                geometry.inner_electrode_radius_m, 0.0, z_electrode_end, segments
            ),
        ),
        (
            BODY_OUTER_ELECTRODE,
            ROLE_ELECTRODE,
            MATERIAL_ELECTRODE_CONDUCTOR,
            annular_tube(
                geometry.outer_electrode_inner_radius_m,
                geometry.outer_electrode_outer_radius_m,
                0.0,
                z_device_end,
                segments,
            ),
        ),
        (
            BODY_CHAMBER_WALL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            annular_tube(
                geometry.chamber_inner_radius_m,
                geometry.chamber_outer_radius_m,
                0.0,
                z_device_end,
                segments,
            ),
        ),
        (
            BODY_END_WALL_UPSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            cylinder_solid(
                geometry.chamber_outer_radius_m,
                0.0 - geometry.end_wall_thickness_m,
                0.0,
                segments,
            ),
        ),
        (
            BODY_END_WALL_DOWNSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            cylinder_solid(
                geometry.chamber_outer_radius_m,
                z_device_end,
                z_device_end + geometry.end_wall_thickness_m,
                segments,
            ),
        ),
        (
            BODY_PLASMA_COLUMN,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            cylinder_solid(
                column.column_radius_m,
                z_electrode_end,
                z_electrode_end + column.column_length_m,
                segments,
            ),
        ),
    )
    meshes = tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        segments=segments,
        meshes=meshes,
    )
