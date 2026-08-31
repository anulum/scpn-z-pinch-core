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

## Planned (no implementation exists; ordering is not a commitment)
1. **Diagnostic and clock semantics** — declared current/voltage,
   imaging, mode-amplitude, flow-profile, and neutron channels with
   nanosecond clock identities aligned with the SCPN Phase Orchestrator
   semantic profile.
2. **Safety-envelope declaration** — machine-readable operational envelope
   (bank, current, repetition, electrode bounds) consumed by the CONTROL
   adapter contract.
3. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
4. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for pinch equilibrium and stability surfaces,
   strictly after the family migration gate proves exact replacement; no
   solver code is copied.
5. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Theta pinches, the dense plasma focus, MagLIF, the reversed-field pinch,
toroidal and open magnetic systems, laser and beam inertial systems,
generic controller mathematics, machine-protection logic, and any direct
actuation path.
