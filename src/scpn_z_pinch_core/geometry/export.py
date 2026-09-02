# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — open-format mesh exports

"""Binary STL and glTF 2.0 (GLB) exports of the device model.

The serialisers are the shared geometry kernels of the pinned kernel
library (``scpn_reactor_kernels.geometry.export``, kernel
``geometry_exports``); this module owns only the device-side provenance:
the document ``extras`` of the GLB carry the model schema, the source
digests, the model digest, the segment count, the units and the
non-claims so a viewer can show where the meshes came from. Coordinates
are stored in metres; float32 storage is a format constraint of both
containers and is stated in the contract document.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scpn_reactor_kernels.geometry import (
    GLTF_GENERATOR,
    STL_HEADER,
    TriangleMesh,
)
from scpn_reactor_kernels.geometry import glb_bytes as _library_glb_bytes
from scpn_reactor_kernels.geometry import stl_bytes as _library_stl_bytes

from scpn_z_pinch_core.geometry.model import DeviceModel3D

__all__ = [
    "GLTF_GENERATOR",
    "STL_HEADER",
    "glb_bytes",
    "glb_extras",
    "stl_bytes",
    "write_glb",
    "write_stl",
]


def glb_extras(model: DeviceModel3D) -> dict[str, Any]:
    """Return the document-level provenance record of the GLB export.

    Parameters
    ----------
    model
        Validated device model.

    Returns
    -------
    dict[str, Any]
        Schema identity, both source digests, the model digest, the segment
        count, the units and the non-claims of the model record.
    """
    record = model.to_record()
    return {
        "schema": record["schema"],
        "schema_version": record["schema_version"],
        "configuration_digest_sha256": record["configuration_digest_sha256"],
        "geometry_digest_sha256": record["geometry_digest_sha256"],
        "model_sha256": model.digest_sha256(),
        "segments": record["segments"],
        "units": record["units"],
        "non_claims": record["non_claims"],
    }


def stl_bytes(meshes: tuple[TriangleMesh, ...]) -> bytes:
    """Serialise meshes as one binary STL document.

    Parameters
    ----------
    meshes
        Validated meshes; all bodies are concatenated in order.

    Returns
    -------
    bytes
        The binary STL document written by the library kernel.
    """
    return _library_stl_bytes(meshes)


def glb_bytes(model: DeviceModel3D) -> bytes:
    """Serialise the model as one glTF 2.0 binary document.

    Parameters
    ----------
    model
        Validated device model.

    Returns
    -------
    bytes
        The GLB document written by the library kernel with the device
        provenance of :func:`glb_extras` as its document ``extras``.
    """
    return _library_glb_bytes(model.meshes, glb_extras(model))


def write_stl(path: Path, meshes: tuple[TriangleMesh, ...]) -> int:
    """Write a binary STL document.

    Parameters
    ----------
    path
        Destination file.
    meshes
        Validated meshes.

    Returns
    -------
    int
        Number of bytes written.
    """
    return path.write_bytes(stl_bytes(meshes))


def write_glb(path: Path, model: DeviceModel3D) -> int:
    """Write a glTF 2.0 binary document.

    Parameters
    ----------
    path
        Destination file.
    model
        Validated device model.

    Returns
    -------
    int
        Number of bytes written.
    """
    return path.write_bytes(glb_bytes(model))
