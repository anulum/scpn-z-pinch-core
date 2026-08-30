<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — GOVERNANCE
-->

# Governance

## Ownership and decision authority

The project is owned by Miroslav Šotek (ANULUM, Marbach SG, Switzerland;
ORCID 0009-0009-3560-0851). Final authority over scope, releases, licensing,
publication, and every outward action rests with the owner.

The repository is stewarded by the SCPN Reactor Systems Research Group, which
coordinates the reactor-family portfolio and its cross-project boundaries.

## Boundary control

The project boundary — the assignment of `sheared_flow_z_pinch` and
`z_pinch` to this repository, and the exclusions listed in the
README — derives from the SCPN reactor family repository standard and its
machine-readable map. A change to that assignment is a portfolio-level
decision: it must update the canonical map, recount the registry
intersection, and notify affected project owners before this repository
adopts it. This repository never redefines its own boundary unilaterally.

## Change process

1. Changes land locally on `main` after the full gate sequence in
   `VALIDATION.md` passes.
2. Evidence maturity advances only per the reactor family standard: each
   public capability declares exactly one state, and no state is advanced by
   repository age, code volume, or simulation output alone.
3. Contract surfaces (domain manifest schema, CONTROL adapter specification,
   Studio descriptor) change only through versioned revisions that preserve
   or explicitly break compatibility, never silently.
4. Remote creation, push, package publication, release, deployment, and
   external registrations each require separate owner authority.

## Roles

| Role | Holder | Authority |
|---|---|---|
| Owner | Miroslav Šotek | all final decisions, all outward actions |
| Steward | SCPN Reactor Systems Research Group | portfolio boundaries, cross-project contracts |
| Maintainers | per `.github/CODEOWNERS` | review of changes within the boundary |
