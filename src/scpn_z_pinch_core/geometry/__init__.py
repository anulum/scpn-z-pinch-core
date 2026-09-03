# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device geometry and 3D model

"""Device geometry, tier-G1 3D model and tier-G2 CAD model of the family.

A validated device geometry, the composed device model record of six
analytic bodies, the composed device CAD model record of the same six
bodies as B-rep solids on the pinned third-party OpenCASCADE kernel, and
the device-side provenance of the open-format exports (binary STL, glTF
2.0 binary, STEP). The unit circle, the tessellation primitives, the
closed-mesh contract, the serialisers and the B-rep, STEP and faceting
kernels are consumed from the pinned shared kernel library
``scpn_reactor_kernels`` (ADR 0007, ADR 0008); the mesh type of every
body is that library's ``TriangleMesh``. Every body is a synthetic
design surface or solid; nothing here is an equilibrium boundary or an
engineering model, and no value describes a real machine. Design
records: ADR 0006, ADR 0007, ADR 0008.
"""

from __future__ import annotations

from scpn_z_pinch_core.geometry.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    BodyCADEvidence,
    DeviceModelCAD,
    build_device_cad,
)
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
    glb_extras,
    stl_bytes,
    write_glb,
    write_step,
    write_stl,
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

__all__ = [
    "BODY_NAMES",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "GEOMETRY_FIELDS",
    "GLTF_GENERATOR",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "STL_HEADER",
    "BodyCADEvidence",
    "DeviceGeometry",
    "DeviceModel3D",
    "DeviceModelCAD",
    "build_device_cad",
    "build_device_model",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "stl_bytes",
    "write_glb",
    "write_step",
    "write_stl",
]
