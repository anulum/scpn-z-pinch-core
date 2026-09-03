# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — bytes diagnostic tests

"""The canonical byte form and the record and byte parsers.

The parsers are fail-closed: an unknown field, a boolean where a number
belongs, a non-canonical document or invalid UTF-8 is refused rather than
coerced. Round trips preserve the digest.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    channel_derived,
    channel_event_train,
    clock_facility,
    clock_shot,
    synthetic_plan,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    CATALOGUE_BINDING,
    DeferredCandidate,
    DiagnosticPlan,
    plan_from_bytes,
    plan_from_record,
)


def test_record_round_trips_signals_transformations_and_topology() -> None:
    """The record carries the depth sections and parses back exactly."""
    record = synthetic_plan().to_record()
    assert any(
        signal["role"] == "carrier" for signal in record["channels"][0]["signals"]
    )
    assert record["clock_topology"]["reference_domain_identifier"] == "dom_facility"
    assert plan_from_record(record) == synthetic_plan()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda r: r["channels"][0].__setitem__("signals", {}), "must be an array"),
        (lambda r: r["channels"][0]["signals"].__setitem__(0, 1), "must be an object"),
        (
            lambda r: r["channels"][0]["signals"][0].__setitem__("zz", 1),
            "unknown members",
        ),
        (
            lambda r: r["channels"][0]["signals"][0].__setitem__("role", "lead"),
            "is not one of",
        ),
        (lambda r: r.__setitem__("frame_transformations", {}), "must be an array"),
        (lambda r: r["frame_transformations"].append(1), "must be an object"),
        (lambda r: r["frame_transformations"].append({"zz": 1}), "unknown members"),
        (lambda r: r.__setitem__("clock_topology", []), "must be an object"),
        (lambda r: r["clock_topology"].__setitem__("zz", 1), "unknown members"),
        (lambda r: r["clock_topology"].__setitem__("domains", {}), "must be an array"),
        (
            lambda r: r["clock_topology"]["domains"].__setitem__(0, 1),
            "must be an object",
        ),
        (
            lambda r: r["clock_topology"]["domains"][0].__setitem__("zz", 1),
            "unknown members",
        ),
        (
            lambda r: r["clock_topology"]["domains"][0].__setitem__(
                "member_clock_identifiers", "x"
            ),
            "must be an array",
        ),
        (
            lambda r: r["clock_topology"]["domains"][0].__setitem__(
                "member_clock_identifiers", [1]
            ),
            "entries must be strings",
        ),
    ],
)
def test_parser_rejects_malformed_depth_sections(mutate: Any, message: str) -> None:
    """Every depth section is parsed with exact keys and strict types."""
    record = synthetic_plan().to_record()
    mutate(record)
    with pytest.raises(DiagnosticPlanError, match=message):
        plan_from_record(record)


def test_parser_rejects_pre_depth_record_shape() -> None:
    """A record without the depth sections is refused, fail closed."""
    record = synthetic_plan().to_record()
    del record["frame_transformations"]
    del record["clock_topology"]
    with pytest.raises(DiagnosticPlanError, match="must be an array"):
        plan_from_record(record)
    record = synthetic_plan().to_record()
    for channel in record["channels"]:
        del channel["signals"]
    with pytest.raises(DiagnosticPlanError, match="must be an array"):
        plan_from_record(record)


def test_parser_builds_then_refuses_a_well_formed_transformation() -> None:
    """A well-formed transformation entry parses and is then refused by the plan."""
    record = synthetic_plan().to_record()
    record["frame_transformations"].append(
        {
            "source_identifier": "frm_pinch_axis",
            "target_identifier": "frm_zz_extra",
            "kind": "rigid",
            "equilibrium_dependent": False,
            "method": "synthetic declaration",
            "evidence_claimed": False,
        }
    )
    with pytest.raises(DiagnosticPlanError, match="no admissible transformation"):
        plan_from_record(record)


def test_round_trip_preserves_deferrals() -> None:
    """A plan with an explicit deferral survives the record round-trip."""
    plan = DiagnosticPlan(
        identifier="z_pinch_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(channel_event_train(), channel_derived()),
        deferrals=(
            DeferredCandidate(
                candidate_id="model.synthetic_oscillator_coordinate",
                reason="synthetic oscillator adds no exercised content here",
            ),
        ),
    )
    assert plan_from_record(plan.to_record()) == plan


def test_round_trip_preserves_digest() -> None:
    """Record and byte round-trips preserve the canonical digest."""
    plan = synthetic_plan()
    rebuilt = plan_from_record(plan.to_record())
    assert rebuilt == plan
    assert plan_from_bytes(plan.canonical_bytes()) == plan
    assert rebuilt.digest_sha256() == plan.digest_sha256()


def test_canonical_bytes_are_sorted_and_terminated() -> None:
    """Canonical bytes use sorted keys and end with a newline."""
    data = synthetic_plan().canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data.decode("utf-8"))
    assert list(decoded) == sorted(decoded)
    digest = hashlib.sha256(data).hexdigest()
    assert synthetic_plan().digest_sha256() == digest


def test_parser_rejects_non_object_record() -> None:
    """A non-object record is rejected."""
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record([1, 2])


def test_parser_rejects_unknown_fields() -> None:
    """Unknown top-level fields are rejected."""
    record = synthetic_plan().to_record()
    record["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown fields"):
        plan_from_record(record)


def test_parser_rejects_non_mapping_binding() -> None:
    """A non-object binding is rejected."""
    record = synthetic_plan().to_record()
    record["binding"] = 3
    with pytest.raises(DiagnosticPlanError, match="binding: must be an object"):
        plan_from_record(record)


@pytest.mark.parametrize(
    "field", ["clocks", "channels", "deferrals", "frames", "clock_relations"]
)
def test_parser_rejects_non_list_sections(field: str) -> None:
    """Every plan section must be an array."""
    record = synthetic_plan().to_record()
    record[field] = {}
    with pytest.raises(DiagnosticPlanError, match=f"{field}: must be an array"):
        plan_from_record(record)


@pytest.mark.parametrize(
    "field", ["clocks", "channels", "deferrals", "frames", "clock_relations"]
)
def test_parser_rejects_non_object_entries(field: str) -> None:
    """Every section entry must be an object."""
    record = synthetic_plan().to_record()
    record[field] = [1]
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record(record)


def test_parser_rejects_boolean_number() -> None:
    """Booleans are rejected where numbers are required."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["resolution_s"] = True
    with pytest.raises(DiagnosticPlanError, match="must be a number"):
        plan_from_record(record)


