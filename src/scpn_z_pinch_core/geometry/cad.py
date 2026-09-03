# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device CAD model record (tier G2)

"""Tier-G2 device CAD model: B-rep solids of one validated design.

The model composes the validated configuration (plasma column) and the
validated device geometry (electrodes, chamber, end walls) into the same
six named bodies as the tier-G1 model (:func:`build_device_model`), built
as exact B-rep solids of revolution by the pinned third-party OpenCASCADE
kernel through the shared kernel library (``scpn_reactor_kernels.cad``,
kernels ``cad_brep_solids``, ``cad_step_export``, ``cad_faceting``; ADR
0008). OpenCASCADE is not the bit-exact floor: every body is checked
fail-closed against its analytic closed form (volume and surface area
within the library's declared relative tolerance ``1e-9``), the faceted
B-rep volume is checked against the declared deflection deficit bound and
against the tier-G1 mesh at the declared reference segment count within
the exact polygon-deficit bound, and the STEP export is the library's
normalised deterministic writer. The canonical record carries the schema
identity, the units and axis convention, both source digests, the declared
deflections and reference segment count, the back-end versions, the
assembly manifest and its digest, the STEP digest and the per-body
evidence; the SHA-256 of that record identifies the exact model. No body
carries an engineering property and no value describes a real machine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Final

from scpn_reactor_kernels.cad import (
    MANIFEST_SCHEMA,
    MEASURE_TOLERANCE,
    BrepAssembly,
    annular_tube_brep,
    backend_versions,
    cylinder_solid_brep,
    deflection_volume_bound,
    facet_assembly,
    inscribed_polygon_area_ratio,
)
from scpn_reactor_kernels.cad import (
    step_bytes as _normalised_step_bytes,
)
from scpn_reactor_kernels.cad import (
    step_sha256 as _step_bytes_sha256,
)
from scpn_reactor_kernels.errors import CadError, GeometryError
from scpn_reactor_kernels.geometry import TriangleMesh, require_segments

from scpn_z_pinch_core.configuration import DeviceConfiguration
from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry.device import DeviceGeometry
from scpn_z_pinch_core.geometry.model import (
    BODY_CHAMBER_WALL,
    BODY_END_WALL_DOWNSTREAM,
    BODY_END_WALL_UPSTREAM,
    BODY_INNER_ELECTRODE,
    BODY_NAMES,
    BODY_OUTER_ELECTRODE,
    BODY_PLASMA_COLUMN,
    MATERIAL_CHAMBER_WALL,
    MATERIAL_ELECTRODE_CONDUCTOR,
    MATERIAL_PLASMA,
    MODEL_UNITS,
    ROLE_ELECTRODE,
    ROLE_PLASMA,
    ROLE_VACUUM_BOUNDARY,
    build_device_model,
)

CAD_MODEL_SCHEMA: Final = "scpn.z-pinch-cad-model.v1"
CAD_MODEL_SCHEMA_VERSION: Final = "1.0.0"
CAD_MODEL_NON_CLAIMS: Final = (
    "B-rep solids of the same synthetic design, built by the pinned "
    "third-party OpenCASCADE kernel and checked against the analytic closed "
    "forms; not an engineering model",
    "no material property, load, field or neutronic quantity is carried",
    "STEP bytes are deterministic only within one pinned back-end "
    "environment; identity across OpenCASCADE or gmsh versions is not claimed",
    "no value describes or validates any real machine",
)

#: Reference segment count of the tier-G1 mesh the faceted B-rep is
#: compared against.
DEFAULT_REFERENCE_MESH_SEGMENTS: Final = 8
#: Declared mesher deflections of the pilot record.
DEFAULT_LINEAR_DEFLECTION_M: Final = 1.0e-4
DEFAULT_ANGULAR_DEFLECTION_RAD: Final = 0.1


@dataclass(frozen=True, slots=True)
class BodyCADEvidence:
    """Per-body evidence of one B-rep body against its analytic form.

    Parameters
    ----------
    name, role, material_identifier
        Body identity, identical to the tier-G1 body of the same name.
    analytic_volume_m3, brep_volume_m3
        Closed-form volume and the B-rep kernel's measure.
    volume_relative_error
        ``|V_brep - V_analytic| / V_analytic``; must not exceed the
        library's declared measure tolerance ``1e-9``.
    analytic_surface_area_m2, brep_surface_area_m2
        Closed-form surface area and the B-rep kernel's measure.
    surface_area_relative_error
        ``|A_brep - A_analytic| / A_analytic``; same tolerance.
    faceted_volume_m3
        Signed volume of the faceted B-rep (closed mesh).
    faceted_volume_relative_deficit
        ``(V_analytic - V_faceted) / V_analytic`` of the faceted body.
    faceted_volume_deficit_bound
        Declared bound ``2 d / r`` of the chord deficit at the body's
        smallest circular radius ``r`` and the linear deflection ``d``.
    reference_mesh_volume_m3
        Signed volume of the tier-G1 mesh at the reference segment count.
    mesh_volume_relative_difference
        ``|V_faceted - V_reference| / V_analytic``.
    mesh_volume_difference_bound
        Exact polygon-deficit bound ``1 - (n / (2 pi)) sin(2 pi / n)`` of
        the reference segment count ``n``.

    Raises
    ------
    DeviceGeometryError
        If a declared bound is violated.
    """

    name: str
    role: str
    material_identifier: str
    analytic_volume_m3: float
    brep_volume_m3: float
    volume_relative_error: float
    analytic_surface_area_m2: float
    brep_surface_area_m2: float
    surface_area_relative_error: float
    faceted_volume_m3: float
    faceted_volume_relative_deficit: float
    faceted_volume_deficit_bound: float
    reference_mesh_volume_m3: float
    mesh_volume_relative_difference: float
    mesh_volume_difference_bound: float

    def __post_init__(self) -> None:
        """Refuse evidence that violates a declared bound.

        Raises
        ------
        DeviceGeometryError
            If a relative error exceeds the measure tolerance or a deficit
            exceeds its declared bound.
        """
        if self.volume_relative_error > MEASURE_TOLERANCE:
            raise DeviceGeometryError(
                f"{self.name}.volume_relative_error: must not exceed "
                f"{MEASURE_TOLERANCE!r}, got {self.volume_relative_error!r}"
            )
        if self.surface_area_relative_error > MEASURE_TOLERANCE:
            raise DeviceGeometryError(
                f"{self.name}.surface_area_relative_error: must not exceed "
                f"{MEASURE_TOLERANCE!r}, got {self.surface_area_relative_error!r}"
            )
        if self.faceted_volume_relative_deficit > self.faceted_volume_deficit_bound:
            raise DeviceGeometryError(
                f"{self.name}.faceted_volume_relative_deficit: must not exceed "
                f"the declared bound {self.faceted_volume_deficit_bound!r}, got "
                f"{self.faceted_volume_relative_deficit!r}"
            )
        if self.mesh_volume_relative_difference > self.mesh_volume_difference_bound:
            raise DeviceGeometryError(
                f"{self.name}.mesh_volume_relative_difference: must not exceed "
                f"the polygon-deficit bound {self.mesh_volume_difference_bound!r}, "
                f"got {self.mesh_volume_relative_difference!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the evidence to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Identity, analytic and measured values, and every declared
            bound with the measured value next to it.
        """
        return {
            "name": self.name,
            "role": self.role,
            "material_identifier": self.material_identifier,
            "analytic_volume_m3": self.analytic_volume_m3,
            "brep_volume_m3": self.brep_volume_m3,
            "volume_relative_error": self.volume_relative_error,
            "analytic_surface_area_m2": self.analytic_surface_area_m2,
            "brep_surface_area_m2": self.brep_surface_area_m2,
            "surface_area_relative_error": self.surface_area_relative_error,
            "faceted_volume_m3": self.faceted_volume_m3,
            "faceted_volume_relative_deficit": self.faceted_volume_relative_deficit,
            "faceted_volume_deficit_bound": self.faceted_volume_deficit_bound,
            "reference_mesh_volume_m3": self.reference_mesh_volume_m3,
            "mesh_volume_relative_difference": self.mesh_volume_relative_difference,
            "mesh_volume_difference_bound": self.mesh_volume_difference_bound,
        }


