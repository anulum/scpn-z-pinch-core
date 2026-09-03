# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device CAD model tests (tier G2)

"""B-rep agreement, faceting bounds, STEP determinism and record identity.

Every value is a synthetic fixture; nothing describes a real machine. The
B-rep measures come from the pinned third-party OpenCASCADE kernel and are
checked against the analytic closed forms within the library's declared
tolerance; the tier-G1 reference mesh and the polygon-deficit bound come
from the shared kernel library.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path

import pytest

pytest.importorskip("cadquery")

from scpn_reactor_kernels.cad import MANIFEST_SCHEMA, MEASURE_TOLERANCE

from geometry_fixtures import reference_configuration, reference_geometry
from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry import (
    BODY_NAMES,
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModelCAD,
    build_device_cad,
    build_device_model,
    write_step,
)
from scpn_z_pinch_core.parameters import PinchColumn

#: Digest of the reference CAD model record in the pinned back-end
#: environment (cadquery 2.8.0, OCP 7.9.3.1); a back-end bump re-pins it
#: as a governed data change (ADR 0008).
REFERENCE_CAD_MODEL_SHA256 = (
    "73688d3e214a72cee7a5fbcd2d4fd9a561dd94a9b642f11a5ce9b568dfbd5b9a"
)

# Analytic body volumes in the shared library's exact operation order
# (``pi r r h`` for the cylinder, ``pi (r_o r_o - r_i r_i) h`` for the
# tube), so the equality check is exact rather than approximate.
ANALYTIC_VOLUMES = (
    math.pi * 0.05 * 0.05 * (1.0 - 0.0),
    math.pi * (0.11 * 0.11 - 0.1 * 0.1) * (1.6 - 0.0),
    math.pi * (0.16 * 0.16 - 0.15 * 0.15) * (1.6 - 0.0),
    math.pi * 0.16 * 0.16 * (0.0 - (0.0 - 0.02)),
    math.pi * 0.16 * 0.16 * (1.6 + 0.02 - 1.6),
    math.pi * 0.01 * 0.01 * (1.0 + 0.5 - 1.0),
)


def reference_cad_model() -> DeviceModelCAD:
    """Build the synthetic CAD model of the tests."""
    return build_device_cad(reference_configuration(), reference_geometry())


def test_bodies_match_the_g1_inventory_roles_and_materials() -> None:
    """The CAD bodies are the G1 bodies: same names, roles, materials."""
    model = reference_cad_model()
    reference = build_device_model(
        reference_configuration(), reference_geometry(), DEFAULT_REFERENCE_MESH_SEGMENTS
    )
    assert tuple(body.name for body in model.bodies) == BODY_NAMES
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.role == mesh.role
        assert body.material_identifier == mesh.material_identifier


def test_brep_measures_agree_with_the_analytic_closed_forms() -> None:
    """Every body volume and area matches the analytic form within 1e-9."""
    model = reference_cad_model()
    for body, analytic in zip(model.bodies, ANALYTIC_VOLUMES, strict=True):
        assert body.analytic_volume_m3 == analytic
        assert 0.0 <= body.volume_relative_error <= MEASURE_TOLERANCE
        assert 0.0 <= body.surface_area_relative_error <= MEASURE_TOLERANCE


def test_faceted_volumes_stay_within_the_deflection_deficit_bound() -> None:
    """The faceted body underestimates the analytic volume within 2 d / r."""
    model = reference_cad_model()
    for body in model.bodies:
        assert body.faceted_volume_relative_deficit >= 0.0
        assert body.faceted_volume_relative_deficit <= body.faceted_volume_deficit_bound
        assert body.faceted_volume_m3 < body.analytic_volume_m3


def test_faceted_meshes_are_closed_and_outward_oriented() -> None:
    """Every faceted mesh satisfies the G1 closed-mesh contract."""
    model = reference_cad_model()
    assert len(model.faceted_meshes) == len(BODY_NAMES)
    for mesh in model.faceted_meshes:
        assert mesh.signed_volume_m3() > 0.0
        assert mesh.face_count > 0


def test_faceted_volumes_track_the_reference_mesh_within_the_polygon_bound() -> None:
    """Faceted and G1 volumes agree within the exact polygon-deficit bound."""
    model = reference_cad_model()
    reference = build_device_model(
        reference_configuration(), reference_geometry(), DEFAULT_REFERENCE_MESH_SEGMENTS
    )
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.reference_mesh_volume_m3 == mesh.signed_volume_m3()
        assert body.mesh_volume_relative_difference >= 0.0
        assert body.mesh_volume_relative_difference <= body.mesh_volume_difference_bound


def test_step_export_is_byte_deterministic() -> None:
    """Two builds of the same design give byte-identical STEP documents."""
    first = reference_cad_model()
    second = reference_cad_model()
    assert first.step_data == second.step_data
    assert first.step_sha256 == second.step_sha256
    assert len(first.step_sha256) == 64
    assert first.digest_sha256() == second.digest_sha256()


def test_step_round_trip_reproduces_the_volumes(tmp_path: Path) -> None:
    """Re-importing the written STEP gives the bodies' volumes within 1e-9.

    The re-import runs in a subprocess, which is how a consumer reads the
    file: a separate reader process. (An in-process import is also safe
    since the library's unfolding normalisation removed the writer-state
    sensitivity — the library's ADR 0006 addendum.)
    """
    import subprocess
    import sys

    model = reference_cad_model()
    target = tmp_path / "device.step"
    written = write_step(target, model)
    assert written == len(model.step_data)
    assert target.read_bytes() == model.step_data
    assert hashlib.sha256(target.read_bytes()).hexdigest() == model.step_sha256
    script = (
        "import json, sys;"
        "import cadquery;"
        "solids = cadquery.importers.importStep(sys.argv[1]).solids().vals();"
        "print(json.dumps(sorted(float(s.Volume()) for s in solids)))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    got = json.loads(completed.stdout)
    assert len(got) == len(BODY_NAMES)
    expected = sorted(body.analytic_volume_m3 for body in model.bodies)
    for value, reference in zip(got, expected, strict=True):
        assert math.isclose(value, reference, rel_tol=MEASURE_TOLERANCE)


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_cad(configuration, geometry)
    record = model.to_record()
    assert record["schema"] == CAD_MODEL_SCHEMA
    assert record["schema_version"] == CAD_MODEL_SCHEMA_VERSION
    assert record["non_claims"] == list(CAD_MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["reference_mesh_segments"] == DEFAULT_REFERENCE_MESH_SEGMENTS
    assert record["linear_deflection_m"] == DEFAULT_LINEAR_DEFLECTION_M
    assert record["angular_deflection_rad"] == DEFAULT_ANGULAR_DEFLECTION_RAD
    assert record["backend_versions"]["cadquery"] != "unavailable"
    assert record["backend_versions"]["ocp"] != "unavailable"
    assert record["assembly_manifest"]["schema"] == MANIFEST_SCHEMA
    assert record["assembly_manifest"]["body_count"] == len(BODY_NAMES)
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_CAD_MODEL_SHA256


def test_invalid_segments_are_refused() -> None:
    """The reference mesh segment rule is enforced by the build."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_cad(reference_configuration(), reference_geometry(), 20)


def test_column_violations_are_refused() -> None:
    """The column containment invariants hold for the CAD build."""
    configuration = dataclasses.replace(
        reference_configuration(),
        column=PinchColumn(column_radius_m=0.1, column_length_m=0.5),
    )
    with pytest.raises(DeviceGeometryError, match="column_radius_m"):
        build_device_cad(configuration, reference_geometry())


def test_invalid_deflections_are_refused() -> None:
    """Non-positive deflections are refused by the build."""
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            linear_deflection_m=0.0,
        )


