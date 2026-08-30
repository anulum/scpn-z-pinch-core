<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)

**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. The `self_magnetic` registry family
contains several pulsed-current devices (Z-pinch variants, theta pinch,
dense plasma focus) and borders MagLIF; a boundary decision was needed on
which share one repository.

## Decision

1. `SCPN-Z-PINCH-CORE` owns exactly two registry configurations:
   `z_pinch` and `sheared_flow_z_pinch`. Both confine a linear column by
   the azimuthal field of its own axial current with Bennett-type
   equilibrium and the same driver, diagnostic, and lifecycle class;
   sheared-flow stabilisation is a configuration parameter on that shared
   physics, not a separate family.
2. The repository owns device-level truth only: column configuration
   policy, pulsed-power lifecycle semantics, mode-amplitude and
   flow-profile diagnostic declarations, actuator-response model
   boundaries, the safety-envelope declaration, and the device-owned
   CONTROL adapter specification.
3. Solver mathematics remains in `SCPN-FUSION-CORE` until an exact surface
   passes the family migration gate. No solver code is copied here.
4. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only).
   Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation remains in `SCPN-STUDIO`; this project is
   `not_federated`.
5. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **One repository for all self-magnetic pinches** (+ theta pinch, dense
  plasma focus): rejected — the theta pinch reverses the current/field
  roles (azimuthal induced current, axial compression field) and the
  dense plasma focus is defined by coaxial rundown and focus formation;
  drivers, diagnostics, and lifecycle stages differ (surfaces 1–4).
- **Separate repositories for static and sheared-flow variants**:
  rejected — all five boundary surfaces are substantially shared; the
  split would duplicate every contract for a stabilisation parameter.
- **Owning MagLIF here** (Z-pinch driver heritage): rejected — MagLIF is
  a magneto-inertial liner implosion with premagnetisation and laser
  preheat; the portfolio map assigns it to `SCPN-MIF-MAGLIF-CORE`.
- **Absorbing solver code at scaffold time**: rejected — violates the
  migration gate.

## Consequences

- Downstream consumers get one stable identity per Z-pinch configuration
  and a manifest to bind against.
- The validator fails on any capability or claim entry while maturity is
  `architecture_only`.
- Boundary changes require a portfolio-level map change first; a future
  ADR records any such change here.
