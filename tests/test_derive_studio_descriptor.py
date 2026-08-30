# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Studio descriptor derivation tests

"""Contract tests for the deterministic Studio descriptor derivation."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from derive_studio_descriptor import derive_descriptor, main
from manifest_io import sha256_of_file

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "reactor-domain.json"


def test_descriptor_projects_identity_without_authority() -> None:
    """The derivation copies identity and grants no executable authority."""
    descriptor = derive_descriptor(MANIFEST)
    assert descriptor["schema"] == "scpn.studio-portfolio-descriptor.v1"
    assert descriptor["project"] == "SCPN-Z-PINCH-CORE"
    assert descriptor["configurations"] == [
        "sheared_flow_z_pinch",
        "z_pinch",
    ]
    assert descriptor["capabilities"] == []
    assert descriptor["lifecycle"]["state"] == "not_federated"
    assert descriptor["schema_version"] == "1.1.0"
    assert descriptor["source"]["repository"] == descriptor["project"]
    assert descriptor["lifecycle"]["evidence_pointer"] is None
    authority = descriptor["authority"]
    assert authority["allowed_action_authority"] == "none"
    assert authority["spo_actionable"] is False
    assert authority["control_intent_contract"] is None
    assert descriptor["machine_protection"] == {
        "availability": "not_assessed",
        "final_veto_owner": "independent_machine_protection",
    }
    assert descriptor["source"]["manifest_sha256"] == sha256_of_file(MANIFEST)


def test_committed_descriptor_is_in_sync(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The committed descriptor matches a fresh derivation byte for byte."""
    monkeypatch.chdir(REPO)
    assert main(["--check"]) == 0
    assert "PASS in sync" in capsys.readouterr().out


def test_write_then_check_round_trip(tmp_path: Path) -> None:
    """A written descriptor immediately passes its own drift check."""
    manifest = tmp_path / "reactor-domain.json"
    shutil.copyfile(MANIFEST, manifest)
    descriptor = tmp_path / "studio" / "portfolio-descriptor.json"
    write_argv = [
        "--manifest",
        str(manifest),
        "--descriptor",
        str(descriptor),
    ]
    assert main([*write_argv, "--write"]) == 0
    assert descriptor.is_file()
    assert main([*write_argv, "--check"]) == 0


def test_manual_edit_is_reported_as_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Any manual descriptor edit fails the drift check."""
    manifest = tmp_path / "reactor-domain.json"
    shutil.copyfile(MANIFEST, manifest)
    descriptor = tmp_path / "portfolio-descriptor.json"
    argv = ["--manifest", str(manifest), "--descriptor", str(descriptor)]
    assert main([*argv, "--write"]) == 0
    descriptor.write_bytes(descriptor.read_bytes() + b" ")
    assert main([*argv, "--check"]) == 1
    assert "FAIL drift" in capsys.readouterr().out


def test_missing_descriptor_fails_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An absent committed descriptor is a failure, not a skip."""
    argv = [
        "--manifest",
        str(MANIFEST),
        "--descriptor",
        str(tmp_path / "absent.json"),
        "--check",
    ]
    assert main(argv) == 1
    assert "cannot read committed descriptor" in capsys.readouterr().out


def test_unreadable_manifest_fails_derivation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing manifest fails the derivation itself."""
    argv = [
        "--manifest",
        str(tmp_path / "absent.json"),
        "--descriptor",
        str(tmp_path / "out.json"),
        "--check",
    ]
    assert main(argv) == 1
    assert "studio-descriptor: FAIL" in capsys.readouterr().out


def test_mode_flag_is_required() -> None:
    """Exactly one of ``--check`` or ``--write`` must be given."""
    with pytest.raises(SystemExit):
        main(["--manifest", str(MANIFEST)])
