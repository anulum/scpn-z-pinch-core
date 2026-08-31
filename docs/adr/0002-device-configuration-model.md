<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — ADR 0002: device configuration model
-->

# ADR 0002 — Device configuration model and evidence-maturity semantics

**Status:** accepted (2026-08-31)

**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The repository was established architecture-only (ADR 0001). The first
capability lane is the device configuration model for the two registry
configurations this repository owns (`sheared_flow_z_pinch`,
`z_pinch`). The claim boundary and repository-level `evidence_maturity`
semantics follow the family pilot.

## Decision

1. The package `scpn_z_pinch_core` implements the device configuration
   model as frozen, strictly typed value objects: the pinch column
   (radius, length), the discharge (peak current, ion line density),
   and the configuration container with the flow-shear declaration.
2. Claim boundary — identical to the family pilot: internal-consistency
   validation, cited textbook estimates with documented bounds,
   canonical serialisation with SHA-256 digest, and the data-only SPO
   registry pin. No claim about any real machine; every exercised
   parameter set is a synthetic test fixture.
3. Hard class invariants: `sheared_flow_z_pinch` requires a strictly
   positive flow-shear declaration — sheared axial flow is the
   stabilising mechanism that defines the class (U. Shumlak,
   C. W. Hartman, Phys. Rev. Lett. 75 (1995) 3285) — and the static
   `z_pinch` class requires exactly zero declared shear.
4. Derived quantity with citation: the Bennett-relation temperature
   ``T = mu0 I^2 / (16 pi N e)`` (equal ion and electron temperatures;
   W. H. Bennett, Phys. Rev. 45 (1934) 890). Advisory finding, reported
   by `consistency_report()` and never clamped: a Bennett temperature
   outside the documented model window ``[1 eV, 100 keV]`` of pinch
   plasma experiments.
5. Repository-level `evidence_maturity` = the highest state claimed by
   any capability entry; per-capability states are the authoritative
   claim surface.
6. Everything else is unchanged: review-only/non-actionable SPO
   profile, no adapter implementation, empty solver seams,
   `not_federated` Studio state, independent machine-protection veto,
   all non-claims.

## Consequences

- The Studio descriptor's `capabilities` array carries its first item
  (schema 1.1.0 data change only).
- The reactor-domain validator gains the populated-capabilities branch
  with the ceiling rule.
- Later lanes (current/imaging diagnostic semantics, safety envelope)
  build on these types; maturity advances per capability only with the
  evidence the family standard requires.
