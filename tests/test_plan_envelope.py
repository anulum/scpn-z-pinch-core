# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — portable diagnostic-plan envelope tests

"""Every branch of the plan envelope, its verifier, and its parsers.

The committed fixture is the immutable pilot exchange document: its
byte hash is pinned here, and every tamper path must fail closed. All
content is synthetic; nothing describes an observation or a control
proposal.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    ObservabilityBinding,
    plan_from_record,
)
from scpn_z_pinch_core.plan_envelope import (
    ENVELOPE_SCHEMA,
    ENVELOPE_SCHEMA_VERSION,
    NON_CLAIMS,
    PROJECT,
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

FIXTURE = Path(__file__).parent / "data" / "plan_envelope_fixture.json"
FIXTURE_SHA256 = "b7f93462fa224ec2a012b4275065393e03ff63060b1d1c64318dedbe81639267"


def fixture_document() -> dict[str, Any]:
    """Load the committed fixture document."""
    document = json.loads(FIXTURE.read_bytes().decode("utf-8"))
    assert isinstance(document, dict)
    return document


def fixture_envelope() -> PlanEnvelope:
    """Load the envelope half of the committed fixture."""
    return envelope_from_record(fixture_document()["envelope"])


def test_fixture_is_immutable_and_verifies() -> None:
    """The committed fixture matches its pinned hash and verifies."""
    data = FIXTURE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FIXTURE_SHA256
    document = fixture_document()
    plan = plan_from_record(document["plan"])
    envelope = envelope_from_record(document["envelope"])
    verify_envelope(envelope, plan)
    assert envelope.plan_sha256 == plan.digest_sha256()


def test_builder_matches_fixture_envelope() -> None:
    """Rebuilding the envelope from the plan reproduces the fixture."""
    document = fixture_document()
    plan = plan_from_record(document["plan"])
    envelope = envelope_from_record(document["envelope"])
    assert (
        envelope_for_plan(plan, envelope.producer_revision, envelope.manifest_sha256)
        == envelope
    )


def test_round_trip_preserves_digest() -> None:
    """Record and byte round-trips preserve the canonical digest."""
    envelope = fixture_envelope()
    rebuilt = envelope_from_record(envelope.to_record())
    assert rebuilt == envelope
    assert envelope_from_bytes(envelope.canonical_bytes()) == envelope
    assert rebuilt.digest_sha256() == envelope.digest_sha256()


def test_canonical_bytes_are_sorted_and_terminated() -> None:
    """Canonical bytes use sorted keys and end with a newline."""
    data = fixture_envelope().canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data.decode("utf-8"))
    assert list(decoded) == sorted(decoded)


def test_verify_rejects_tampered_plan_content() -> None:
    """Any change to the plan bytes breaks the pinned digest."""
    document = fixture_document()
    envelope = envelope_from_record(document["envelope"])
    tampered = document["plan"]
    tampered["channels"][0]["evidence_bindings"]["provenance"] = "tampered"
    plan = plan_from_record(tampered)
    with pytest.raises(DiagnosticPlanError, match="plan bytes hash"):
        verify_envelope(envelope, plan)


def test_verify_rejects_foreign_plan_identifier() -> None:
    """An envelope for one plan refuses another plan's identifier."""
    document = fixture_document()
    envelope = envelope_from_record(document["envelope"])
    renamed = document["plan"]
    renamed["identifier"] = "another_plan"
    plan = plan_from_record(renamed)
    with pytest.raises(DiagnosticPlanError, match="envelope names"):
        verify_envelope(envelope, plan)


def test_builder_rejects_empty_revision() -> None:
    """An empty producer revision is rejected."""
    document = fixture_document()
    plan = plan_from_record(document["plan"])
    with pytest.raises(DiagnosticPlanError, match="producer_revision"):
        envelope_for_plan(plan, "", "0" * 64)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("schema", "scpn.other.v1", r"envelope\.schema"),
        ("schema_version", "9.9.9", "schema_version"),
        ("schema_version", "1.0.0", "schema_version"),
        ("schema_version", "1.1.0", "schema_version"),
        ("project", "SCPN-OTHER-CORE", r"envelope\.project"),
        ("configurations", ("conventional_tokamak",), "owned set"),
        ("capability", "device_configuration_model", r"envelope\.capability"),
        ("evidence_maturity", "benchmark_validated", "evidence_maturity"),
        ("synthetic", False, "synthetic"),
        ("authority", "supervisory", "review_only"),
        ("actionable", True, "never actionable"),
        ("plan_identifier", "Bad-Id", "plan_identifier"),
        ("plan_sha256", "XYZ", "plan_sha256"),
        ("manifest_sha256", "XYZ", "manifest_sha256"),
        ("producer_revision", "", "producer_revision"),
        ("non_claims", ("no control action is proposed or authorised",), "non_claims"),
    ],
)
def test_envelope_rejects_contract_violations(
    field: str, value: Any, match: str
) -> None:
    """Every hard envelope invariant fails closed."""
    envelope = fixture_envelope()
    with pytest.raises(DiagnosticPlanError, match=match):
        dataclasses.replace(envelope, **{field: value})


