<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z Pinch Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: cited closed-form models with native parity

Status: accepted (2026-09-02). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

Until this record the repository carried no physics beyond the Bennett
temperature used as a consistency instrument. Every device manifest
excludes `solver_mathematics_and_validation_evidence` (owner
SCPN-FUSION-CORE), and no FUSION seam will ever cover the z-pinch
family. The device owner therefore needs its own bounded, exercised,
published physics: closed-form models from the device's own literature,
evaluated on the validated configuration, without solving any equation.

## Decision

1. A new owned domain `analytic_device_physics_models` is declared in
   `reactor-domain.json`: device-owned closed-form and 0-D models from
   the device literature. It is disjoint from solver mathematics: no
   solver code is copied, no equilibrium or stability equation is
   solved, and no FUSION seam is implied or consumed.
2. Four models, each with its published form cited in the module
   docstring, live one per module under `src/scpn_z_pinch_core/physics/`:
   the Bennett equilibrium (Bennett 1934; Haines 2011 §2), ideal-MHD
   growth-rate estimates with the Kadomtsev m=0 criterion (Kadomtsev
   1966; Haines 2011 §5), the Shumlak-Hartman sheared-flow criterion
   (PRL 75 (1995) 3285), and the Pease-Braginskii current in the closed
   form of Klíř (2005), arXiv:physics/0703207, eq. (2.20), with NRL
   Plasma Formulary coefficients. A composed `Level0PhysicsRecord`
   serialises canonically with a SHA-256 digest and carries fixed
   non-claims.
3. Inputs the configuration does not carry (ion mass, mean charge,
   axial wavenumber, adiabatic index, Coulomb logarithm, reporting
   radius) are declared explicitly in `ModelInputs`; nothing is
   defaulted silently.
4. Native kernels (`rust/`, crate `scpn-z-pinch-rs`, optional
   distribution `scpn-z-pinch-native` via maturin) mirror every
   evaluation with identical operation order using only `+ - * /` and
   `sqrt`; parity tests compare float64 bit patterns, never
   tolerances. The pure-Python floor remains the public API and the
   default; the native module is an optional accelerator reachable as
   `scpn_z_pinch_native`.
5. Performance numbers follow the ecosystem benchmark standard
   (warm-up, repeats, percentiles, one row per backend, provenance);
   the local artefact is committed and labelled non-isolated.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. VALIDATION states per model what is exercised and what is
not claimed. Reactivity, yield, gain and breakeven remain out of scope
and would need their own acceptance contract. The manifest change alters
`manifest_sha256` inside the plan envelope, so the envelope fixture is
regenerated from the public surface and re-pinned; the plan bytes and
`plan_sha256` are unchanged.
