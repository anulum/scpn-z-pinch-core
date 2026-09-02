# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device 3D model tests

"""Body inventory, invariants, record identity and the immutable pin."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math

import pytest

from geometry_fixtures import reference_configuration, reference_geometry
from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    build_device_model,
)
from scpn_z_pinch_core.parameters import PinchColumn

REFERENCE_MODEL_SHA256 = (
    "fe7beef57e78ea185a931539599d566347a082bcf0550e468708c77d6988b25e"
)


def test_bodies_roles_materials_and_extents() -> None:
    """Six bodies in the fixed order with the declared roles and placement."""
    geometry = reference_geometry()
    model = build_device_model(reference_configuration(), geometry, 16)
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES
    roles = [mesh.role for mesh in model.meshes]
    assert roles == [
        "electrode",
        "electrode",
        "vacuum_boundary",
        "vacuum_boundary",
        "vacuum_boundary",
        "plasma",
    ]
    inner, outer, chamber, upstream, downstream, plasma = model.meshes
    assert inner.bounding_box() == ((-0.05, -0.05, 0.0), (0.05, 0.05, 1.0))
    assert outer.bounding_box()[1][2] == geometry.device_length_m
    assert chamber.bounding_box()[1][0] == geometry.chamber_outer_radius_m
    assert upstream.bounding_box()[0][2] == -geometry.end_wall_thickness_m
    assert downstream.bounding_box()[1][2] == geometry.device_length_m + 0.02
    assert plasma.bounding_box() == ((-0.01, -0.01, 1.0), (0.01, 0.01, 1.5))
    for mesh in model.meshes:
        assert mesh.signed_volume_m3() > 0.0


def test_volumes_follow_the_analytic_bodies() -> None:
    """Each body volume converges on the analytic cylinder or tube volume."""
    geometry = reference_geometry()
    model = build_device_model(reference_configuration(), geometry, 1024)
    analytic = [
        math.pi * 0.05**2 * 1.0,
        math.pi * (0.11**2 - 0.1**2) * 1.6,
        math.pi * (0.16**2 - 0.15**2) * 1.6,
        math.pi * 0.16**2 * 0.02,
        math.pi * 0.16**2 * 0.02,
        math.pi * 0.01**2 * 0.5,
    ]
    for mesh, exact in zip(model.meshes, analytic, strict=True):
        assert 0.0 < (exact - mesh.signed_volume_m3()) / exact < 1.0e-5


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_model(configuration, geometry, 8)
    record = model.to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["units"] == MODEL_UNITS
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["segments"] == 8
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    data = model.canonical_bytes()
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_MODEL_SHA256


def test_model_is_deterministic() -> None:
    """Two builds of the same inputs are equal and share every digest."""
    first = build_device_model(reference_configuration(), reference_geometry(), 32)
    second = build_device_model(reference_configuration(), reference_geometry(), 32)
    assert first == second
    assert first.digest_sha256() == second.digest_sha256()
    assert [m.digest_sha256() for m in first.meshes] == [
        m.digest_sha256() for m in second.meshes
    ]


def test_column_must_fit_the_bore() -> None:
    """A column as wide as the outer electrode bore is refused."""
    configuration = dataclasses.replace(
        reference_configuration(),
        column=PinchColumn(column_radius_m=0.1, column_length_m=0.5),
    )
    with pytest.raises(DeviceGeometryError, match="column_radius_m"):
        build_device_model(configuration, reference_geometry(), 8)


def test_column_must_fit_the_assembly_region() -> None:
    """A column longer than the assembly region is refused."""
    configuration = dataclasses.replace(
        reference_configuration(),
        column=PinchColumn(column_radius_m=0.01, column_length_m=0.7),
    )
    with pytest.raises(DeviceGeometryError, match="column_length_m"):
        build_device_model(configuration, reference_geometry(), 8)


def test_invalid_segments_are_refused_before_tessellation() -> None:
    """The segment rule is checked first."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_model(reference_configuration(), reference_geometry(), 20)


def test_body_inventory_is_enforced() -> None:
    """A model with the wrong bodies or order is refused."""
    model = build_device_model(reference_configuration(), reference_geometry(), 8)
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        DeviceModel3D(
            configuration_digest_sha256=model.configuration_digest_sha256,
            geometry_digest_sha256=model.geometry_digest_sha256,
            segments=8,
            meshes=model.meshes[::-1],
        )