def test_body_evidence_refuses_out_of_bound_values() -> None:
    """The evidence record fails closed when a bound is violated."""
    model = reference_cad_model()
    body = model.bodies[0]
    with pytest.raises(DeviceGeometryError, match="volume_relative_error"):
        dataclasses.replace(body, volume_relative_error=1.0)
    with pytest.raises(DeviceGeometryError, match="surface_area_relative_error"):
        dataclasses.replace(body, surface_area_relative_error=1.0)
    with pytest.raises(DeviceGeometryError, match="faceted_volume_relative_deficit"):
        dataclasses.replace(body, faceted_volume_relative_deficit=1.0)
    with pytest.raises(DeviceGeometryError, match="mesh_volume_relative_difference"):
        dataclasses.replace(body, mesh_volume_relative_difference=1.0)


def test_model_refuses_a_foreign_body_inventory() -> None:
    """A record with the wrong body order is refused."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        dataclasses.replace(model, bodies=model.bodies[::-1])


def test_model_refuses_invalid_declared_parameters() -> None:
    """The record refuses invalid segments, deflections and digests."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="multiple"):
        dataclasses.replace(model, reference_mesh_segments=20)
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        dataclasses.replace(model, linear_deflection_m=math.nan)
    with pytest.raises(DeviceGeometryError, match="angular_deflection_rad"):
        dataclasses.replace(model, angular_deflection_rad=-1.0)
    with pytest.raises(DeviceGeometryError, match="step_sha256"):
        dataclasses.replace(model, step_sha256="not-a-digest")
    with pytest.raises(DeviceGeometryError, match="assembly_manifest"):
        dataclasses.replace(model, assembly_manifest={"schema": "foreign"})
    manifest = dict(model.assembly_manifest)
    manifest["body_count"] = 1
    with pytest.raises(DeviceGeometryError, match="body_count"):
        dataclasses.replace(model, assembly_manifest=manifest)


def test_evidence_projection_is_json_serialisable() -> None:
    """The per-body evidence projects to JSON with every declared bound."""
    model = reference_cad_model()
    record = model.bodies[0].to_record()
    assert record["name"] == BODY_NAMES[0]
    assert record["volume_relative_error"] <= MEASURE_TOLERANCE
    assert (
        record["faceted_volume_relative_deficit"]
        <= record["faceted_volume_deficit_bound"]
    )
    json.dumps(record, allow_nan=False)
