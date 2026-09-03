<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — Threat model
-->

# Threat model

Scoped to the current `computational_prototype` state: the executable
surface is the package under `src/` and the validation tooling under
`tools/`; the valuable content is the contract metadata and the exported
model files. The model is revisited whenever a new surface (adapter
implementation, solver seam, federation) is added.

## Assets

| Asset | Why it matters |
|---|---|
| `reactor-domain.json` | source of project identity; downstream projects bind to it; carries the exact pin of the shared kernel library (`kernel_library`) |
| Pinned kernel library (`scpn-reactor-kernels` at one commit object) | every vertex of the 3D model and every export byte come from it; a substituted or drifted library would change numerics silently |
| Pinned CAD back-end (OpenCASCADE through the library's `cad` extra) | the B-rep solids and the STEP bytes come from third-party C++; a version drift changes the export bytes silently unless detected |
| `studio/portfolio-descriptor.json` | what the portfolio layer would ingest; must never overstate maturity |
| `capability-inventory.json` | public truthfulness of "zero implemented capabilities" |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | safety-relevant contract text (no-direct-actuation semantics) |
| Workflow definitions | future execution with hosted credentials |
| Licensing/provenance metadata | legal integrity of the repository |

## Trust boundaries and actors

- **Repository editor** (owner, reviewed contributor): trusted after review;
  every change passes the gate sequence.
- **Downstream consumer** (SPO, CONTROL, STUDIO tooling): trusts the
  manifest only as far as its digest and validator verdicts; must not be
  able to read more authority out of the metadata than the manifest grants.
- **Hosted CI** (future, after a remote exists): untrusted-by-default
  execution environment; workflows therefore carry empty top-level
  permissions, per-job least privilege, pinned action commit objects, and
  bounded timeouts.
- **Supply chain**: the pinned Python toolchain in `requirements-dev.txt`
  and the pinned GitHub Actions are the only third-party code paths.

## Misuse paths and mitigations

| Misuse path | Mitigation |
|---|---|
| Editing the descriptor or inventory to imply implemented capability | both files are generated; `--check` drift gates in pre-commit, preflight, and CI fail on any manual edit |
| Adding a capability or claim without evidence | validator fails on non-empty `capabilities`/`claims` at `architecture_only` |
| Re-pinning the SPO registry silently | validator fails on version/digest mismatch against the manifest's recorded values (and against the portfolio map when present) |
| Treating review-only semantics or a Studio request as an actuator command | `spo_semantic_profile.actionable` is `false`; adapter specification defines no actuation verb; machine-protection statement is a required manifest field the validator enforces |
| Workflow tampering towards write authority | scaffold contains no write-authority workflow; permissions are empty at top level; action references must be 40-hex commit objects (shared Tier-0 audit enforces) |
| Dependency substitution | exact version pins; dependabot updates land only through the full gate sequence |
| Re-pinning the kernel library silently or inconsistently | the manifest, the `pyproject.toml` dependency, the installed package version and the CI install steps must name one commit object (contract test); the validator enforces the 40-hex commit, the 64-hex inventory digest and the consumed kernel identifiers; parity against the library's native module runs in CI |
| Presenting the STEP export as an engineering model or a drawing | the CAD record carries fixed non-claims and per-body evidence bounds; the contract document states the file is an export of the record, never a source; determinism is claimed only within the pinned back-end environment, whose versions the record carries |
| CAD back-end version drift | the back-end versions are pinned by the library's `cad` extra and recorded in the CAD record; a pinned reference digest in the tests fails on any byte drift, and a version bump is a governed data change (re-pinned digests) |
| Secret introduction | no secrets exist or are needed; security-audit workflow and review gates scan the diff |

## Fail-closed behaviour

Every validator in `tools/` exits non-zero on the first unrecoverable
finding, treats a missing file, unparseable JSON, duplicate JSON keys, or an
unknown schema as failure (never as "skip"), and prints the exact failing
check. The preflight orchestrator aggregates gate results and fails if any
gate fails or cannot run — a missing tool is a failed gate, not a pass.

## Residual risks

- The ecosystem cross-check against the portfolio map runs only where the
  canonical map file is present (the local canonical checkout); a standalone
  checkout validates manifest-internal truth only. Accepted: the map is not
  distributed with the repository by design.
- Licence-text files and generated JSON carry no in-file provenance header
  (format constraints); REUSE.toml annotations close this gap.
- No cryptographic signing of the manifest exists yet; digest pinning covers
  integrity of derivation, not authorship. Signing is a future portfolio
  decision.
