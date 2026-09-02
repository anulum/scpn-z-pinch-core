# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device geometry and 3D model package

"""Device geometry and tier-G1 3D model of the z-pinch family.

A validated device geometry, deterministic tessellation of analytic
bodies built on a vendored bit-exact unit circle, a closed-mesh contract
with canonical bytes and digests, a composed device model record, and
open-format exports (binary STL, glTF 2.0 binary). Every body is an
analytic surface of a synthetic design; nothing here is a CAD solid, an
equilibrium boundary or an engineering model, and no value describes a
real machine. Design record: ADR 0006.
"""

from __future__ import annotations

from scpn_z_pinch_core.geometry.device import (
    GEOMETRY_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)
from scpn_z_pinch_core.geometry.export import (
    GLTF_GENERATOR,
    STL_HEADER,
    glb_bytes,
    stl_bytes,
    write_glb,
    write_stl,
)
from scpn_z_pinch_core.geometry.mesh import (
    MESH_BYTES_LAYOUT,
    Face,
    TriangleMesh,
    Vertex,
    face_normal_and_area,
)
from scpn_z_pinch_core.geometry.model import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    build_device_model,
)
from scpn_z_pinch_core.geometry.primitives import annular_tube, cylinder_solid
from scpn_z_pinch_core.geometry.trig import (
    MIN_SEGMENTS,
    SEGMENT_MULTIPLE,
    cosine_polynomial,
    require_segments,
    sine_polynomial,
    unit_circle,
)

__all__ = [
    "BODY_NAMES",
    "GEOMETRY_FIELDS",
    "GLTF_GENERATOR",
    "MESH_BYTES_LAYOUT",
    "MIN_SEGMENTS",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "SEGMENT_MULTIPLE",
    "STL_HEADER",
    "DeviceGeometry",
    "DeviceModel3D",
    "Face",
    "TriangleMesh",
    "Vertex",
    "annular_tube",
    "build_device_model",
    "cosine_polynomial",
    "cylinder_solid",
    "face_normal_and_area",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "require_segments",
    "sine_polynomial",
    "stl_bytes",
    "unit_circle",
    "write_glb",
    "write_stl",
]
