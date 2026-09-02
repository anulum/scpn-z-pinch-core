<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z Pinch Core — ADR 0007
-->

# ADR 0007 — Consume the shared geometry kernels instead of carrying copies

Status: accepted (2026-09-02). Amends ADR 0006 items 4, 5 and 7: the
unit circle, the tessellation primitives, the closed-mesh contract and the
serialisers are no longer implemented here.

## Context

ADR 0006 landed the device 3D model with its own copies of the
family-independent geometry substrate (`trig`, `mesh`, `primitives`,
`export` and their native mirrors). The same substrate was then moved
verbatim into the shared kernel library of the research group,
`scpn-reactor-kernels` (its ADR 0002, kernels `geometry_unit_circle`,
`geometry_mesh_contract`, `geometry_primitives`, `geometry_exports`), so
that every device family tessellates on one proven implementation. Two
copies of the same numerics would drift; a device repository that keeps
its own copy would also re-prove parity that the library already proves.

## Decision

1. The repository declares `scpn-reactor-kernels` as its one runtime
   dependency, pinned to a commit object of the library's public
   repository (`pyproject.toml`, `dependencies`); no release of the
   library exists yet, so the commit is the exact identity.
2. The manifest carries the pin as an optional `kernel_library` block:
   distribution, version, `source_commit`, `inventory_sha256` (the SHA-256
   of the library's generated `kernel-inventory.json` at that commit) and
   the sorted identifiers of the kernels consumed. The validator enforces
   every field exactly; a contract test proves that the manifest, the
   `pyproject.toml` dependency, the installed package version and the CI
   install steps agree on one commit. The inventory digest identifies the
   inventory at the pinned commit; the library's own consumer table is
   updated in a later library commit and therefore never appears in the
   inventory a consumer pins.
3. The geometry copies are deleted: `src/scpn_z_pinch_core/geometry/`
   keeps `device.py` (device truth), `model.py` (composition of the six
   bodies on the library's primitives; the mesh type of every body is the
   library's `TriangleMesh`) and `export.py` (device-side provenance
   `glb_extras` handed to the library's serialisers). The library's
   segment refusal is re-raised as `DeviceGeometryError` with its message,
   so the consumer's error contract is unchanged. Library symbols are not
   re-exported from this package; consumers import them from the library.
4. The native crate `scpn-z-pinch-rs` carries physics only. Parity of the
   device model is proven against the library's native module
   (`scpn_reactor_kernels_native`): every vertex coordinate, face index,
   volume and area of the six bodies agrees bit for bit with the library's
   native tessellation and measures, so the consumer inherits the
   library's bit-exactness instead of re-proving the kernels.
5. The 3D-model benchmark measures the library's Python floor (through the
   validated device build) against the library's native kernels.
6. The exported bytes change in two literal fields only: the binary STL
   header and the glTF `asset.generator` now name the library kernel; the
   model record, its digest and the mesh digests are unchanged
   (`docs/DEVICE_3D_MODEL_CONTRACT.md`).
7. The manifest adds the excluded domain
   `shared_physics_geometry_and_numerics_kernels` owned by
   `SCPN-REACTOR-KERNELS`, mirroring the library's exclusion of device
   truth.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. `VALIDATION.md#device-3d-model` now lists what this
repository exercises (device geometry, model composition, provenance,
export read-back, parity against the library's native module) and points
at the library's evidence for the kernels themselves. A change of the
library pin is a governed data change of this repository (manifest,
descriptor and inventory regeneration, envelope fixture re-pin, SPO
re-intake). The manifest change alters `manifest_sha256` inside the plan
envelope, so the envelope fixture is regenerated from the public surface
and re-pinned; the plan bytes and `plan_sha256` are unchanged.
