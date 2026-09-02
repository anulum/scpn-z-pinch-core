# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device geometry model tests

"""Every invariant, derived quantity and codec branch of DeviceGeometry."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math

import pytest

from geometry_fixtures import reference_geometry
from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry import (
    GEOMETRY_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)


def test_derived_quantities() -> None:
    """Outer radii and the device length follow from the declared values."""
    geometry = reference_geometry()
    assert geometry.outer_electrode_outer_radius_m == 0.1 + 0.01
    assert geometry.chamber_outer_radius_m == 0.15 + 0.01
    assert geometry.device_length_m == 1.0 + 0.6


@pytest.mark.parametrize("field", GEOMETRY_FIELDS)
@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_every_field_must_be_finite_and_positive(field: str, value: float) -> None:
    """Non-finite and non-positive values fail closed on every field."""
    with pytest.raises(DeviceGeometryError, match=field):
        dataclasses.replace(reference_geometry(), **{field: value})


def test_inner_electrode_must_fit_the_bore() -> None:
    """The inner electrode radius must be smaller than the outer bore."""
    with pytest.raises(DeviceGeometryError, match="inner_electrode_radius_m"):
        dataclasses.replace(reference_geometry(), inner_electrode_radius_m=0.1)


def test_outer_electrode_must_fit_the_chamber() -> None:
    """The outer electrode outer radius must not exceed the chamber bore."""
    with pytest.raises(DeviceGeometryError, match="chamber_inner_radius_m"):
        dataclasses.replace(reference_geometry(), chamber_inner_radius_m=0.1)
    flush = dataclasses.replace(reference_geometry(), chamber_inner_radius_m=0.11)
    assert flush.chamber_inner_radius_m == flush.outer_electrode_outer_radius_m


def test_record_round_trip_and_digest() -> None:
    """The canonical bytes are sorted JSON and the digest identifies them."""
    geometry = reference_geometry()
    record = geometry.to_record()
    assert tuple(record) == GEOMETRY_FIELDS
    data = geometry.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert list(json.loads(data)) == sorted(record)
    assert geometry.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert geometry_from_record(record) == geometry
    assert geometry_from_bytes(data) == geometry


def test_record_must_be_an_object() -> None:
    """Non-object records are refused."""
    with pytest.raises(DeviceGeometryError, match="record: must be an object"):
        geometry_from_record([1, 2, 3])


def test_unknown_fields_are_refused() -> None:
    """The parser refuses fields outside the declared set."""
    record = reference_geometry().to_record()
    record["port_count"] = 4
    with pytest.raises(DeviceGeometryError, match=r"unknown fields \['port_count'\]"):
        geometry_from_record(record)


@pytest.mark.parametrize("value", [None, "0.1", True])
def test_non_numeric_fields_are_refused(value: object) -> None:
    """Missing, string and boolean values are not numbers."""
    record = reference_geometry().to_record()
    record["end_wall_thickness_m"] = value  # type: ignore[assignment]
    with pytest.raises(DeviceGeometryError, match="end_wall_thickness_m: must be"):
        geometry_from_record(record)


def test_invalid_json_and_non_finite_literals_are_refused() -> None:
    """Malformed documents and NaN literals fail closed."""
    with pytest.raises(DeviceGeometryError, match="invalid JSON"):
        geometry_from_bytes(b"{")
    with pytest.raises(DeviceGeometryError, match="invalid JSON"):
        geometry_from_bytes(b"\xff\xfe")
    record = reference_geometry().to_record()
    text = json.dumps(record).replace("0.02", "NaN")
    with pytest.raises(DeviceGeometryError, match="non-finite JSON literal"):
        geometry_from_bytes(text.encode("utf-8"))


def test_geometry_is_frozen() -> None:
    """The dataclass is immutable."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        reference_geometry().end_wall_thickness_m = 1.0  # type: ignore[misc]
    assert isinstance(reference_geometry(), DeviceGeometry)
