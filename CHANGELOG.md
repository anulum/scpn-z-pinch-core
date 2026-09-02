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

- Device 3D model (`src/scpn_z_pinch_core/geometry/`), the fourth
  implemented capability at `computational_prototype` (ADR 0006): a
  validated coaxial `DeviceGeometry` (electrodes, acceleration and
  assembly regions, chamber, end walls) with canonical digest and strict
  parser; a vendored deterministic unit circle (polynomial sine/cosine
  with exact symmetry) so every vertex is bit-exact across backends;
  solid-cylinder and annular-tube tessellation; a closed-mesh contract
  (`TriangleMesh`: closure and orientation validation, signed volume,
  surface area, canonical bytes, SHA-256); the composed `DeviceModel3D`
  record (`scpn.z-pinch-3d-model.v1`) with a pinned reference digest;
  binary STL and glTF 2.0 binary exports with the consumer contract
  `docs/DEVICE_3D_MODEL_CONTRACT.md`. Native kernels in `rust/src/geometry/`
  reproduce every vertex, face and measure bit for bit, proven by parity
  tests; a standard-conformant benchmark (`benchmarks/device_model_3d.py`)
  with a committed local artefact and a `docs/benchmarks.md` section. The
  manifest declares the capability and the owned domain
  `device_geometry_and_3d_model` with the non-claims reworded; descriptor
  and inventory regenerated; the envelope fixture regenerated for the new
  `manifest_sha256` (plan bytes unchanged). Gates: the `rust` CI job runs
  the geometry parity file and a second benchmark smoke; `mypy` resolves
  the shared test fixtures module.

- Level-0 device physics (`src/scpn_z_pinch_core/physics/`), the third
  implemented capability at `computational_prototype` (ADR 0005): the
  Bennett equilibrium with its profiles, field, enclosed current and
  Alfvén quantities; ideal-MHD growth-rate estimates with the Kadomtsev
  m=0 criterion in closed form on the Bennett profile; the
  Shumlak-Hartman sheared-flow criterion; the Pease-Braginskii current
  in the published closed form with NRL formulary coefficients; and a
  canonical `Level0PhysicsRecord` with explicit `ModelInputs`. Native
  kernels (`rust/`, crate `scpn-z-pinch-rs`, optional distribution
  `scpn-z-pinch-native`) reproduce every value bit for bit, proven by
  parity tests; a standard-conformant benchmark
  (`benchmarks/level0_physics.py`) with a committed local artefact and
  `docs/benchmarks.md`. The manifest declares the capability and the
  owned domain `analytic_device_physics_models`; descriptor and
  inventory regenerated; the envelope fixture regenerated for the new
  `manifest_sha256` (plan bytes unchanged). Gates extended: `mypy` scope
  includes `benchmarks/`, a `rust` CI job runs the crate gates, parity
  and a benchmark smoke, `make rust` locally.

- Diagnostic-plan depth: per-channel signal inventories, frame
  transformations with a fixed kind-admissibility table and connectivity
  rule, and a clock topology partitioning the physical clocks into rooted
  domains with a star of relations to the reference root. Envelope
  `scpn.reactor-diagnostic-plan-envelope.v1` bumped to `1.2.0`; the
  fixture is regenerated from the public surface and re-pinned. All new
  members are declarations: no observation, phase, mapping, or control
  authority is created.
- Local gate parity with the wider ecosystem: the pre-commit chain now
  also runs REUSE licensing compliance and a typographical checker
  (`_typos.toml` carries the deliberate reactor vocabulary), and adds
  the upstream YAML, TOML, large-file and private-key guards. Licensing
  and spelling were previously verified only in hosted CI, so a broken
  REUSE annotation — including the aggregate annotation that covers the
  binary header images — could reach a push before being caught.
- Generated repository header artwork: `docs/assets/generate_header.py`
  renders three deterministic 1280x640 images from the repository's own
  domain surface (the pinch column used by the README, the
  static-versus-sheared class split, and the Bennett window gate).
- Modular hosted-workflow surface per the ecosystem workflow-modularity
  standard: `ci.yml` reduced to a coordinator with a stable fail-closed
  `gate` job, single-responsibility reusable workflows for static
  analysis/repository policy and for tests, a versioned machine-readable
  inventory (`.github/workflow-inventory.json`,
  `scpn.workflow-inventory.v1` `1.0.0`), and a fail-closed modularity
  guard (`tools/audit_workflows.py`) enforced locally (preflight gate,
  pre-commit hook) and in hosted CI. The duplicate documentation-links
  step was removed from the CI chain; `docs.yml` remains the single
  owner of documentation validation.

- Typed reference frames, clock synchronisation relations (synthetic
  bounds only; no correlation evidence claimed), and per-channel
  acquisition windows and element counts in the diagnostic model;
  hardened decoders (recursive exact-key, duplicate-member, and
  byte-canonical refusal in both codecs); envelope `1.1.0` adding
  `manifest_sha256` over the committed canonical `reactor-domain.json`
  (fixture regenerated; byte hash re-pinned in tests).

- Portable diagnostic-plan envelope
  (`src/scpn_z_pinch_core/plan_envelope.py`,
  `scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): a
  producer-owned, canonically serialised wrapper carrying project
  identity, exact owned configurations, capability and maturity,
  synthetic/review-only/non-actuating statements, both SPO registry
  pins, the inner plan's SHA-256, the producer revision, and fixed
  no-observation/no-control non-claims; strict parsers refuse unknown,
  duplicate, and non-finite members, and an immutable committed fixture
  exercises the exchange end to end.

- Diagnostic and clock semantics model
  (`src/scpn_z_pinch_core/observability.py`), the second implemented
  capability at `computational_prototype`: frozen clock, channel,
  deferral, and plan objects aligned fail-closed with the pinned SPO
  observability-profile catalogue (candidate applicability, carrier
  admissibility, exact class-fixed evidence vocabularies, clock-kind
  compatibility, Nyquist and event-timing bounds); cited advisory band
  and timing checks; canonical serialisation with SHA-256 digests and
  strict NaN-rejecting round-trip parsing (design record
  `docs/adr/0003-diagnostic-clock-semantics.md`).

- Device configuration model (`src/scpn_z_pinch_core/`), the first implemented
  capability at `computational_prototype`: validated frozen parameter
  objects with device-specific invariants and documented, cited
  consistency estimates; canonical serialisation with SHA-256 digests
  and strict NaN-rejecting round-trip parsing; a data-only pin to the
  SPO reactor registry; and the reactor-domain validator branch
  enforcing populated capability inventories with the ADR 0002
  evidence-maturity ceiling rule (design record
  `docs/adr/0002-device-configuration-model.md`).

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
