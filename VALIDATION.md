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

Every gate currently active in this repository, with its exact scope. There
is no reactor-capability validation because no reactor capability exists;
these gates validate the repository infrastructure and the truthfulness of
its architecture-only state.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `tools/` and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict tools tests` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, empty capability/claim inventories, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates (definitions present; run on the hosted platform once a
remote exists under separate owner authority)

| Workflow | Purpose |
|---|---|
| `ci.yml` | run-always lint, format, typing, tests, coverage, domain checks |
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