def test_parser_rejects_boolean_optional_number() -> None:
    """Booleans are rejected where nullable numbers are required."""
    record = synthetic_plan().to_record()
    record["channels"][0]["timing_uncertainty_s"] = True
    with pytest.raises(DiagnosticPlanError, match="number or null"):
        plan_from_record(record)


def test_parser_accepts_integer_numbers() -> None:
    """Plain integers satisfy numeric fields."""
    record = synthetic_plan().to_record()
    record["channels"][2]["sample_rate_hz"] = 1000
    assert plan_from_record(record).channels[2].sample_rate_hz == 1000.0


def test_parser_rejects_non_boolean_flag() -> None:
    """A non-boolean synthetic flag is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["synthetic"] = "yes"
    with pytest.raises(DiagnosticPlanError, match="must be a boolean"):
        plan_from_record(record)


def test_parser_rejects_non_string_field() -> None:
    """A non-string identifier is rejected."""
    record = synthetic_plan().to_record()
    record["identifier"] = 7
    with pytest.raises(DiagnosticPlanError, match="must be a string"):
        plan_from_record(record)


def test_parser_rejects_unknown_enum_value() -> None:
    """A value outside the enum vocabulary is rejected."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["kind"] = "sundial"
    with pytest.raises(DiagnosticPlanError, match="is not one of"):
        plan_from_record(record)


def test_parser_rejects_non_string_evidence_value() -> None:
    """A non-string evidence statement is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["evidence_bindings"]["provenance"] = 5
    with pytest.raises(DiagnosticPlanError, match="evidence_bindings"):
        plan_from_record(record)


def test_bytes_parser_rejects_nan_literal() -> None:
    """A NaN literal in the document is rejected."""
    record = synthetic_plan().to_record()
    text = json.dumps(record).replace("5e-09", "NaN")
    with pytest.raises(DiagnosticPlanError, match="non-finite"):
        plan_from_bytes(text.encode("utf-8"))


def test_bytes_parser_rejects_invalid_json() -> None:
    """A malformed document is rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"{")


def test_bytes_parser_rejects_invalid_utf8() -> None:
    """Non-UTF-8 bytes are rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"\xff\xfe")


@pytest.mark.parametrize("section", ["clocks", "channels", "frames", "clock_relations"])
def test_parser_rejects_unknown_entry_members(section: str) -> None:
    """Unknown members inside nested entries are rejected."""
    record = synthetic_plan().to_record()
    record[section][0]["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown members"):
        plan_from_record(record)


def test_parser_rejects_unknown_deferral_members() -> None:
    """Unknown members inside a deferral entry are rejected."""
    record = synthetic_plan().to_record()
    record["deferrals"] = [{"candidate_id": "x", "reason": "y", "z": 1}]
    with pytest.raises(DiagnosticPlanError, match="unknown members"):
        plan_from_record(record)


def test_bytes_parser_rejects_duplicate_members() -> None:
    """A duplicate JSON member is rejected."""
    data = synthetic_plan().canonical_bytes()
    text = data.decode("utf-8").rstrip("\n")
    tampered = text[:-1] + ',"identifier":"x"}\n'
    with pytest.raises(DiagnosticPlanError, match="duplicate member"):
        plan_from_bytes(tampered.encode("utf-8"))


def test_bytes_parser_rejects_non_canonical_document() -> None:
    """A valid but non-canonical byte form is rejected."""
    record = synthetic_plan().to_record()
    pretty = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(DiagnosticPlanError, match="non-canonical"):
        plan_from_bytes(pretty)


def test_parser_rejects_non_integer_element_count() -> None:
    """A non-integer element count is rejected by the parser."""
    record = synthetic_plan().to_record()
    record["channels"][0]["element_count"] = "many"
    with pytest.raises(DiagnosticPlanError, match="must be an integer"):
        plan_from_record(record)


def test_parser_rejects_pre_deepening_record_shape() -> None:
    """A record without the deepened sections is refused, fail closed."""
    record = synthetic_plan().to_record()
    del record["frames"]
    del record["clock_relations"]
    with pytest.raises(DiagnosticPlanError, match="must be an array"):
        plan_from_record(record)
