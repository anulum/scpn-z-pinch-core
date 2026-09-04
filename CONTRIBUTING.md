<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z-Pinch Core — CONTRIBUTING
-->

# Contributing

The repository is public and its gates run in CI on every push.
Contributions are coordinated directly with the owner
(protoscience@anulum.li).

## Ground rules

1. **Truthful maturity.** `reactor-domain.json` declares the evidence
   maturity and is the only place it is written; this file does not repeat
   it, because a value kept in two places goes stale in one of them. Do not
   add placeholder APIs, toy solvers, fabricated data, empty tests,
   readiness language, or any capability or claim entry without the
   evidence the reactor family standard requires for the maturity the
   manifest declares.
2. **Boundary discipline.** Work stays inside the Z-pinch device boundary.
   Solver mathematics belongs to `SCPN-FUSION-CORE`; typed semantics to
   `SCPN-PHASE-ORCHESTRATOR`; control admission to `SCPN-CONTROL`;
   presentation to `SCPN-STUDIO`. Nothing here actuates hardware.
3. **Complete units.** A change ships with its implementation, strict typing,
   NumPy-convention docstrings, tests (statement- and branch-complete for new
   executable code), and documentation in the same commit.
4. **Model fidelity.** When physics models arrive, each must match its cited
   publication exactly within a declared applicability domain; simplified
   proxies cannot carry full-fidelity claims.
5. **Licensing and provenance.** Every file carries the seven-line
   provenance header in its native comment syntax (HTML comment in rendered
   Markdown; `REUSE.toml` annotations where a format has no comments).
   `reuse lint` must pass.
6. **Language and tone.** British English; descriptive names; no
   self-applied quality labels; no internal planning codes in any tracked
   file.

## Workflow

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
make lint typecheck test validate   # or: make preflight
```

All gates in `VALIDATION.md` must pass before a commit is proposed. Commits
are atomic, descriptive, and staged by explicit pathspec. History is never
rewritten.

## Security-relevant changes

Anything touching the threat model, the CONTROL adapter specification, or the
safety-envelope declarations follows `SECURITY.md` and requires owner review.
