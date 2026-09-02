<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z Pinch Core — ADR 0006
-->

# ADR 0006 — Device 3D model: validated geometry, deterministic tessellation, open exports

Status: accepted (2026-09-02). Adds the fourth implemented capability,
`device_3d_model`, at `computational_prototype`.

## Context

The device repository owns device geometry (ADR 0001 boundary: plant and
experiment truth, configuration policy). Until this record the geometry
was a plasma column alone; there was no mechanical envelope and no way to
present, measure or hand a design to downstream tooling. A three-
dimensional model of the device is the substrate for every later
engineering lane (surface loading, neutronics geometry, magnet and
pulsed-power layouts) and for portfolio presentation. It must be
regenerated exactly from the validated records, must not depend on a
heavy CAD kernel to run in every gate, and must never overstate what an
analytic surface is.

## Decision

1. A new owned domain `device_geometry_and_3d_model` is declared in
   `reactor-domain.json`: device-owned geometry parameters and the 3D
   model derived from them. It is disjoint from solver mathematics (no
   equation is solved), from portfolio presentation (the exported files
   are an offer, `docs/DEVICE_3D_MODEL_CONTRACT.md`; STUDIO decides the
   viewer and the federation) and from any engineering lane (no property
   is carried).
2. `DeviceGeometry` (`src/scpn_z_pinch_core/geometry/device.py`) carries
   the coaxial mechanical envelope — inner electrode, outer electrode
   bore and wall, acceleration and assembly region lengths, chamber bore
   and wall, end walls — with fail-closed positivity and containment
   invariants, canonical bytes and a SHA-256 digest, and a strict record
   parser. The layout follows the qualitative coaxial-gun/assembly-region
   arrangement of the sheared-flow z-pinch literature (Shumlak et al.,
   Phys. Plasmas 24 (2017) 055702); no dimension of any device is used.
3. The model is tier G1: analytic bodies (solid cylinders and annular
   tubes) tessellated into closed, outward-oriented triangle meshes with
   fixed vertex and face order. Six bodies in a fixed order: inner
   electrode, outer electrode, chamber wall, upstream and downstream end
   walls, and the plasma column (the configuration's column radius and
   length placed in the assembly region — an analytic surface, not an
   equilibrium boundary). B-rep CAD (tier G2) is a separate, later
   decision.
4. Vertices come from a vendored deterministic unit circle: degree-15
   sine and degree-16 cosine Taylor polynomials in Horner form on
   `[0, pi/4]` with exact octant and quadrant symmetry, evaluated with the
   same operation order in Python and Rust, so no `libm` call enters the
   geometry and every vertex agrees bit for bit across backends. Segment
   counts are multiples of eight. The polynomials are within one unit in
   the last place of `math.sin`/`math.cos` on the reduced interval and
   the whole circle is tested against `libm` to `1e-15`.
5. `TriangleMesh` validates closure and consistent orientation (every
   directed edge exactly once with its reverse), computes the signed
   volume (divergence theorem) and surface area with a fixed summation
   order, and serialises canonically (little-endian counts, float64
   vertices, uint32 faces) with a SHA-256 digest. `DeviceModel3D`
   (`scpn.z-pinch-3d-model.v1` `1.0.0`) records the source digests, the
   segment count, the units and axis convention, every body summary and
   fixed non-claims; its canonical digest identifies the exact model, and
   one reference digest is pinned in the tests as an immutability fixture.
6. Exports are pure serialisations of the validated meshes: binary STL
   (all bodies) and glTF 2.0 binary (GLB) per the Khronos specification,
   one named node per body, float32 storage as the container requires,
   and document `extras` carrying the schema, digests, units and
   non-claims.
7. The native crate mirrors the unit circle, both primitives, the volume
   and the area (`rust/src/geometry/`); parity tests compare float64 bit
   patterns of every vertex coordinate, the face index streams and the
   measures. The Python floor remains the public API and the default.
8. A standard-conformant benchmark (`benchmarks/device_model_3d.py`)
   times one full device tessellation with measures per generated face on
   both backends; the local artefact is committed and labelled
   non-isolated.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. VALIDATION states what is exercised (closure, orientation,
exact polygon-prism identities, quadratic convergence of the volume to the
analytic bodies, export layouts read back at specification level, native
parity) and what is not claimed (no CAD solid, no equilibrium boundary, no
material, load, field or neutronic quantity, no real machine). The
manifest change alters `manifest_sha256` inside the plan envelope, so the
envelope fixture is regenerated from the public surface and re-pinned; the
plan bytes and `plan_sha256` are unchanged. The exported GLB and its node
contract are offered to the portfolio layer; federation state remains
`not_federated` until its gates run.
