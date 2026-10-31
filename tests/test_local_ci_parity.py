# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — local and hosted gate parity tests

"""Local entry points run every hosted gate command with the same scope.

The hosted static-policy and test workflows are the reference cohort. The
``make`` targets and the preflight gate plan must each carry every one of
those commands with identical arguments, so a contributor who runs the
local sequence checks exactly the source roots CI checks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from preflight import build_gate_plan

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github" / "workflows"
CI_WORKFLOWS = ("reusable-static-policy.yml", "reusable-tests.yml")
LOCAL_TARGETS = ("lint", "typecheck", "test", "validate")
GATE_TOOLS = frozenset({"ruff", "mypy", "pytest", "python"})


def ci_gate_commands(workflow_texts: list[str]) -> set[str]:
    """Collect the gate commands that hosted workflows run.

    Parameters
    ----------
    workflow_texts
        YAML text of each reference workflow.

    Returns
    -------
    set[str]
        Single-line ``run`` commands whose program is a gate tool; package
        installation steps are excluded.
    """
    commands: set[str] = set()
    for text in workflow_texts:
        parsed: dict[str, Any] = yaml.safe_load(text)
        for job in parsed["jobs"].values():
            for step in job.get("steps", []):
                run = step.get("run")
                if not isinstance(run, str) or "\n" in run.strip():
                    continue
                words = run.split()
                if words[0] in GATE_TOOLS and "pip" not in words:
                    commands.add(" ".join(words))
    return commands


def make_target_commands(makefile_text: str, targets: tuple[str, ...]) -> set[str]:
    """Collect the recipe commands of selected ``make`` targets.

    Parameters
    ----------
    makefile_text
        Makefile source.
    targets
        Target names whose recipes are collected.

    Returns
    -------
    set[str]
        Recipe lines with the virtual-environment prefixes removed, so they
        compare directly with the hosted commands.
    """
    commands: set[str] = set()
    current: str | None = None
    for line in makefile_text.splitlines():
        if line and not line.startswith(("\t", "#", " ")) and ":" in line:
            current = line.split(":", 1)[0].strip()
            continue
        if current in targets and line.startswith("\t"):
            recipe = line.strip()
            recipe = recipe.replace("$(PYTHON)", "python").replace("$(VENV)/", "")
            commands.add(" ".join(recipe.split()))
    return commands


def preflight_commands(root: Path) -> set[str]:
    """Collect the preflight gate commands in hosted spelling.

    Parameters
    ----------
    root
        Repository root the plan is built for.

    Returns
    -------
    set[str]
        Command vectors joined with spaces, with the virtual-environment
        binary directory removed; the internal docs gate is skipped.
    """
    prefix = str(root / ".venv" / "bin") + "/"
    commands: set[str] = set()
    for _name, argv in build_gate_plan(root):
        if argv is None:
            continue
        words = [word.removeprefix(prefix) for word in argv]
        commands.add(" ".join(words))
    return commands


FULL_SUITE_PREFIX = "pytest -q --cov="


def uncovered(reference: set[str], local: set[str]) -> set[str]:
    """Return the hosted commands no local command runs.

    Parameters
    ----------
    reference
        Hosted gate commands.
    local
        Commands of a local entry point.

    Returns
    -------
    set[str]
        Hosted commands missing locally. A hosted ``pytest -q`` run of named
        test files is covered when the local entry point runs the whole
        suite with coverage, because that run includes those files.
    """
    full_suite = any(command.startswith(FULL_SUITE_PREFIX) for command in local)
    return {
        command
        for command in reference - local
        if not (full_suite and command.startswith("pytest -q tests/"))
    }


def _ci_reference() -> set[str]:
    """Return the hosted reference cohort of this repository."""
    texts = [(WORKFLOWS / name).read_text(encoding="utf-8") for name in CI_WORKFLOWS]
    return ci_gate_commands(texts)


def test_reference_cohort_covers_every_source_root() -> None:
    """The hosted cohort types every Python root and measures src and tools."""
    reference = _ci_reference()
    assert "mypy --strict src tools tests benchmarks conftest.py" in reference
    assert (
        "pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100" in reference
    )
    assert "python tools/audit_workflows.py" in reference


def test_make_targets_run_every_hosted_gate() -> None:
    """``make lint typecheck test validate`` runs the whole hosted cohort."""
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    missing = uncovered(_ci_reference(), make_target_commands(makefile, LOCAL_TARGETS))
    assert not missing, sorted(missing)


def test_preflight_runs_every_hosted_gate() -> None:
    """The preflight plan runs the whole hosted cohort."""
    plan = {command.split(" --map ", 1)[0] for command in preflight_commands(REPO)}
    missing = uncovered(_ci_reference(), plan)
    assert not missing, sorted(missing)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            "mypy --strict src tools tests benchmarks conftest.py",
            "mypy --strict tools tests",
        ),
        ("--cov=src --cov=tools", "--cov=tools"),
        ("\t$(PYTHON) tools/audit_workflows.py\n", ""),
    ],
    ids=["typecheck-without-src", "coverage-without-src", "validate-without-audit"],
)
def test_narrowed_make_target_is_detected(before: str, after: str) -> None:
    """A Makefile that drops any root or gate fails the parity comparison."""
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    assert before in makefile
    narrowed = makefile.replace(before, after)
    missing = uncovered(_ci_reference(), make_target_commands(narrowed, LOCAL_TARGETS))
    assert missing


def test_multiline_and_install_steps_are_not_gates() -> None:
    """Install steps and multi-line scripts are outside the gate cohort."""
    text = (
        "jobs:\n"
        "  run:\n"
        "    steps:\n"
        "      - run: python -m pip install --no-deps -e .\n"
        "      - run: |\n"
        "          echo one\n"
        "          echo two\n"
        "      - uses: actions/checkout@" + "0" * 40 + "\n"
        "      - run: ruff check .\n"
    )
    assert ci_gate_commands([text]) == {"ruff check ."}


def test_named_test_files_are_covered_only_by_the_full_suite() -> None:
    """A targeted hosted run is covered by a local full run, not otherwise."""
    reference = {"pytest -q tests/test_x.py", "ruff check ."}
    full = "pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100"
    assert uncovered(reference, {full, "ruff check ."}) == set()
    assert uncovered(reference, {"ruff check ."}) == {"pytest -q tests/test_x.py"}


def hook_stage_findings(config_text: str) -> list[str]:
    """Report hooks that would run at an unintended stage.

    Parameters
    ----------
    config_text
        ``.pre-commit-config.yaml`` source.

    Returns
    -------
    list[str]
        Findings when hooks without their own stage list are not limited to
        pre-commit and pre-push, or when any hook other than the trailer
        guard runs at commit-msg.
    """
    config: dict[str, Any] = yaml.safe_load(config_text)
    findings: list[str] = []
    if config.get("default_stages") != ["pre-commit", "pre-push"]:
        findings.append(f"default_stages: {config.get('default_stages')!r}")
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            stages = hook.get("stages", config.get("default_stages"))
            if stages and "commit-msg" in stages and hook["id"] != "commit-trailers":
                findings.append(f"{hook['id']}: runs at commit-msg")
    return findings


def test_hooks_run_once_at_their_intended_stage() -> None:
    """Only the trailer guard runs at commit-msg; the rest before commit/push."""
    text = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert hook_stage_findings(text) == []


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (
            "default_stages: [pre-commit, pre-push]\n",
            "",
            "default_stages: None",
        ),
        (
            "        stages: [pre-push]\n",
            "        stages: [pre-push, commit-msg]\n",
            "preflight-pre-push: runs at commit-msg",
        ),
    ],
    ids=["no-default-stages", "extra-commit-msg-stage"],
)
def test_unintended_hook_stage_is_detected(
    before: str, after: str, expected: str
) -> None:
    """Dropping the default or adding commit-msg to a hook is a finding."""
    text = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert before in text
    assert expected in hook_stage_findings(text.replace(before, after, 1))
