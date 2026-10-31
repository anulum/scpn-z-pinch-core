# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — commit trailer verifier

"""Validate commit-message trailers as the ``commit-msg`` hook.

The hook receives the pending commit-message file path and rejects messages
without exactly one required authorship line and exactly one vendor-neutral
``Seat:`` trailer immediately preceding it, messages carrying the superseded
``Co-Authored-By:`` trailer, and commit subjects containing outward-facing
self-praise terms.

``--audit-range REV_RANGE`` applies the same rules, read-only, to every
commit of an existing git revision range (for example ``origin/main..main``)
and reports each violating commit by its abbreviated hash and subject.
History is never rewritten; commits older than the policy are reported as
they are.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

REQUIRED_AUTHORSHIP_LINE: Final = (
    "Authored by Anulum Fortis & Arcane Sapience (protoscience@anulum.li)"
)
LEGACY_COAUTHOR_RE: Final = re.compile(r"^\s*Co-Authored-By:", re.IGNORECASE)
SEAT_PREFIX_RE: Final = re.compile(r"^\s*Seat:")
SEAT_TRAILER_RE: Final = re.compile(r"^Seat:\s+([A-Za-z0-9][A-Za-z0-9_-]{0,63})\s*$")
FORBIDDEN_SEAT_PREFIXES: Final = (
    "claude-",
    "codex-",
    "gemini-",
    "grok-",
    "kimi-",
    "openai-",
)
BANNED_SUBJECT_RE: Final = re.compile(
    r"\b(world-class|best-in-class|state-of-the-art|cutting-edge|revolutionary"
    r"|groundbreaking|unrivalled|elite|comprehensive|robust|leveraging)\b",
    re.IGNORECASE,
)


def _subject_line(message: str) -> str:
    """Return the first non-empty commit-message line.

    Parameters
    ----------
    message
        Full commit-message text.

    Returns
    -------
    str
        The stripped subject line, or an empty string.
    """
    return next((line.strip() for line in message.splitlines() if line.strip()), "")


def _seat_violations(lines: list[str], authorship_indices: list[int]) -> list[str]:
    """Return validation errors for the ``Seat:`` trailer.

    Parameters
    ----------
    lines
        Commit-message lines.
    authorship_indices
        Indexes of lines equal to the required authorship line.

    Returns
    -------
    list[str]
        Violations; empty when the trailer is valid.
    """
    seat_indices = [i for i, line in enumerate(lines) if SEAT_PREFIX_RE.match(line)]
    if not seat_indices:
        return ["missing `Seat: <seat-id>` trailer"]
    if len(seat_indices) != 1:
        return ["expected exactly one `Seat: <seat-id>` trailer"]
    seat_index = seat_indices[0]
    match = SEAT_TRAILER_RE.match(lines[seat_index].strip())
    if match is None:
        return ["invalid `Seat: <seat-id>` trailer"]
    violations: list[str] = []
    seat_id = match.group(1).lower()
    if seat_id.startswith(FORBIDDEN_SEAT_PREFIXES):
        violations.append("vendor-prefixed `Seat:` trailer is forbidden")
    if len(authorship_indices) == 1:
        authorship_index = authorship_indices[0]
        between = lines[seat_index + 1 : authorship_index]
        if seat_index >= authorship_index or any(line.strip() for line in between):
            violations.append(
                "`Seat:` trailer must immediately precede the authorship line"
            )
    return violations


def message_violations(message: str) -> list[str]:
    """Return commit-message policy violations.

    Parameters
    ----------
    message
        Full commit-message text.

    Returns
    -------
    list[str]
        Empty when the message satisfies the local agent commit policy.
    """
    lines = message.splitlines()
    violations: list[str] = []
    authorship_indices = [
        i for i, line in enumerate(lines) if line.strip() == REQUIRED_AUTHORSHIP_LINE
    ]
    if not authorship_indices:
        violations.append("missing required authorship line")
    elif len(authorship_indices) != 1:
        violations.append("expected exactly one authorship line")
    violations.extend(_seat_violations(lines, authorship_indices))
    if any(LEGACY_COAUTHOR_RE.match(line) for line in lines):
        violations.append("legacy `Co-Authored-By:` trailer is forbidden")
    banned = sorted(
        {m.group(1).lower() for m in BANNED_SUBJECT_RE.finditer(_subject_line(message))}
    )
    if banned:
        violations.append(f"banned public subject term(s): {', '.join(banned)}")
    return violations


class RangeAuditError(RuntimeError):
    """A revision range could not be read from git."""


def _git(root: Path, *args: str) -> str:
    """Run one read-only git command and return its standard output.

    Parameters
    ----------
    root
        Repository work tree the command runs in.
    *args
        Git arguments.

    Returns
    -------
    str
        Standard output decoded as UTF-8.

    Raises
    ------
    RangeAuditError
        If git is not installed or the command exits non-zero.
    """
    git = shutil.which("git")
    if git is None:
        raise RangeAuditError("git executable not found")
    completed = subprocess.run([git, *args], cwd=root, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RangeAuditError(detail or f"git {args[0]} exited {completed.returncode}")
    return completed.stdout.decode("utf-8")


def audit_range(rev_range: str, root: Path) -> list[tuple[str, str, list[str]]]:
    """Check every commit message of a revision range.

    Parameters
    ----------
    rev_range
        Any revision range ``git rev-list`` accepts, such as ``A..B``.
    root
        Repository work tree.

    Returns
    -------
    list of (str, str, list[str])
        Abbreviated hash, subject and violations of each violating commit,
        oldest first; empty when every commit passes.

    Raises
    ------
    RangeAuditError
        If the range or any commit cannot be read.
    """
    if rev_range.startswith("-"):
        raise RangeAuditError(f"revision range must not start with '-': {rev_range!r}")
    commits = _git(root, "rev-list", "--reverse", rev_range, "--").split()
    findings: list[tuple[str, str, list[str]]] = []
    for commit in commits:
        message = _git(root, "show", "-s", "--format=%B", commit)
        violations = message_violations(message)
        if violations:
            findings.append((commit[:12], _subject_line(message), violations))
    return findings


def _report_range(rev_range: str, root: Path) -> int:
    """Print a range audit and return its exit status.

    Parameters
    ----------
    rev_range
        Revision range to audit.
    root
        Repository work tree.

    Returns
    -------
    int
        ``0`` when every commit passes, ``1`` when any violates the policy,
        ``2`` when the range cannot be read.
    """
    try:
        findings = audit_range(rev_range, root)
    except RangeAuditError as exc:
        print(f"Range audit failed: {exc}", file=sys.stderr)
        return 2
    if not findings:
        print(f"commit-trailers: PASS {rev_range}")
        return 0
    print(f"commit-trailers: FAIL {rev_range}", file=sys.stderr)
    for commit, subject, violations in findings:
        print(f"  {commit} {subject}", file=sys.stderr)
        for violation in violations:
            print(f"    - {violation}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Run the commit-trailer hook.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when validation passes, ``1`` for policy violations, ``2``
        when an audited range cannot be read.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("message_file", type=Path, nargs="?")
    target.add_argument("--audit-range", metavar="REV_RANGE")
    parser.add_argument("--root", type=Path, default=Path())
    args = parser.parse_args(argv)
    if args.audit_range is not None:
        return _report_range(args.audit_range, args.root)
    violations = message_violations(args.message_file.read_text(encoding="utf-8"))
    if not violations:
        return 0
    print("Commit message rejected:", file=sys.stderr)
    for violation in violations:
        print(f"  - {violation}", file=sys.stderr)
    print("Required block:\n  Seat: <seat-id>", file=sys.stderr)
    print(f"  {REQUIRED_AUTHORSHIP_LINE}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
