# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — diagnostic plan record parsing

"""Strict parsing of diagnostic-plan records and canonical bytes.

:func:`plan_from_record` rebuilds a :class:`DiagnosticPlan` from a JSON
record with exact member sets at every level; :func:`plan_from_bytes`
accepts only canonical UTF-8 JSON and refuses duplicate members,
non-finite literals, nesting deeper than the decoder can follow and any
non-canonical byte form, always with :class:`DiagnosticPlanError`.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Final

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.binding import (
    ObservabilityBinding,
)
from scpn_z_pinch_core.observability.clocks import (
    ClockDomain,
    ClockModel,
    ClockRelation,
    ClockTopology,
)
from scpn_z_pinch_core.observability.frames import (
    FrameTransformation,
    ReferenceFrame,
)
from scpn_z_pinch_core.observability.plan import (
    DiagnosticPlan,
)
from scpn_z_pinch_core.observability.signals import (
    DeferredCandidate,
    DiagnosticChannelPlan,
    SignalDeclaration,
)
from scpn_z_pinch_core.observability.vocabulary import (
    ClockKind,
    FrameKind,
    SemanticCarrier,
    SignalRole,
    TransformationKind,
)


def _require_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """Return one required mapping field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a mapping.

    Returns
    -------
    dict[str, Any]
        The nested mapping.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a mapping.
    """
    value = record.get(field)
    if not isinstance(value, dict):
        raise DiagnosticPlanError(f"{field}: must be an object")
    return value


def _require_list(record: dict[str, Any], field: str) -> list[Any]:
    """Return one required list field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a list.

    Returns
    -------
    list[Any]
        The nested list.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a list.
    """
    value = record.get(field)
    if not isinstance(value, list):
        raise DiagnosticPlanError(f"{field}: must be an array")
    return value


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number.

    Returns
    -------
    float
        The numeric value; booleans are rejected.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a real number.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DiagnosticPlanError(f"{field}: must be a number, got {value!r}")
    return float(value)


def _optional_number(record: dict[str, Any], field: str) -> float | None:
    """Return one nullable real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number or ``None``.

    Returns
    -------
    float or None
        The numeric value, or ``None``; booleans are rejected.

    Raises
    ------
    DiagnosticPlanError
        If the field holds anything else.
    """
    value = record.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DiagnosticPlanError(f"{field}: must be a number or null, got {value!r}")
    return float(value)


def _boolean(record: dict[str, Any], field: str) -> bool:
    """Return one required boolean field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a boolean.

    Returns
    -------
    bool
        The boolean value.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a boolean.
    """
    value = record.get(field)
    if not isinstance(value, bool):
        raise DiagnosticPlanError(f"{field}: must be a boolean, got {value!r}")
    return value


def _string(record: dict[str, Any], field: str) -> str:
    """Return one required string field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a string.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DiagnosticPlanError(f"{field}: must be a string, got {value!r}")
    return value


def _enum_value[E: StrEnum](
    record: dict[str, Any], field: str, enum_type: type[E]
) -> E:
    """Return one required enum-valued field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold one of the enum values.
    enum_type
        Enum the value must belong to.

    Returns
    -------
    E
        The enum member.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a member value.
    """
    value = _string(record, field)
    try:
        return enum_type(value)
    except ValueError as exc:
        raise DiagnosticPlanError(
            f"{field}: {value!r} is not one of "
            f"{sorted(member.value for member in enum_type)!r}"
        ) from exc


def _evidence_bindings(record: dict[str, Any]) -> dict[str, str]:
    """Return the evidence-binding mapping of a channel record.

    Parameters
    ----------
    record
        Channel record under inspection.

    Returns
    -------
    dict[str, str]
        Slot-to-statement mapping with string keys and values.

    Raises
    ------
    DiagnosticPlanError
        If the mapping shape is violated.
    """
    bindings = _require_mapping(record, "evidence_bindings")
    result: dict[str, str] = {}
    for slot, statement in bindings.items():
        if not isinstance(statement, str):
            raise DiagnosticPlanError(
                f"evidence_bindings[{slot!r}]: must be a string, got {statement!r}"
            )
        result[slot] = statement
    return result


def _string_tuple(record: dict[str, Any], field: str) -> tuple[str, ...]:
    """Return one required string-array field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold an array of strings.

    Returns
    -------
    tuple of str
        The array entries.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing, not an array, or holds non-strings.
    """
    value = record.get(field)
    if not isinstance(value, list):
        raise DiagnosticPlanError(f"{field}: must be an array")
    for entry in value:
        if not isinstance(entry, str):
            raise DiagnosticPlanError(
                f"{field}: entries must be strings, got {entry!r}"
            )
    return tuple(value)