def test_envelope_rejects_foreign_binding() -> None:
    """A binding to any other registry release is rejected."""
    envelope = fixture_envelope()
    foreign = ObservabilityBinding(
        catalogue_version="9.9.9",
        catalogue_digest_sha256="0" * 64,
        reactor_registry_version="1.0.0",
        reactor_registry_digest_sha256="0" * 64,
    )
    with pytest.raises(DiagnosticPlanError, match=r"envelope\.binding"):
        dataclasses.replace(envelope, binding=foreign)


def test_parser_rejects_non_object_record() -> None:
    """A non-object record is rejected."""
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        envelope_from_record([1, 2])


def test_parser_rejects_unknown_fields() -> None:
    """Unknown envelope fields are rejected."""
    record = fixture_envelope().to_record()
    record["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown fields"):
        envelope_from_record(record)


def test_parser_rejects_non_mapping_binding() -> None:
    """A non-object binding is rejected."""
    record = fixture_envelope().to_record()
    record["binding"] = 3
    with pytest.raises(DiagnosticPlanError, match="binding: must be an object"):
        envelope_from_record(record)


def test_parser_rejects_non_string_field() -> None:
    """A non-string field is rejected."""
    record = fixture_envelope().to_record()
    record["project"] = 7
    with pytest.raises(DiagnosticPlanError, match="must be a string"):
        envelope_from_record(record)


def test_parser_rejects_non_boolean_flag() -> None:
    """A non-boolean flag is rejected."""
    record = fixture_envelope().to_record()
    record["synthetic"] = "yes"
    with pytest.raises(DiagnosticPlanError, match="must be a boolean"):
        envelope_from_record(record)


def test_parser_rejects_non_array_configurations() -> None:
    """A non-array configurations field is rejected."""
    record = fixture_envelope().to_record()
    record["configurations"] = "conventional_tokamak"
    with pytest.raises(DiagnosticPlanError, match="must be an array"):
        envelope_from_record(record)


def test_parser_rejects_non_string_configuration_entry() -> None:
    """A non-string configurations entry is rejected."""
    record = fixture_envelope().to_record()
    record["configurations"] = [1]
    with pytest.raises(DiagnosticPlanError, match="entries must be strings"):
        envelope_from_record(record)


def test_bytes_parser_rejects_duplicate_members() -> None:
    """A duplicate JSON member is rejected."""
    data = fixture_envelope().canonical_bytes()
    text = data.decode("utf-8").rstrip("\n")
    tampered = text[:-1] + ',"actionable":false}\n'
    with pytest.raises(DiagnosticPlanError, match="duplicate member"):
        envelope_from_bytes(tampered.encode("utf-8"))


def test_bytes_parser_rejects_nan_literal() -> None:
    """A NaN literal in the document is rejected."""
    data = fixture_envelope().canonical_bytes()
    tampered = data.decode("utf-8").replace('"synthetic":true', '"synthetic":NaN')
    with pytest.raises(DiagnosticPlanError, match="non-finite"):
        envelope_from_bytes(tampered.encode("utf-8"))


def test_bytes_parser_rejects_invalid_json() -> None:
    """A malformed document is rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        envelope_from_bytes(b"{")


def test_bytes_parser_rejects_invalid_utf8() -> None:
    """Non-UTF-8 bytes are rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        envelope_from_bytes(b"\xff\xfe")


def test_constants_are_the_published_contract() -> None:
    """The public constants state the exchanged contract exactly."""
    assert ENVELOPE_SCHEMA == "scpn.reactor-diagnostic-plan-envelope.v1"
    assert ENVELOPE_SCHEMA_VERSION == "1.2.0"
    assert PROJECT == "SCPN-Z-PINCH-CORE"
    assert NON_CLAIMS == (
        "no control action is proposed or authorised",
        "no physical observation is described or claimed",
    )


def test_manifest_digest_matches_committed_manifest() -> None:
    """The envelope pins the committed canonical manifest bytes."""
    manifest = Path(__file__).parents[1] / "reactor-domain.json"
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert fixture_envelope().manifest_sha256 == digest


def test_parser_rejects_unknown_binding_members() -> None:
    """Unknown members inside the binding are rejected."""
    record = fixture_envelope().to_record()
    record["binding"]["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown members"):
        envelope_from_record(record)


def test_bytes_parser_rejects_non_canonical_document() -> None:
    """A valid but non-canonical byte form is rejected."""
    record = fixture_envelope().to_record()
    pretty = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(DiagnosticPlanError, match="non-canonical"):
        envelope_from_bytes(pretty)
