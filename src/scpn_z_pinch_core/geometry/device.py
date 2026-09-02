# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device geometry model

"""Validated device geometry of a coaxial z-pinch assembly.

The geometry complements the
:class:`~scpn_z_pinch_core.configuration.DeviceConfiguration` (which carries
the plasma column and the discharge) with the device-owned mechanical
envelope: the coaxial electrode pair, the acceleration and assembly
regions, and the vacuum chamber with its end walls. The layout is
the qualitative coaxial-gun/assembly-region arrangement of the sheared-flow
z-pinch literature (Shumlak et al., Phys. Plasmas 24 (2017) 055702); no
dimension of any device is used, and every parameter set is synthetic.
Validation is fail-closed, serialisation is canonical, and the SHA-256
digest identifies the exact geometry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.parameters import require_positive

GEOMETRY_FIELDS: Final = (
    "inner_electrode_radius_m",
    "outer_electrode_inner_radius_m",
    "outer_electrode_wall_thickness_m",
    "acceleration_region_length_m",
    "assembly_region_length_m",
    "chamber_inner_radius_m",
    "chamber_wall_thickness_m",
    "end_wall_thickness_m",
)


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule with the geometry error type."""
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceGeometry:
    """Validated coaxial device geometry (SI units in the field names).

    Parameters
    ----------
    inner_electrode_radius_m
        Radius of the solid inner electrode; strictly positive and smaller
        than the outer electrode bore.
    outer_electrode_inner_radius_m
        Bore radius of the outer electrode; strictly positive.
    outer_electrode_wall_thickness_m
        Radial wall thickness of the outer electrode; strictly positive.
    acceleration_region_length_m
        Axial length of the coaxial acceleration region (the inner
        electrode spans it); strictly positive.
    assembly_region_length_m
        Axial length of the assembly region downstream of the inner
        electrode end; strictly positive.
    chamber_inner_radius_m
        Bore radius of the vacuum chamber; at least the outer electrode
        outer radius.
    chamber_wall_thickness_m
        Radial wall thickness of the chamber; strictly positive.
    end_wall_thickness_m
        Axial thickness of the two end walls; strictly positive.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive, if the inner
        electrode does not fit inside the outer electrode bore, or if the
        outer electrode does not fit inside the chamber bore.
    """

    inner_electrode_radius_m: float
    outer_electrode_inner_radius_m: float
    outer_electrode_wall_thickness_m: float
    acceleration_region_length_m: float
    assembly_region_length_m: float
    chamber_inner_radius_m: float
    chamber_wall_thickness_m: float
    end_wall_thickness_m: float

    def __post_init__(self) -> None:
        """Validate every value and the radial containment invariants.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        for name in GEOMETRY_FIELDS:
            _positive(name, getattr(self, name))
        if self.inner_electrode_radius_m >= self.outer_electrode_inner_radius_m:
            raise DeviceGeometryError(
                "inner_electrode_radius_m: must be smaller than "
                "outer_electrode_inner_radius_m, got "
                f"{self.inner_electrode_radius_m!r} >= "
                f"{self.outer_electrode_inner_radius_m!r}"
            )
        if self.outer_electrode_outer_radius_m > self.chamber_inner_radius_m:
            raise DeviceGeometryError(
                "chamber_inner_radius_m: must be at least the outer electrode "
                f"outer radius {self.outer_electrode_outer_radius_m!r}, got "
                f"{self.chamber_inner_radius_m!r}"
            )

    @property
    def outer_electrode_outer_radius_m(self) -> float:
        """Outer radius of the outer electrode (bore plus wall)."""
        return (
            self.outer_electrode_inner_radius_m + self.outer_electrode_wall_thickness_m
        )

    @property
    def chamber_outer_radius_m(self) -> float:
        """Outer radius of the chamber (bore plus wall)."""
        return self.chamber_inner_radius_m + self.chamber_wall_thickness_m

    @property
    def device_length_m(self) -> float:
        """Axial length from the upstream electrode face to the downstream end."""
        return self.acceleration_region_length_m + self.assembly_region_length_m

    def to_record(self) -> dict[str, float]:
        """Project the geometry to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in GEOMETRY_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the geometry canonically.

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
        """Identify the exact geometry.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Raises
    ------
    DeviceGeometryError
        If the field is missing or not a real number (booleans rejected).
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceGeometryError(f"{field}: must be a number, got {value!r}")
    return float(value)


def geometry_from_record(record: Any) -> DeviceGeometry:
    """Build a validated geometry from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceGeometry.to_record`.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the record shape or any value violates the model; unknown
        fields are refused.
    """
    if not isinstance(record, dict):
        raise DeviceGeometryError("record: must be an object")
    unknown = sorted(set(record) - set(GEOMETRY_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"record: unknown fields {unknown!r}")
    return DeviceGeometry(**{name: _number(record, name) for name in GEOMETRY_FIELDS})


def geometry_from_bytes(data: bytes) -> DeviceGeometry:
    """Build a validated geometry from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceGeometryError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceGeometryError(f"record: invalid JSON document: {exc}") from exc
    return geometry_from_record(record)