def _signals(record: dict[str, Any]) -> tuple[SignalDeclaration, ...]:
    """Return the signal inventory of a channel record.

    Parameters
    ----------
    record
        Channel record under inspection.

    Returns
    -------
    tuple of SignalDeclaration
        Declared signals in document order.

    Raises
    ------
    DiagnosticPlanError
        If the inventory shape is violated.
    """
    signals = []
    for entry in _require_list(record, "signals"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("signals[]: must be an object")
        _exact_entry_keys(entry, _SIGNAL_KEYS, "signals[]")
        signals.append(
            SignalDeclaration(
                identifier=_string(entry, "identifier"),
                quantity=_string(entry, "quantity"),
                unit=_string(entry, "unit"),
                role=_enum_value(entry, "role", SignalRole),
                description=_string(entry, "description"),
            )
        )
    return tuple(signals)


def _integer(record: dict[str, Any], field: str) -> int:
    """Return one required integer field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold an integer.

    Returns
    -------
    int
        The integer value; booleans are rejected.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not an integer.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DiagnosticPlanError(f"{field}: must be an integer, got {value!r}")
    return value


def _exact_entry_keys(
    entry: dict[str, Any], allowed: frozenset[str], label: str
) -> None:
    """Refuse unknown members inside one nested entry.

    Parameters
    ----------
    entry
        Nested mapping under inspection.
    allowed
        Exactly the member names the entry may carry.
    label
        Boundary label for the rejection message.

    Raises
    ------
    DiagnosticPlanError
        If the entry carries any unknown member.
    """
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise DiagnosticPlanError(f"{label}: unknown members {unknown!r}")


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Assemble a JSON object while refusing duplicate members.

    Parameters
    ----------
    pairs
        Key-value pairs in document order.

    Returns
    -------
    dict[str, Any]
        The assembled object.

    Raises
    ------
    DiagnosticPlanError
        If any key occurs more than once.
    """
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise DiagnosticPlanError(f"record: duplicate member {key!r} is rejected")
        record[key] = value
    return record


_CLOCK_KEYS: Final = frozenset(
    {"identifier", "kind", "epoch", "resolution_s", "uncertainty_s"}
)


_CHANNEL_KEYS: Final = frozenset(
    {
        "identifier",
        "candidate_id",
        "carrier",
        "clock_identifier",
        "sample_rate_hz",
        "max_signal_frequency_hz",
        "timing_uncertainty_s",
        "acquisition_start_s",
        "acquisition_duration_s",
        "element_count",
        "evidence_bindings",
        "signals",
        "synthetic",
    }
)


_DEFERRAL_KEYS: Final = frozenset({"candidate_id", "reason"})


_FRAME_KEYS: Final = frozenset({"identifier", "kind", "description"})


_RELATION_KEYS: Final = frozenset(
    {
        "child_identifier",
        "parent_identifier",
        "max_offset_s",
        "uncertainty_s",
        "method",
        "mapping_state",
        "evidence_claimed",
    }
)


_SIGNAL_KEYS: Final = frozenset(
    {"identifier", "quantity", "unit", "role", "description"}
)


_TRANSFORMATION_KEYS: Final = frozenset(
    {
        "source_identifier",
        "target_identifier",
        "kind",
        "equilibrium_dependent",
        "method",
        "evidence_claimed",
    }
)


_DOMAIN_KEYS: Final = frozenset(
    {"identifier", "root_clock_identifier", "member_clock_identifiers", "scope"}
)


_TOPOLOGY_KEYS: Final = frozenset({"domains", "reference_domain_identifier"})


def plan_from_record(record: Any) -> DiagnosticPlan:
    """Build a validated diagnostic plan from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DiagnosticPlan.to_record`.

    Returns
    -------
    DiagnosticPlan
        The fully validated plan.

    Raises
    ------
    DiagnosticPlanError
        If the record shape or any value violates the model.
    """
    if not isinstance(record, dict):
        raise DiagnosticPlanError("record: must be an object")
    known = {
        "identifier",
        "binding",
        "clocks",
        "channels",
        "deferrals",
        "frames",
        "clock_relations",
        "frame_transformations",
        "clock_topology",
    }
    unknown = sorted(set(record) - known)
    if unknown:
        raise DiagnosticPlanError(f"record: unknown fields {unknown!r}")
    binding = _require_mapping(record, "binding")
    clocks = []
    for entry in _require_list(record, "clocks"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("clocks[]: must be an object")
        _exact_entry_keys(entry, _CLOCK_KEYS, "clocks[]")
        clocks.append(
            ClockModel(
                identifier=_string(entry, "identifier"),
                kind=_enum_value(entry, "kind", ClockKind),
                epoch=_string(entry, "epoch"),
                resolution_s=_number(entry, "resolution_s"),
                uncertainty_s=_number(entry, "uncertainty_s"),
            )
        )
    channels = []
    for entry in _require_list(record, "channels"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("channels[]: must be an object")
        _exact_entry_keys(entry, _CHANNEL_KEYS, "channels[]")
        channels.append(
            DiagnosticChannelPlan(
                identifier=_string(entry, "identifier"),
                candidate_id=_string(entry, "candidate_id"),
                carrier=_enum_value(entry, "carrier", SemanticCarrier),
                clock_identifier=_string(entry, "clock_identifier"),
                sample_rate_hz=_number(entry, "sample_rate_hz"),
                max_signal_frequency_hz=_number(entry, "max_signal_frequency_hz"),
                timing_uncertainty_s=_optional_number(entry, "timing_uncertainty_s"),
                acquisition_start_s=_number(entry, "acquisition_start_s"),
                acquisition_duration_s=_number(entry, "acquisition_duration_s"),
                element_count=_integer(entry, "element_count"),
                evidence_bindings=_evidence_bindings(entry),
                signals=_signals(entry),
                synthetic=_boolean(entry, "synthetic"),
            )
        )
    deferrals = []
    for entry in _require_list(record, "deferrals"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("deferrals[]: must be an object")
        _exact_entry_keys(entry, _DEFERRAL_KEYS, "deferrals[]")
        deferrals.append(
            DeferredCandidate(
                candidate_id=_string(entry, "candidate_id"),
                reason=_string(entry, "reason"),
            )
        )
    frames = []
    for entry in _require_list(record, "frames"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("frames[]: must be an object")
        _exact_entry_keys(entry, _FRAME_KEYS, "frames[]")
        frames.append(
            ReferenceFrame(
                identifier=_string(entry, "identifier"),
                kind=_enum_value(entry, "kind", FrameKind),
                description=_string(entry, "description"),
            )
        )
    relations = []
    for entry in _require_list(record, "clock_relations"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("clock_relations[]: must be an object")
        _exact_entry_keys(entry, _RELATION_KEYS, "clock_relations[]")
        relations.append(
            ClockRelation(
                child_identifier=_string(entry, "child_identifier"),
                parent_identifier=_string(entry, "parent_identifier"),
                max_offset_s=_number(entry, "max_offset_s"),
                uncertainty_s=_number(entry, "uncertainty_s"),
                method=_string(entry, "method"),
                mapping_state=_string(entry, "mapping_state"),
                evidence_claimed=_boolean(entry, "evidence_claimed"),
            )
        )
    transformations = []
    for entry in _require_list(record, "frame_transformations"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("frame_transformations[]: must be an object")
        _exact_entry_keys(entry, _TRANSFORMATION_KEYS, "frame_transformations[]")
        transformations.append(
            FrameTransformation(
                source_identifier=_string(entry, "source_identifier"),
                target_identifier=_string(entry, "target_identifier"),
                kind=_enum_value(entry, "kind", TransformationKind),
                equilibrium_dependent=_boolean(entry, "equilibrium_dependent"),
                method=_string(entry, "method"),
                evidence_claimed=_boolean(entry, "evidence_claimed"),
            )
        )
    topology_record = _require_mapping(record, "clock_topology")
    _exact_entry_keys(topology_record, _TOPOLOGY_KEYS, "clock_topology")
    domains = []
    for entry in _require_list(topology_record, "domains"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("clock_topology.domains[]: must be an object")
        _exact_entry_keys(entry, _DOMAIN_KEYS, "clock_topology.domains[]")
        domains.append(
            ClockDomain(
                identifier=_string(entry, "identifier"),
                root_clock_identifier=_string(entry, "root_clock_identifier"),
                member_clock_identifiers=_string_tuple(
                    entry, "member_clock_identifiers"
                ),
                scope=_string(entry, "scope"),
            )
        )
    topology = ClockTopology(
        domains=tuple(domains),
        reference_domain_identifier=_string(
            topology_record, "reference_domain_identifier"
        ),
    )
    return DiagnosticPlan(
        identifier=_string(record, "identifier"),
        binding=ObservabilityBinding(
            catalogue_version=_string(binding, "catalogue_version"),
            catalogue_digest_sha256=_string(binding, "catalogue_digest_sha256"),
            reactor_registry_version=_string(binding, "reactor_registry_version"),
            reactor_registry_digest_sha256=_string(
                binding, "reactor_registry_digest_sha256"
            ),
        ),
        clocks=tuple(clocks),
        channels=tuple(channels),
        deferrals=tuple(deferrals),
        frames=tuple(frames),
        clock_relations=tuple(relations),
        frame_transformations=tuple(transformations),
        clock_topology=topology,
    )


def plan_from_bytes(data: bytes) -> DiagnosticPlan:
    """Build a validated diagnostic plan from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals, duplicate
        members, and non-canonical byte forms are rejected.

    Returns
    -------
    DiagnosticPlan
        The fully validated plan.

    Raises
    ------
    DiagnosticPlanError
        If the document is not valid strict JSON, nests deeper than the
        decoder can follow, violates the model, or is not canonical.
    """

    def _reject_constant(literal: str) -> float:
        raise DiagnosticPlanError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicates,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticPlanError(f"record: invalid JSON document: {exc}") from exc
    except RecursionError as exc:
        raise DiagnosticPlanError("record: JSON nesting is too deep") from exc
    plan = plan_from_record(record)
    if plan.canonical_bytes() != data:
        raise DiagnosticPlanError("record: non-canonical document is rejected")
    return plan
