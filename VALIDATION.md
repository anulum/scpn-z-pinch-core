<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests benchmarks` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Native kernels | `make rust` (`cargo fmt --check`, `cargo clippy --all-targets --features python -- -D warnings`, `cargo test` in `rust/`) | formatting, lints with warnings denied, kernel unit tests |
| Native parity | `pytest -q tests/test_physics_native_parity.py` | bit-exact float64 agreement of every native kernel with the Python floor (skipped hermetically when the optional native module is absent) |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage; native crate gates, parity and benchmark smoke |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-Z-PINCH-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`PinchColumn`, `Discharge`,
  `DeviceConfiguration`) rejecting non-finite values, non-positive
  extents, and the hard flow-shear class invariants: strictly positive
  declared shear for `sheared_flow_z_pinch` (the stabilising mechanism
  that defines the class; Shumlak & Hartman, PRL 75 (1995) 3285) and
  exactly zero for the static `z_pinch` — every rejection branch is
  tested.
- The Bennett-relation temperature `T = mu0 I^2 / (16 pi N e)`
  (Bennett, Phys. Rev. 45 (1934) 890) as a documented derived quantity,
  with an advisory finding outside the documented `[1 eV, 100 keV]`
  pinch plasma window, reported and never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are advisory regime checks, not equilibrium, stability,
  or yield results; no benchmark, dataset, solver, controller, or
  experimental correlation exists in this repository.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, unresolvable event-timing bounds,
  and incomplete candidate coverage — every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- A reference plan mirroring canonical practice with synthetic
  declarations: current/voltage event train, pinch-mode probe array, synthetic oscillator, each bound to its clock domain.
- Documented advisory band and timing checks with their sources stated
  in the code: sausage/kink instability bands of 0.1–100 MHz and ~100 ns drive timing (Shumlak and Hartman 1995); findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for this device family remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_z_pinch_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). The envelope is `1.1.0`, adding
`manifest_sha256` — the SHA-256 of the committed canonical
`reactor-domain.json` — verified in tests against the committed file.
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion;
`1.1.0` remains historical custody at the consumer) adds three typed
declaration surfaces, every branch under the 100 % statement-and-branch
gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; a `timing_marker` in `"s"` exactly for
  event-relative channels and forbidden otherwise; numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`): the frame kinds this
  repository may declare admit no transformation pair, so the
  transformation tuple must be empty and a second frame — which could
  never be connected — is refused. The model, its admissibility table
  and its declaration-only semantics (`evidence_claimed` always `False`)
  are shared with the portfolio.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design record: `docs/adr/0005-level0-device-physics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate
(`src/scpn_z_pinch_core/physics/`):

- **Bennett equilibrium** (Bennett, Phys. Rev. 45 (1934) 890; Haines,
  Plasma Phys. Control. Fusion 53 (2011) 093001, §2): the integral
  pressure balance, the Bennett density and pressure profiles, the
  azimuthal field of that profile, the enclosed current, and the Alfvén
  speed and transit time at the on-axis density. Tests close the
  pressure balance to machine precision, integrate the profile back to
  the line density, verify Ampère's law at sampled radii, and check the
  `I^2`, `1/N` and `m_i^{-1/2}` scalings.
- **Ideal-MHD stability estimates** (Haines 2011 §5; Kadomtsev, Reviews
  of Plasma Physics 2 (1966) 153): the order-of-magnitude growth rate
  `gamma ~ k v_A` for a declared wavenumber and the Kadomtsev m=0
  criterion `-d ln p / d ln r < 4 gamma_ad / (2 + gamma_ad beta)` on the
  Bennett profile in closed form. Tests reproduce the published
  conclusion that the Bennett profile is sausage-unstable at every radius
  for `gamma_ad = 5/3` and that the reduced criterion flips exactly at
  `gamma_ad = 2`.
- **Sheared-flow stabilisation** (Shumlak and Hartman, PRL 75 (1995)
  3285): the threshold `dv_z/dr > 0.1 k v_A` for a declared wavenumber
  and the disposition of the declared shear; the static class reports
  no stabilisation.
- **Pease-Braginskii current** (Pease 1957; Braginskii 1958) in the
  published closed form of Klíř, The Study of a Fibre Z-Pinch, PhD
  thesis, CTU Prague (2005), arXiv:physics/0703207, eq. (2.20), with the
  NRL Plasma Formulary Spitzer and bremsstrahlung coefficients converted
  to SI. Tests reproduce the quoted hydrogenic reference value
  (1.37 MA against the literature's ≈ 1.4 MA at `ln Lambda = 10`) and the
  `sqrt(ln Lambda)` scaling.
- A composed `Level0PhysicsRecord` (`scpn.z-pinch-level0-physics.v1`
  `1.0.0`) with canonical bytes, SHA-256 digest and fixed non-claims,
  built from the validated configuration and explicit `ModelInputs`;
  every input rejects non-positive and non-finite values.
- **Native parity**: the Rust crate in `rust/` mirrors every kernel with
  identical operation order; `tests/test_physics_native_parity.py`
  compares float64 bit patterns over a 72-point parameter grid plus the
  stability, criterion and critical-current inputs (99 cases). The
  native module is optional; the Python floor is the public API.
- **Benchmark**: `benchmarks/level0_physics.py` per the ecosystem
  benchmark standard; results in `docs/benchmarks.md` and the committed
  local artefact `benchmarks/results/level0_physics.local.json`.

Bounded claims — what is NOT claimed:

- Every number is a closed-form evaluation of a cited published model on
  a synthetic configuration; no equilibrium, stability or transport
  equation is solved, and no linear eigenvalue problem exists here.
- No reactivity, yield, gain, breakeven or confinement-time statement is
  made; the Pease-Braginskii regime label is an energy-balance
  disposition of the cited model, not a prediction.
- No value describes, approximates or validates any real machine; the
  benchmark measures per-point evaluation cost of two implementations of
  the same closed forms, not physics.
- Maturity stays `computational_prototype`; `benchmark_validated` would
  require documented accepted analytical cases with thresholds, which
  this record does not claim.
