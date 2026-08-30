<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — CHANGELOG
-->

# Changelog

## [Unreleased]

### Added

- Architecture-only repository scaffold: governance, security, licensing,
  REUSE metadata, contribution and support policies, and citation metadata.
- Machine-readable domain manifest `reactor-domain.json` binding the project
  to SCPN Phase Orchestrator reactor registry `1.0.0`
  (configurations `sheared_flow_z_pinch`, `z_pinch`).
- Device-owned CONTROL adapter specification and threat model.
- Derived Studio portfolio descriptor (`not_federated`) and generated
  capability inventory (zero implemented capabilities).
- Validation tooling: domain-manifest validator, descriptor derivation and
  inventory generation with drift checks, and a fail-closed preflight
  orchestrator, each with statement- and branch-complete tests.
- Continuous-integration, code-scanning, security-audit, documentation,
  SBOM, pre-commit, and Scorecard workflow definitions (read-only
  permissions; no publication or deployment workflows).

### Changed

- Studio portfolio descriptor schema ratified at version 1.1.0 after
  downstream review, before any consumer adoption (1.0.0 superseded
  unconsumed): canonical JSON Schema published in-repository with a strict
  unknown-field policy, explicit source repository, nullable lifecycle
  evidence pointer, nullable versioned control-intent reference, ratified
  capability item shape, and a machine-protection object (independent
  final-veto owner with availability `not_assessed`) replacing the former
  boolean flag.
