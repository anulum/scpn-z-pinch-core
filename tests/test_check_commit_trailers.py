# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — commit trailer verifier tests

"""Contract tests for the commit-message trailer guard."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from check_commit_trailers import (
    REQUIRED_AUTHORSHIP_LINE,
    RangeAuditError,
    audit_range,
    main,
    message_violations,
)

VALID_MESSAGE = (
    "feat: add configuration policy surface\n\nbody text\n\n"
    f"Seat: rs01\n{REQUIRED_AUTHORSHIP_LINE}\n"
)


def test_valid_message_has_no_violations() -> None:
    """A compliant message passes with no findings."""
    assert message_violations(VALID_MESSAGE) == []


@pytest.mark.parametrize(
    ("message", "fragment"),
    [
        ("feat: x\n\nSeat: rs01\n", "missing required authorship line"),
        (
            (
                f"feat: x\n\nSeat: rs01\n{REQUIRED_AUTHORSHIP_LINE}\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "exactly one authorship line",
        ),
        (f"feat: x\n\n{REQUIRED_AUTHORSHIP_LINE}\n", "missing `Seat:"),
        (
            f"feat: x\n\nSeat: a1\nSeat: b2\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "exactly one `Seat:",
        ),
        (f"feat: x\n\nSeat: !bad!\n{REQUIRED_AUTHORSHIP_LINE}\n", "invalid `Seat:"),
        (
            f"feat: x\n\nSeat: claude-1\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "vendor-prefixed",
        ),
        (
            f"feat: x\n\nSeat: rs01\nextra\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "immediately precede",
        ),
        (
            f"feat: x\n\n{REQUIRED_AUTHORSHIP_LINE}\nSeat: rs01\n",
            "immediately precede",
        ),
        (
            (
                f"feat: x\n\nCo-Authored-By: Someone\nSeat: rs01\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "Co-Authored-By",
        ),
        (
            (
                f"feat: comprehensive robust module\n\nSeat: rs01\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "banned public subject term(s): comprehensive, robust",
        ),
    ],
)
def test_violation_is_reported(message: str, fragment: str) -> None:
    """Each policy breach yields a finding naming the failing rule."""
    findings = message_violations(message)
    assert any(fragment in finding for finding in findings), findings


def test_main_accepts_valid_file(tmp_path: Path) -> None:
    """The hook exits 0 for a compliant commit-message file."""
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(VALID_MESSAGE, encoding="utf-8")
    assert main([str(path)]) == 0


def test_main_rejects_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The hook exits 1 and names the violations for a bad message."""
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("feat: x\n", encoding="utf-8")
    assert main([str(path)]) == 1
    err = capsys.readouterr().err
    assert "Commit message rejected" in err
    assert "Seat: <seat-id>" in err


def _git(root: Path, *args: str) -> str:
    """Run one git command in a scratch repository and return stdout."""
    git = shutil.which("git")
    assert git is not None
    completed = subprocess.run(
        [
            git,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.org",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8").strip()


@pytest.fixture
def history(tmp_path: Path) -> Path:
    """Build a throwaway history: valid, missing trailers, valid, vendor seat."""
    _git(tmp_path, "init", "-q", "-b", "main")
    messages = [
        VALID_MESSAGE,
        "fix: old commit without trailers\n",
        VALID_MESSAGE.replace("feat: add", "feat: extend"),
        f"docs: vendor seat\n\nSeat: claude-09bd\n{REQUIRED_AUTHORSHIP_LINE}\n",
    ]
    for index, message in enumerate(messages):
        (tmp_path / "file.txt").write_text(str(index), encoding="utf-8")
        _git(tmp_path, "add", "file.txt")
        _git(tmp_path, "commit", "-q", "-m", message)
    return tmp_path


def test_range_audit_reports_each_violating_commit(history: Path) -> None:
    """Only the violating commits are reported, oldest first, with reasons."""
    findings = audit_range("HEAD~2..HEAD", history)
    assert [subject for _, subject, _ in findings] == ["docs: vendor seat"]
    whole = audit_range("HEAD", history)
    subjects = [subject for _, subject, _ in whole]
    assert subjects == ["fix: old commit without trailers", "docs: vendor seat"]
    assert "missing required authorship line" in whole[0][2]
    assert "vendor-prefixed `Seat:` trailer is forbidden" in whole[1][2]
    assert len(whole[0][0]) == 12


def test_range_audit_passes_a_clean_range(history: Path) -> None:
    """A range of compliant commits has no findings."""
    assert audit_range("HEAD~2..HEAD~1", history) == []


def test_range_audit_is_read_only(history: Path) -> None:
    """The audit leaves every ref and the work tree unchanged."""
    before = _git(history, "for-each-ref")
    status = _git(history, "status", "--porcelain")
    audit_range("HEAD", history)
    assert _git(history, "for-each-ref") == before
    assert _git(history, "status", "--porcelain") == status


def test_cli_range_exit_codes(
    history: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI returns 0 for a clean range, 1 for violations, 2 for bad refs."""
    root = ["--root", str(history)]
    assert main(["--audit-range", "HEAD~2..HEAD~1", *root]) == 0
    assert "commit-trailers: PASS" in capsys.readouterr().out
    assert main(["--audit-range", "HEAD", *root]) == 1
    error = capsys.readouterr().err
    assert "commit-trailers: FAIL HEAD" in error
    assert "fix: old commit without trailers" in error
    assert main(["--audit-range", "no-such-ref..HEAD", *root]) == 2
    assert "Range audit failed" in capsys.readouterr().err


def test_option_like_range_is_refused(history: Path) -> None:
    """A range that git would read as an option never reaches git."""
    with pytest.raises(RangeAuditError, match="must not start with"):
        audit_range("--output=/tmp/x", history)


def test_range_audit_fails_closed_without_git(
    history: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a git executable the audit is an error, never a pass."""
    monkeypatch.setenv("PATH", str(history / "no-bin"))
    with pytest.raises(RangeAuditError, match="git executable not found"):
        audit_range("HEAD", history)


def test_message_file_and_range_are_exclusive(tmp_path: Path) -> None:
    """Exactly one of a message file and a range is accepted."""
    path = tmp_path / "MSG"
    path.write_text(VALID_MESSAGE, encoding="utf-8")
    with pytest.raises(SystemExit):
        main([str(path), "--audit-range", "HEAD"])
    with pytest.raises(SystemExit):
        main([])
