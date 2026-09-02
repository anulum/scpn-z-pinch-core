<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-Z-PINCH-CORE` is the device-family owner for Z-pinch systems in the
SCPN Reactor Systems Research Group portfolio. The
repository owns three implemented capabilities at
`computational_prototype` in `src/scpn_z_pinch_core/`: the device
configuration model (design record ADR 0002, evidence record
`VALIDATION.md#device-configuration-model`), the diagnostic and
clock semantics model (design record ADR 0003, evidence record
`VALIDATION.md#diagnostic-and-clock-semantics`) and the level-0
device physics (design record ADR 0005, evidence record
`VALIDATION.md#level-0-device-physics`; owned domain
`analytic_device_physics_models`, disjoint from solver mathematics).
Every other
section below describes boundaries and contracts. The claim inventory is
empty; capability and claim inventories are generated and drift-checked.

## The five-surface boundary

1. **Governing confinement physics** — self-magnetic confinement of a
   linear plasma column by the azimuthal field of its own axial current
   (`self_magnetic` registry family). The classical `z_pinch` equilibrium
   is Bennett-type pressure balance, unstable to sausage (m=0) and kink
   (m=1) modes on Alfvénic timescales; the `sheared_flow_z_pinch` embeds
   the same equilibrium in a sheared axial flow whose velocity gradient
   stabilises those modes and extends column lifetime. The two
   configurations share the confinement principle, driver class,
   diagnostics, and lifecycle; the stabilisation mechanism is the
   configuration parameter. Theta pinches (azimuthal induced current),
   the dense plasma focus (coaxial rundown and focus), MagLIF
   (premagnetised liner implosion), and the toroidal RFP fail this
   sharing test and are excluded.
2. **Primary driver and energy delivery** — pulsed-power drive: capacitor
   banks or pulse-forming lines discharging axial current through the
   column between electrode assemblies; for the sheared-flow variant,
   coaxial-gun plasma injection establishing the flow profile.
3. **Plant and shot lifecycle** — single-shot pulsed lifecycle: charge,
   trigger, column formation (or injection), pinch phase with
   instability-or-stabilised evolution, neutron-producing window where
   achieved, and disassembly. Device-level hazard semantics cover
   electrode damage, restrike, and bank-fault transients.
4. **Diagnostic, reference-frame, and clock model** — axial/radial column
   conventions, current and voltage monitors, interferometry and imaging
   of column radius, mode-amplitude declarations for m=0/m=1, flow-profile
   channels for the sheared-flow variant, and nanosecond-resolved
   shot-relative clock identities.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE`, review-only semantics towards
   `SCPN-PHASE-ORCHESTRATOR`, and the device-owned CONTROL adapter
   specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-Z-PINCH-CORE (device truth: self-magnetic column policy, pulsed
                   lifecycle, mode/flow diagnostics, safety envelope,
                   adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   └──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated inventory of the three implemented capabilities |
| `src/scpn_z_pinch_core/physics/` | level-0 device physics (four cited closed-form models, composed record) |
| `rust/` | optional native kernels (`scpn-z-pinch-rs`), bit-exact with the Python floor |
| `benchmarks/` | standard-conformant benchmark and committed local artefact |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `src/` and `tools/`, native parity tests |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`; unknown
  schemas are rejected by consumers.
- The Studio descriptor is derived deterministically and embeds the
  manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at `0.1.0-spec`.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`.

## What would change this architecture

Acceptance of a FUSION solver seam through the family migration gate,
ratification of an SPO `ControlIntent`-class contract, or Studio federation
after a real capability passes producer and consumer gates — each recorded
as a versioned contract change in a new ADR.
