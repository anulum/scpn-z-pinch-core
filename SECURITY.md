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
| `main` at its current tip | yes — the only supported state |
| Any released version | none exists |

The evidence maturity is `computational_prototype` (see the README). The
executable surface is the Python package `scpn_z_pinch_core` under `src/`
and the validation tooling under `tools/`. The package parses four public
JSON documents (device configuration, device geometry, diagnostic plan and
plan envelope), evaluates level-0 physics through the pinned SCPN reactor
kernel library (optionally through its native kernels), builds two
geometry models and writes STL, glTF and STEP exports to paths the caller
chooses; the kernel library is installed with its `cad` extra, which brings
the B-rep toolchain.
There is no network service, no daemon, no controller and no hardware or
actuation path.

## Reporting a vulnerability

Report privately through GitHub private vulnerability reporting
(**Security → Report a vulnerability** on this repository) or by email to
**protoscience@anulum.li**. Do not open public issues for vulnerabilities.
Include the affected file, a reproduction and the impact you see. You will
receive an acknowledgement, and coordinated disclosure, including any
GitHub security advisory, will be agreed before a public statement.
Good-faith research within this scope is welcome.

## Response scope

In scope: the package parsers and models under `src/`, the validation
tooling, workflow definitions, the hash-locked dependency sets, licensing
and provenance metadata, and any way the repository could misrepresent its
evidence maturity or safety boundaries (for example, a path that lets the
capability inventory or Studio descriptor claim more than the manifest).

Out of scope: the scientific accuracy of the level-0 relations (the
claim inventory is empty; accuracy questions are ordinary issues), hardware
and actuation paths (none exist and none are permitted here), the
machine-protection domain (independent by design), and third-party
infrastructure. A vulnerability inside the first-party kernel library is
reported to [SCPN Reactor Kernels](https://github.com/anulum/scpn-reactor-kernels/security);
one inside the third-party CAD toolchain goes to its own maintainers.

## Non-claims

This policy is not a safety certification and does not make the project
machine-ready. The threat model and fail-closed behaviour are described in
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
