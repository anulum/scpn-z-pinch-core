<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — ROADMAP
-->

# Roadmap

Planned work and implemented capability are kept strictly separate. Anything
listed under "Planned" carries no implementation, no code, and no claim in
this repository until it appears in the capability inventory with evidence.

## Implemented (repository infrastructure, not reactor capability)

- Domain manifest (`reactor-domain.json`) with validator.
- Derived Studio portfolio descriptor (`not_federated`) with drift check.
- Generated capability inventory (truthfully empty) with drift check.
- CONTROL adapter specification (contract only, no implementation).
- Local and workflow gate definitions (lint, typing, tests, coverage,
  REUSE, security audit, SBOM, documentation checks).

- **Device configuration model** (landed 2026-08-31) — validated
  pinch-column and discharge objects for `sheared_flow_z_pinch` and
  `z_pinch` with hard flow-shear class invariants, the Bennett-relation
  temperature estimate (Bennett 1934), a documented plasma-regime
  advisory window, canonical digests, and the SPO registry data pin;
  `computational_prototype` (ADR 0002,
  `VALIDATION.md#device-configuration-model`). Electrode/injector
  geometry classes remain future work under the same capability.
- **Diagnostic and clock semantics** (landed 2026-08-31) — synthetic
  diagnostic-channel and clock declarations aligned fail-closed with the
  pinned SPO observability-profile catalogue (release `1.0.0`): candidate
  applicability, carrier admissibility, exact evidence vocabularies,
  clock-kind compatibility, Nyquist and event-timing bounds, canonical
  digests; the reference plan mirrors canonical practice
  (current/voltage event train, pinch-mode probe array, synthetic oscillator); `computational_prototype` (ADR 0003,
  `VALIDATION.md#diagnostic-and-clock-semantics`). No ingress is
  declared; the SPO semantic-profile state remains `not_declared`.
- **Level-0 device physics** (landed 2026-09-02) — four cited
  closed-form models evaluated on the validated configuration (Bennett
  equilibrium and profiles, ideal-MHD growth estimates with the
  Kadomtsev m=0 criterion, the Shumlak-Hartman sheared-flow criterion,
  the Pease-Braginskii current), a canonical `Level0PhysicsRecord`,
  optional native kernels bit-exact with the Python floor, and a
  standard-conformant benchmark; `computational_prototype` (ADR 0005,
  `VALIDATION.md#level-0-device-physics`). Follow-ups under the same
  capability: parameter-grid scans as the first compute hot path (which
  opens the multi-language chain with measured benchmarks per backend),
  and D-D reactivity under its own acceptance contract.
- **Device 3D model** (landed 2026-09-02) — validated coaxial device
  geometry (electrodes, acceleration and assembly regions, chamber, end
  walls), deterministic tessellation of six analytic bodies, a canonical
  `DeviceModel3D` record, binary STL and glTF 2.0 exports with a published
  consumer contract, and a standard-conformant benchmark;
  `computational_prototype` (ADR 0006, `VALIDATION.md#device-3d-model`).
  Since 2026-09-02 the unit circle, the primitives, the mesh contract and
  the serialisers are consumed from the shared kernel library
  `scpn-reactor-kernels`, pinned by commit object and inventory digest
  (ADR 0007), and the model is proven bit-exact against that library's
  native module. Follow-ups under the same capability: B-rep CAD solids (a
  separate tooling decision), coil and pulsed-power layouts, and mesh
  contracts for the engineering lanes.

## Planned (no implementation exists; ordering is not a commitment)
1. **Safety-envelope declaration** — machine-readable operational envelope
   (bank, current, repetition, electrode bounds) consumed by the CONTROL
   adapter contract.
2. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
3. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for pinch equilibrium and stability surfaces,
   strictly after the family migration gate proves exact replacement; no
   solver code is copied.
4. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Theta pinches, the dense plasma focus, MagLIF, the reversed-field pinch,
toroidal and open magnetic systems, laser and beam inertial systems,
generic controller mathematics, machine-protection logic, and any direct
actuation path.