@dataclass(frozen=True, slots=True)
class DeviceModelCAD:
    """The B-rep device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    reference_mesh_segments
        Segment count of the tier-G1 reference mesh of the comparison.
    linear_deflection_m, angular_deflection_rad
        Declared mesher deflections of the faceting evidence.
    backend_versions
        Versions of the pinned CAD back-ends (``cadquery``, ``ocp``,
        ``gmsh``) as reported by the library.
    assembly_manifest
        The library's B-rep assembly manifest record.
    step_sha256
        SHA-256 of the normalised STEP export of the assembly.
    bodies
        Per-body evidence in the fixed order of :data:`BODY_NAMES`.
    step_data
        The normalised STEP bytes (the digested export).
    faceted_meshes
        The faceted closed meshes, one per body, in the fixed order.

    Raises
    ------
    DeviceGeometryError
        If the body inventory differs from :data:`BODY_NAMES`, the segment
        rule or the deflection rule is violated, the manifest is foreign,
        or the STEP digest is not a 64-hex value.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    reference_mesh_segments: int
    linear_deflection_m: float
    angular_deflection_rad: float
    backend_versions: dict[str, str]
    assembly_manifest: dict[str, Any]
    step_sha256: str
    bodies: tuple[BodyCADEvidence, ...]
    step_data: bytes = field(compare=False, repr=False)
    faceted_meshes: tuple[TriangleMesh, ...] = field(
        compare=False, repr=False, default=()
    )

    def __post_init__(self) -> None:
        """Validate the model inventory and declared parameters.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        names = tuple(body.name for body in self.bodies)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"bodies: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )
        try:
            require_segments(self.reference_mesh_segments)
        except GeometryError as exc:
            raise DeviceGeometryError(str(exc)) from exc
        for name, value in (
            ("linear_deflection_m", self.linear_deflection_m),
            ("angular_deflection_rad", self.angular_deflection_rad),
        ):
            if not (value > 0.0) or value != value or value == float("inf"):
                raise DeviceGeometryError(
                    f"{name}: must be finite and strictly positive, got {value!r}"
                )
        if self.assembly_manifest.get("schema") != MANIFEST_SCHEMA:
            raise DeviceGeometryError(
                f"assembly_manifest.schema: must be {MANIFEST_SCHEMA!r}"
            )
        if self.assembly_manifest.get("body_count") != len(BODY_NAMES):
            raise DeviceGeometryError(
                f"assembly_manifest.body_count: must be {len(BODY_NAMES)}, got "
                f"{self.assembly_manifest.get('body_count')!r}"
            )
        if len(self.step_sha256) != 64 or not all(
            character in "0123456789abcdef" for character in self.step_sha256
        ):
            raise DeviceGeometryError(
                "step_sha256: must be 64 lowercase hexadecimal characters"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, declared
            deflections and reference segment count, back-end versions, the
            assembly manifest, the STEP digest and every body evidence.
        """
        return {
            "schema": CAD_MODEL_SCHEMA,
            "schema_version": CAD_MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(CAD_MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "reference_mesh_segments": self.reference_mesh_segments,
            "linear_deflection_m": self.linear_deflection_m,
            "angular_deflection_rad": self.angular_deflection_rad,
            "backend_versions": dict(self.backend_versions),
            "assembly_manifest": self.assembly_manifest,
            "step_sha256": self.step_sha256,
            "bodies": [body.to_record() for body in self.bodies],
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


def _body_evidence(
    body: Any,
    smallest_radius_m: float,
    faceted: TriangleMesh,
    reference_mesh: TriangleMesh,
    linear_deflection_m: float,
    segments: int,
) -> BodyCADEvidence:
    """Compute the fail-closed evidence of one body.

    Parameters
    ----------
    body
        The B-rep body (a library ``BrepBody``).
    smallest_radius_m
        The body's smallest circular radius (the deficit-bound radius).
    faceted
        The faceted closed mesh of the body.
    reference_mesh
        The tier-G1 mesh of the body at the reference segment count.
    linear_deflection_m
        The mesher's linear deflection.
    segments
        The reference mesh segment count.

    Returns
    -------
    BodyCADEvidence
        The checked evidence.
    """
    faceted_volume = faceted.signed_volume_m3()
    reference_volume = reference_mesh.signed_volume_m3()
    analytic_volume = body.analytic_volume_m3
    return BodyCADEvidence(
        name=body.name,
        role=body.role,
        material_identifier=body.material_identifier,
        analytic_volume_m3=analytic_volume,
        brep_volume_m3=body.volume_m3,
        volume_relative_error=body.volume_relative_error(),
        analytic_surface_area_m2=body.analytic_surface_area_m2,
        brep_surface_area_m2=body.surface_area_m2,
        surface_area_relative_error=body.surface_area_relative_error(),
        faceted_volume_m3=faceted_volume,
        faceted_volume_relative_deficit=(analytic_volume - faceted_volume)
        / analytic_volume,
        faceted_volume_deficit_bound=deflection_volume_bound(
            smallest_radius_m, linear_deflection_m
        ),
        reference_mesh_volume_m3=reference_volume,
        mesh_volume_relative_difference=abs(faceted_volume - reference_volume)
        / analytic_volume,
        mesh_volume_difference_bound=1.0 - inscribed_polygon_area_ratio(segments),
    )


def build_device_cad(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    segments: int = DEFAULT_REFERENCE_MESH_SEGMENTS,
    linear_deflection_m: float = DEFAULT_LINEAR_DEFLECTION_M,
    angular_deflection_rad: float = DEFAULT_ANGULAR_DEFLECTION_RAD,
) -> DeviceModelCAD:
    """Build the B-rep device model of a validated design.

    Parameters
    ----------
    configuration
        Validated device configuration (plasma column and discharge).
    geometry
        Validated device geometry (electrodes, chamber, end walls).
    segments
        Segment count of the tier-G1 reference mesh of the faceting
        comparison; at least 8, multiple of 8.
    linear_deflection_m
        Largest chord distance of the faceting to the true surface;
        strictly positive.
    angular_deflection_rad
        Largest angle between adjacent facet normals; strictly positive.

    Returns
    -------
    DeviceModelCAD
        The composed, fail-closed checked model with its STEP export.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid, the plasma column violates the
        bore or assembly-region invariants, a deflection is invalid, or a
        body violates a declared evidence bound (the library's refusals
        are re-raised under the device error type with their messages);
        :class:`~scpn_reactor_kernels.errors.CadUnavailableError` if the
        optional CAD back-end is absent.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    reference = build_device_model(configuration, geometry, segments)
    column = configuration.column
    z_electrode_end = geometry.acceleration_region_length_m
    z_device_end = geometry.device_length_m
    try:
        assembly = BrepAssembly(
            (
                cylinder_solid_brep(
                    geometry.inner_electrode_radius_m,
                    0.0,
                    z_electrode_end,
                    BODY_INNER_ELECTRODE,
                    ROLE_ELECTRODE,
                    MATERIAL_ELECTRODE_CONDUCTOR,
                ),
                annular_tube_brep(
                    geometry.outer_electrode_inner_radius_m,
                    geometry.outer_electrode_outer_radius_m,
                    0.0,
                    z_device_end,
                    BODY_OUTER_ELECTRODE,
                    ROLE_ELECTRODE,
                    MATERIAL_ELECTRODE_CONDUCTOR,
                ),
                annular_tube_brep(
                    geometry.chamber_inner_radius_m,
                    geometry.chamber_outer_radius_m,
                    0.0,
                    z_device_end,
                    BODY_CHAMBER_WALL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    geometry.chamber_outer_radius_m,
                    0.0 - geometry.end_wall_thickness_m,
                    0.0,
                    BODY_END_WALL_UPSTREAM,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    geometry.chamber_outer_radius_m,
                    z_device_end,
                    z_device_end + geometry.end_wall_thickness_m,
                    BODY_END_WALL_DOWNSTREAM,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    column.column_radius_m,
                    z_electrode_end,
                    z_electrode_end + column.column_length_m,
                    BODY_PLASMA_COLUMN,
                    ROLE_PLASMA,
                    MATERIAL_PLASMA,
                ),
            )
        )
        faceted = facet_assembly(assembly, linear_deflection_m, angular_deflection_rad)
    except CadError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    smallest_radii = (
        geometry.inner_electrode_radius_m,
        geometry.outer_electrode_inner_radius_m,
        geometry.chamber_inner_radius_m,
        geometry.chamber_outer_radius_m,
        geometry.chamber_outer_radius_m,
        column.column_radius_m,
    )
    bodies = tuple(
        _body_evidence(
            body, smallest_radius, mesh, reference_mesh, linear_deflection_m, segments
        )
        for body, smallest_radius, mesh, reference_mesh in zip(
            assembly.bodies, smallest_radii, faceted, reference.meshes, strict=True
        )
    )
    manifest = assembly.manifest()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }
    step_data = _normalised_step_bytes(assembly, extras)
    return DeviceModelCAD(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        reference_mesh_segments=segments,
        linear_deflection_m=linear_deflection_m,
        angular_deflection_rad=angular_deflection_rad,
        backend_versions=backend_versions(),
        assembly_manifest=manifest,
        step_sha256=_step_bytes_sha256(step_data),
        bodies=bodies,
        step_data=step_data,
        faceted_meshes=faceted,
    )
