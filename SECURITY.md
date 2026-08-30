<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — SECURITY
-->

# Security policy

## Supported states

| State | Supported |
|---|---|
| Local `main` at current tip | yes — the only supported state |
| Any released version | none exists |

The repository is `architecture_only`: its executable surface is limited to
the validation tooling under `tools/` (manifest validator, descriptor
derivation, inventory generation, preflight orchestration). There is no
network service, no daemon, no solver, no controller, and no hardware path.

## Reporting a vulnerability

Report privately to **protoscience@anulum.li**. Do not open public reports.
Include the affected file, a reproduction, and the impact you see. You will
receive an acknowledgement, and coordinated disclosure will be agreed before
any public statement. Good-faith research within this scope is welcome.

## Response scope

In scope: the validation tooling, workflow definitions, licensing and
provenance metadata, and any way the repository could misrepresent its
evidence maturity or safety boundaries (for example, a path that lets the
capability inventory or Studio descriptor claim more than the manifest).

Out of scope: reactor physics claims (none exist), hardware and actuation
paths (none exist and none are permitted here), the machine-protection
domain (independent by design), and third-party infrastructure.

## Non-claims

This policy is not a safety certification and does not make the project
machine-ready. Fail-closed behaviour of the validators is described in
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
