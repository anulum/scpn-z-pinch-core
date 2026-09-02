<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — Device 3D model contract
-->

# Device 3D model contract

Producer-owned contract of the `device_3d_model` capability
(`computational_prototype`; design record ADR 0006). It states exactly
what the exported files contain so that a consumer — the portfolio
presentation layer, an engineering tool, a reviewer — can read them
without importing this package. Nothing in the files or in this contract
creates a federation, a claim, or an engineering statement.

## Records

| Record | Schema | Identity |
|---|---|---|
| Device configuration | package `DeviceConfiguration` record | `configuration_digest_sha256` |
| Device geometry | package `DeviceGeometry` record (eight SI fields) | `geometry_digest_sha256` |
| Device model | `scpn.z-pinch-3d-model.v1` version `1.0.0` | `model_sha256` = SHA-256 of the canonical model record |
| Body mesh | little-endian `uint32 vertex_count, uint32 face_count, float64 x y z per vertex, uint32 i j k per face` | `mesh_sha256` |

The model record carries: `schema`, `schema_version`, `units`, `non_claims`,
`configuration_digest_sha256`, `geometry_digest_sha256`, `segments`, and
`bodies` (one summary per body: `name`, `role`, `material_identifier`,
`vertex_count`, `face_count`, `volume_m3`, `surface_area_m2`,
`bounding_box_min_m`, `bounding_box_max_m`, `mesh_sha256`). Canonical bytes
are UTF-8 JSON with sorted keys, minimal separators and a trailing newline;
NaN and infinity are never emitted.

## Units and axes

- Length unit: metre, in every record and in both export formats.
- Right-handed Cartesian frame; `z` is the device axis, increasing
  downstream; the origin is the upstream electrode face on the axis.
- Float64 in the records and the canonical mesh bytes; float32 in STL and
  GLB because both containers require it (the canonical digests are taken
  on the float64 bytes, never on the exports).

## Bodies (fixed order, fixed names)

| Node name | Role | Material token | Analytic body |
|---|---|---|---|
| `inner_electrode` | `electrode` | `electrode_conductor` | solid cylinder, `z in [0, L_acc]` |
| `outer_electrode` | `electrode` | `electrode_conductor` | annular tube, `z in [0, L_acc + L_asm]` |
| `chamber_wall` | `vacuum_boundary` | `chamber_wall` | annular tube, `z in [0, L_acc + L_asm]` |
| `end_wall_upstream` | `vacuum_boundary` | `chamber_wall` | solid cylinder, `z in [-t_end, 0]` |
| `end_wall_downstream` | `vacuum_boundary` | `chamber_wall` | solid cylinder, `z in [L_acc + L_asm, L_acc + L_asm + t_end]` |
| `plasma_column` | `plasma` | `plasma` | solid cylinder of the configuration's column, `z in [L_acc, L_acc + column_length]` |

Material tokens are declarations only; no density, composition,
conductivity or nuclear property is carried anywhere.

Every body is a closed triangle surface with outward orientation
(counter-clockwise vertex order seen from outside), no degenerate face,
every directed edge appearing exactly once together with its reverse.
Segment counts are multiples of eight (at least eight).

## Files

- **Binary STL** (`stl_bytes`, `write_stl`): 80-byte header starting with
  `SCPN Z-Pinch Core device_3d_model`, `uint32` triangle count, then per
  triangle a float32 unit normal, three float32 vertices and a zero
  `uint16` attribute. All bodies are concatenated in the fixed order; STL
  carries no names, so the GLB is the file for body identity.
- **glTF 2.0 binary** (`glb_bytes`, `write_glb`): header (magic `glTF`,
  version 2, total length), one JSON chunk (space-padded to four bytes),
  one binary chunk (zero-padded). One `mesh` and one `node` per body, the
  node named as in the table above, with `node.extras` = `{role,
  material_identifier, mesh_sha256}`. Each primitive has a float32 `VEC3`
  `POSITION` accessor with `min`/`max` and a `uint32` `SCALAR` index
  accessor, mode `TRIANGLES`; buffer views are four-byte aligned. The
  document `extras` carry `schema`, `schema_version`,
  `configuration_digest_sha256`, `geometry_digest_sha256`, `model_sha256`,
  `segments`, `units` and `non_claims`. No materials, textures, animations
  or extensions are used.

## Determinism

The same configuration, geometry and segment count always yield the same
records, the same mesh bytes and the same export bytes, on every backend:
the vertex coordinates are computed by the polynomial unit circle of the
shared kernel library `scpn-reactor-kernels` (pinned by commit object and
kernel-inventory digest in `reactor-domain.json`, `kernel_library`) with
fixed operation order, proven bit-exact between that library's Python
floor and its native kernels, and the device model is proven bit-exact
against the library's native module body by body. The serialisers are the
library's kernel `geometry_exports`: the binary STL header and the glTF
`asset.generator` name that kernel, while the document `extras` carry this
repository's provenance (schema, digests, units, non-claims). A change of
the library pin is a governed data change of this repository.

## Non-claims

- The bodies are analytic surfaces of a synthetic design: no CAD solid,
  no equilibrium boundary, no engineering model.
- No material property, load, field or neutronic quantity is carried.
- No value describes or validates any real machine.
- Providing these files does not federate the repository, present it, or
  gate its execution anywhere; those remain the portfolio layer's domain.
