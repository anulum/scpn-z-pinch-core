<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — Architecture summary
-->

# Architecture summary

`SCPN-Z-PINCH-CORE` is the device-family owner for Z-pinch systems
(classical and sheared-flow-stabilised) inside the SCPN Reactor Systems
Research Group. The repository holds four implemented capabilities at
`computational_prototype` — the device configuration model (ADR 0002),
the diagnostic and clock semantics model (ADR 0003), the level-0
device physics (ADR 0005; cited closed-form models with optional native
kernels in `rust/`) and the device 3D model (ADR 0006 and ADR 0007;
validated geometry, deterministic analytic-surface meshes composed on the
pinned shared kernel library `scpn-reactor-kernels`, open exports), all in
`src/scpn_z_pinch_core/` — alongside the
device boundary, its ecosystem contracts, and the validation tooling
that enforces them.

The authoritative architecture record is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The ownership decision and
its consequences are fixed in
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).

Boundary in one paragraph: this repository owns Z-pinch plant and
experiment truth — configuration policy for linear columns confined by the
azimuthal field of their own axial current (Bennett equilibrium, m=0/m=1
instability structure, sheared-axial-flow stabilisation), pulsed-power
lifecycle semantics (charge, trigger, formation, pinch, burn window,
disassembly) with restrike and bank-fault hazard records, nanosecond-class
diagnostic and clock declarations, actuator-response boundaries limited to
shot-to-shot programming, safety-envelope declarations, and the
device-owned CONTROL adapter specification. Solver mathematics stays in
`SCPN-FUSION-CORE`; typed semantics stay in `SCPN-PHASE-ORCHESTRATOR`
(review-only); admitted control actions are formed only by `SCPN-CONTROL`;
independent machine protection keeps the final veto; portfolio presentation
belongs to `SCPN-STUDIO`, towards which this project is `not_federated`.
