<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z Pinch Core — ADR 0008
-->

# ADR 0008 — Device CAD model: B-rep solids and a deterministic STEP export on the pinned CAD kernels

Status: accepted (2026-09-03). Adds the fifth implemented capability,
`device_cad_model`, at `computational_prototype`.

## Context

The tier-G1 model (ADR 0006, ADR 0007) produces analytic triangle meshes:
enough for viewing, volumes and simple CSG neutronics, but not an
engineering solid — no fillets, no ports, no STEP for CAD tooling, and no
B-rep a volume mesher can consume. The research group's tier-G2 lane
(plan of 2026-09-03) defines the next rung: B-rep solids of the SAME six
bodies built by the pinned third-party OpenCASCADE kernel through the
shared kernel library's `cad` group (`cad_brep_solids`, `cad_step_export`,
`cad_faceting`), a normalised deterministic STEP export, and a faceting
checked against the G1 mesh. This repository is the lane's pilot consumer.

## Decision

1. `src/scpn_z_pinch_core/geometry/cad.py` builds the six bodies with the
   library's B-rep constructors (`cylinder_solid_brep`,
   `annular_tube_brep`) at the same names, roles, material tokens and
   extents as `build_device_model`, assembles them into the library's
   `BrepAssembly`, exports the normalised STEP bytes and facets every
   body. The record `DeviceModelCAD` (`scpn.z-pinch-cad-model.v1`,
   version `1.0.0`) carries the units and axis convention of the G1
   record, both source digests, the declared deflections and the
   reference mesh segment count, the back-end versions, the assembly
   manifest, the STEP digest and the per-body evidence; canonical bytes
   and the SHA-256 digest follow the G1 pattern.
2. The evidence is fail-closed by construction: every body's B-rep volume
   and surface area must agree with the analytic closed form within the
   library's measure tolerance `1e-9`, the faceted volume's deficit
   against the analytic volume must stay within the declared bound
   `2 d / r` at the body's smallest circular radius, and the faceted
   volume must agree with the G1 reference mesh at the declared segment
   count within the exact polygon-deficit bound
   `1 - (n / 2 pi) sin(2 pi / n)`. A violated bound raises
   `DeviceGeometryError`; nothing is clamped.
3. The kernel library pin moves to the commit carrying the `cad` group
   and the `pyproject.toml` dependency gains the `cad` extra
   (`scpn-reactor-kernels[cad] @ git+…@706a5979`). The manifest's
   `kernel_library` block records the new source commit, the inventory
   digest at that commit and the consumed kernel identifiers (the three
   consumed CAD kernels plus the four geometry kernels; `cad_volume_mesh`
   is not consumed by this capability and is not listed).
4. Evidence class, per the library's ADR 0006: OpenCASCADE is a pinned
   third-party numerical kernel, not the bit-exact floor; determinism of
   the STEP bytes is claimed within one pinned back-end environment only
   (the record carries the versions), never across back-end versions. The
   pinned reference digest of the record in the tests is bound to those
   versions; a back-end bump re-pins it as a governed data change.
5. `geometry/export.py` gains `write_step`, which writes exactly the
   digested bytes the record carries, so the exported file and the record
   cannot diverge. The consumer contract document gains the STEP section
   (header normalisation, digest, versions, non-claims).
6. The manifest gains the capability `device_cad_model`
   (`computational_prototype`, `VALIDATION.md#device-cad-model`); the
   descriptor, the inventory and the envelope fixture are regenerated;
   the CI gains a `cad` job that installs the pinned library with the
   extra, runs the CAD tests and a benchmark smoke.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty; no material property, load, field or neutronic quantity is
carried by any body. The STEP file is an export of the record, never its
source; a STEP file is not an engineering model. The library's addendum
to its ADR 0006 (continuation-line unfolding) was found by this pilot:
the writer wraps long lines at a column counted from the pre-renumbering
identifier lengths, so the library's normaliser now unfolds the
continuation lines before renumbering; the re-pin in item 3 consumes that
correction. The torus-segment and sphere-shell primitives needed by the
toroidal and inertial families are later library increments; this
repository consumes them when its geometry needs them.
