# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — analytic surface tessellation

"""Deterministic tessellation of the analytic bodies of the device model.

Two primitives cover every body of the tier-G1 device model: the solid
cylinder (electrodes, end walls, the plasma column) and the annular tube
(the outer electrode and the chamber wall). Both are built on the
device axis ``z`` from the same deterministic unit circle, with fixed
vertex and face order and outward orientation, so the native kernel
reproduces every vertex bit for bit. Every function returns raw vertex
and face streams; :class:`~scpn_z_pinch_core.geometry.mesh.TriangleMesh`
validates them.
"""

from __future__ import annotations

from scpn_z_pinch_core.errors import DeviceGeometryError
from scpn_z_pinch_core.geometry.mesh import Face, Vertex
from scpn_z_pinch_core.geometry.trig import unit_circle
from scpn_z_pinch_core.parameters import require_finite, require_positive


def _require_extent(z_low: float, z_high: float) -> None:
    """Validate an axial extent.

    Raises
    ------
    DeviceGeometryError
        If either bound is non-finite or the extent is not positive.
    """
    for name, value in (("z_low", z_low), ("z_high", z_high)):
        try:
            require_finite(name, value)
        except ValueError as exc:
            raise DeviceGeometryError(str(exc)) from exc
    if z_high <= z_low:
        raise DeviceGeometryError(
            f"z_high: must exceed z_low, got z_low={z_low!r} z_high={z_high!r}"
        )


def _require_radius(name: str, value: float) -> float:
    """Validate a radius through the shared positivity rule."""
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


def _ring(
    radius: float, z: float, circle: tuple[tuple[float, float], ...]
) -> list[Vertex]:
    """Scale the unit circle to one ring of vertices at height ``z``."""
    return [(radius * cosine, radius * sine, z) for cosine, sine in circle]


def cylinder_solid(
    radius_m: float, z_low_m: float, z_high_m: float, segments: int
) -> tuple[tuple[Vertex, ...], tuple[Face, ...]]:
    """Tessellate a closed solid cylinder on the device axis.

    Parameters
    ----------
    radius_m
        Cylinder radius; strictly positive.
    z_low_m, z_high_m
        Axial extent; ``z_high_m > z_low_m``.
    segments
        Circumferential segments; at least 8 and a multiple of 8.

    Returns
    -------
    (vertices, faces)
        ``2 * segments + 2`` vertices (bottom ring, top ring, bottom
        centre, top centre) and ``4 * segments`` outward-oriented faces
        (side quads split into two triangles, then the two cap fans).

    Raises
    ------
    DeviceGeometryError
        If any parameter is invalid.
    """
    _require_radius("radius_m", radius_m)
    _require_extent(z_low_m, z_high_m)
    circle = unit_circle(segments)
    count = len(circle)
    vertices = _ring(radius_m, z_low_m, circle) + _ring(radius_m, z_high_m, circle)
    vertices.append((0.0, 0.0, z_low_m))
    vertices.append((0.0, 0.0, z_high_m))
    bottom_centre = 2 * count
    top_centre = 2 * count + 1
    faces: list[Face] = []
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, count + following))
        faces.append((index, count + following, count + index))
    for index in range(count):
        following = (index + 1) % count
        faces.append((bottom_centre, following, index))
    for index in range(count):
        following = (index + 1) % count
        faces.append((top_centre, count + index, count + following))
    return tuple(vertices), tuple(faces)


def annular_tube(
    inner_radius_m: float,
    outer_radius_m: float,
    z_low_m: float,
    z_high_m: float,
    segments: int,
) -> tuple[tuple[Vertex, ...], tuple[Face, ...]]:
    """Tessellate a closed annular tube (hollow cylinder) on the device axis.

    Parameters
    ----------
    inner_radius_m, outer_radius_m
        Bore and outer radii; both strictly positive with
        ``outer_radius_m > inner_radius_m``.
    z_low_m, z_high_m
        Axial extent; ``z_high_m > z_low_m``.
    segments
        Circumferential segments; at least 8 and a multiple of 8.

    Returns
    -------
    (vertices, faces)
        ``4 * segments`` vertices (outer bottom, outer top, inner bottom,
        inner top rings) and ``8 * segments`` outward-oriented faces
        (outer side, inner side facing the bore, bottom and top annuli).

    Raises
    ------
    DeviceGeometryError
        If any parameter is invalid.
    """
    _require_radius("inner_radius_m", inner_radius_m)
    _require_radius("outer_radius_m", outer_radius_m)
    if outer_radius_m <= inner_radius_m:
        raise DeviceGeometryError(
            "outer_radius_m: must exceed inner_radius_m, got "
            f"inner={inner_radius_m!r} outer={outer_radius_m!r}"
        )
    _require_extent(z_low_m, z_high_m)
    circle = unit_circle(segments)
    count = len(circle)
    vertices = (
        _ring(outer_radius_m, z_low_m, circle)
        + _ring(outer_radius_m, z_high_m, circle)
        + _ring(inner_radius_m, z_low_m, circle)
        + _ring(inner_radius_m, z_high_m, circle)
    )
    outer_top = count
    inner_bottom = 2 * count
    inner_top = 3 * count
    faces: list[Face] = []
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, outer_top + following))
        faces.append((index, outer_top + following, outer_top + index))
    for index in range(count):
        following = (index + 1) % count
        faces.append(
            (inner_bottom + index, inner_top + following, inner_bottom + following)
        )
        faces.append((inner_bottom + index, inner_top + index, inner_top + following))
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, inner_bottom + index, inner_bottom + following))
        faces.append((index, inner_bottom + following, following))
    for index in range(count):
        following = (index + 1) % count
        faces.append((outer_top + index, outer_top + following, inner_top + following))
        faces.append((outer_top + index, inner_top + following, inner_top + index))
    return tuple(vertices), tuple(faces)
