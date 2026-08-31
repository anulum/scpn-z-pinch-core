# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — diagnostic and clock semantics

"""Diagnostic-channel and clock declarations aligned with the SPO catalogue.

A :class:`DiagnosticPlan` declares synthetic diagnostic channels and clock
identities for the z-pinch configurations this repository owns, aligned
with the SCPN Phase Orchestrator observability-profile catalogue release
pinned by :data:`CATALOGUE_BINDING`. The applicable candidate subset is
embedded as data — this package never imports SCPN Phase Orchestrator
code. A plan declares HOW each evidence slot of a candidate would be
bound; it never claims that a diagnostic, a measurement, or a facility
exists. Every channel is synthetic by construction, review-only, and
non-actuating. Serialisation is canonical (sorted keys, no NaN or
infinity accepted anywhere) and the SHA-256 digest of those bytes
identifies the exact plan.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from scpn_z_pinch_core.configuration import ConsistencyFinding
from scpn_z_pinch_core.errors import DiagnosticPlanError

OWNED_CONFIGURATIONS: Final = ("sheared_flow_z_pinch", "z_pinch")
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER: Final = re.compile(r"^[a-z][a-z0-9_.]*$")

OBSERVABILITY_CATALOGUE_VERSION: Final = "1.0.0"
OBSERVABILITY_CATALOGUE_DIGEST: Final = (
    "d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609"
)
REACTOR_REGISTRY_VERSION: Final = "1.0.0"
REACTOR_REGISTRY_DIGEST: Final = (
    "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
)

INSTABILITY_BAND_HZ: Final = (1.0e05, 1.0e08)
DRIVE_TIMING_CEILING_S: Final = 1.0e-08


class ObservabilityClass(StrEnum):
    """Epistemic route mirrored from the SPO catalogue (reachable subset)."""

    DERIVED_CYCLIC = "derived_cyclic"
    EVENT_RELATIVE = "event_relative"
    NUMERICAL_ONLY = "numerical_only"


class SemanticCarrier(StrEnum):
    """Semantic carrier mirrored from the SPO vocabulary (reachable subset)."""

    COMPLEX_MODE = "complex_mode"
    CYCLIC_PHASE = "cyclic_phase"
    FIELD_PHASE = "field_phase"
    EVENT_CYCLE = "event_cycle"
    PROTOCOL_PHASE = "protocol_phase"
    NUMERICAL_PHASE = "numerical_phase"


class ClockKind(StrEnum):
    """Clock domain a channel binds its timing semantics to."""

    FACILITY_MONOTONIC = "facility_monotonic"
    SHOT_EVENT_EPOCH = "shot_event_epoch"
    SIMULATION = "simulation"


_ADMISSIBLE_CARRIERS: Final[dict[ObservabilityClass, frozenset[SemanticCarrier]]] = {
    ObservabilityClass.DERIVED_CYCLIC: frozenset(
        {
            SemanticCarrier.COMPLEX_MODE,
            SemanticCarrier.CYCLIC_PHASE,
            SemanticCarrier.FIELD_PHASE,
        }
    ),
    ObservabilityClass.EVENT_RELATIVE: frozenset(
        {SemanticCarrier.EVENT_CYCLE, SemanticCarrier.PROTOCOL_PHASE}
    ),
    ObservabilityClass.NUMERICAL_ONLY: frozenset({SemanticCarrier.NUMERICAL_PHASE}),
}
_REQUIRED_EVIDENCE: Final[dict[ObservabilityClass, tuple[str, ...]]] = {
    ObservabilityClass.DERIVED_CYCLIC: (
        "calibration",
        "clock_epoch",
        "mode_identity",
        "observability_threshold",
        "observation_operator",
        "operator_validation",
        "provenance",
        "quality",
        "reference_signal",
        "uncertainty",
        "validity",
    ),
    ObservabilityClass.EVENT_RELATIVE: (
        "clock_epoch",
        "event_reference",
        "provenance",
        "repetition_evidence",
        "timing_uncertainty",
        "validity",
    ),
    ObservabilityClass.NUMERICAL_ONLY: (
        "initial_condition",
        "model_revision",
        "provenance",
        "simulation_clock",
        "solver_validity",
    ),
}
_CLOCK_KEY: Final[dict[ObservabilityClass, str]] = {
    ObservabilityClass.DERIVED_CYCLIC: "clock_epoch",
    ObservabilityClass.EVENT_RELATIVE: "clock_epoch",
    ObservabilityClass.NUMERICAL_ONLY: "simulation_clock",
}
_COMPATIBLE_CLOCK_KINDS: Final[dict[ObservabilityClass, frozenset[ClockKind]]] = {
    ObservabilityClass.DERIVED_CYCLIC: frozenset({ClockKind.FACILITY_MONOTONIC}),
    ObservabilityClass.EVENT_RELATIVE: frozenset({ClockKind.SHOT_EVENT_EPOCH}),
    ObservabilityClass.NUMERICAL_ONLY: frozenset({ClockKind.SIMULATION}),
}
_CYCLIC_CLASSES: Final = frozenset({ObservabilityClass.DERIVED_CYCLIC})


@dataclass(frozen=True, slots=True)
class ObservabilityBinding:
    """Pin to one SPO observability-profile catalogue release.

    Parameters
    ----------
    catalogue_version
        Catalogue release version; non-empty.
    catalogue_digest_sha256
        Catalogue digest as 64 lowercase hexadecimal characters.
    reactor_registry_version
        Reactor registry release the catalogue is bound to; non-empty.
    reactor_registry_digest_sha256
        Reactor registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DiagnosticPlanError
        If any pin component is malformed.
    """

    catalogue_version: str
    catalogue_digest_sha256: str
    reactor_registry_version: str
    reactor_registry_digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the catalogue pin.

        Raises
        ------
        DiagnosticPlanError
            If any pin component is malformed.
        """
        if not self.catalogue_version:
            raise DiagnosticPlanError("binding.catalogue_version: must be non-empty")
        if not self.reactor_registry_version:
            raise DiagnosticPlanError(
                "binding.reactor_registry_version: must be non-empty"
            )
        for field, digest in (
            ("catalogue_digest_sha256", self.catalogue_digest_sha256),
            ("reactor_registry_digest_sha256", self.reactor_registry_digest_sha256),
        ):
            if HEX_DIGEST.fullmatch(digest) is None:
                raise DiagnosticPlanError(
                    f"binding.{field}: must be 64 lowercase hexadecimal "
                    f"characters, got {digest!r}"
                )


CATALOGUE_BINDING: Final = ObservabilityBinding(
    catalogue_version=OBSERVABILITY_CATALOGUE_VERSION,
    catalogue_digest_sha256=OBSERVABILITY_CATALOGUE_DIGEST,
    reactor_registry_version=REACTOR_REGISTRY_VERSION,
    reactor_registry_digest_sha256=REACTOR_REGISTRY_DIGEST,
)


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """One SPO catalogue candidate restricted to this repository.

    Applicability means only that the phenomenon is meaningful to
    investigate for the listed configurations. It asserts no
    implementation, measurement, observability, or readiness.

    Parameters
    ----------
    candidate_id
        Exact SPO catalogue candidate identifier.
    phenomenon
        Catalogue phenomenon statement.
    configurations
        Owned configurations the candidate applies to; unique and sorted.
    observability_class
        Epistemic route fixed by the catalogue.

    Raises
    ------
    DiagnosticPlanError
        If any component contradicts the catalogue structure.
    """

    candidate_id: str
    phenomenon: str
    configurations: tuple[str, ...]
    observability_class: ObservabilityClass

    def __post_init__(self) -> None:
        """Validate the embedded candidate row.

        Raises
        ------
        DiagnosticPlanError
            If any component contradicts the catalogue structure.
        """
        if IDENTIFIER.fullmatch(self.candidate_id) is None:
            raise DiagnosticPlanError(
                f"candidate.candidate_id: malformed identifier {self.candidate_id!r}"
            )
        if not self.phenomenon:
            raise DiagnosticPlanError("candidate.phenomenon: must be non-empty")
        if not self.configurations:
            raise DiagnosticPlanError(
                "candidate.configurations: must list at least one configuration"
            )
        if tuple(sorted(set(self.configurations))) != self.configurations:
            raise DiagnosticPlanError(
                "candidate.configurations: must be unique and sorted"
            )
        for configuration in self.configurations:
            if configuration not in OWNED_CONFIGURATIONS:
                raise DiagnosticPlanError(
                    "candidate.configurations: "
                    f"{configuration!r} is not owned by SCPN-Z-PINCH-CORE"
                )

    @property
    def admissible_carriers(self) -> frozenset[SemanticCarrier]:
        """Return the carriers the catalogue admits for this class.

        Returns
        -------
        frozenset of SemanticCarrier
            Admissible carriers fixed by the observability class.
        """
        return _ADMISSIBLE_CARRIERS[self.observability_class]

    @property
    def required_evidence(self) -> tuple[str, ...]:
        """Return the class-fixed evidence vocabulary.

        Returns
        -------
        tuple of str
            Evidence slot names fixed by the observability class.
        """
        return _REQUIRED_EVIDENCE[self.observability_class]


APPLICABLE_CANDIDATES: Final = (
    CandidateProfile(
        candidate_id="model.synthetic_oscillator_coordinate",
        phenomenon="model-owned synthetic oscillator coordinate",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.NUMERICAL_ONLY,
    ),
    CandidateProfile(
        candidate_id="self_magnetic.drive_waveform",
        phenomenon="pulsed-power current and voltage event progression",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.EVENT_RELATIVE,
    ),
    CandidateProfile(
        candidate_id="self_magnetic.resolved_instability_mode",
        phenomenon="resolved sausage, kink, or other pinch mode",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.DERIVED_CYCLIC,
    ),
)
_CANDIDATE_INDEX: Final = {
    candidate.candidate_id: candidate for candidate in APPLICABLE_CANDIDATES
}


@dataclass(frozen=True, slots=True)
class ClockModel:
    """One declared clock identity.

    Parameters
    ----------
    identifier
        Plan-local clock identifier.
    kind
        Clock domain the identifier represents.
    epoch
        Statement of the epoch convention; non-empty.
    resolution_s
        Smallest resolvable increment in seconds; finite and positive.
    uncertainty_s
        Declared timing uncertainty in seconds; finite and non-negative.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    kind: ClockKind
    epoch: str
    resolution_s: float
    uncertainty_s: float

    def __post_init__(self) -> None:
        """Validate the clock declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"clock.identifier: malformed identifier {self.identifier!r}"
            )
        if not self.epoch:
            raise DiagnosticPlanError("clock.epoch: must be non-empty")
        if not math.isfinite(self.resolution_s) or self.resolution_s <= 0.0:
            raise DiagnosticPlanError(
                "clock.resolution_s: must be finite and positive, "
                f"got {self.resolution_s!r}"
            )
        if not math.isfinite(self.uncertainty_s) or self.uncertainty_s < 0.0:
            raise DiagnosticPlanError(
                "clock.uncertainty_s: must be finite and non-negative, "
                f"got {self.uncertainty_s!r}"
            )


@dataclass(frozen=True, slots=True)
class DiagnosticChannelPlan:
    """One synthetic diagnostic-channel declaration.

    Parameters
    ----------
    identifier
        Plan-local channel identifier.
    candidate_id
        SPO catalogue candidate the channel addresses; must be applicable
        to this repository.
    carrier
        Semantic carrier the channel would produce; must be admissible
        for the candidate's observability class.
    clock_identifier
        Plan-local identifier of the clock the channel binds to.
    sample_rate_hz
        Declared sampling rate; finite and positive.
    max_signal_frequency_hz
        Highest signal frequency of interest; finite, non-negative, and
        positive for cyclic classes, where the Nyquist criterion
        ``sample_rate_hz >= 2 * max_signal_frequency_hz`` is enforced.
    timing_uncertainty_s
        Event-timing uncertainty; required positive for event-relative
        channels and forbidden otherwise.
    evidence_bindings
        Statement per evidence slot of HOW the slot would be bound; keys
        must exactly equal the candidate's class-fixed vocabulary.
    synthetic
        Must be ``True``; no channel in this repository describes a real
        diagnostic.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model or the catalogue alignment.
    """

    identifier: str
    candidate_id: str
    carrier: SemanticCarrier
    clock_identifier: str
    sample_rate_hz: float
    max_signal_frequency_hz: float
    timing_uncertainty_s: float | None
    evidence_bindings: dict[str, str]
    synthetic: bool

    def __post_init__(self) -> None:
        """Validate the channel declaration against the embedded catalogue.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model or the alignment.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"channel.identifier: malformed identifier {self.identifier!r}"
            )
        candidate = _CANDIDATE_INDEX.get(self.candidate_id)
        if candidate is None:
            raise DiagnosticPlanError(
                f"channel.candidate_id: {self.candidate_id!r} is not applicable "
                "to SCPN-Z-PINCH-CORE"
            )
        if self.carrier not in candidate.admissible_carriers:
            raise DiagnosticPlanError(
                f"channel.carrier: {self.carrier.value!r} is not admissible for "
                f"class {candidate.observability_class.value!r}"
            )
        if IDENTIFIER.fullmatch(self.clock_identifier) is None:
            raise DiagnosticPlanError(
                "channel.clock_identifier: malformed identifier "
                f"{self.clock_identifier!r}"
            )
        if not math.isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0.0:
            raise DiagnosticPlanError(
                "channel.sample_rate_hz: must be finite and positive, "
                f"got {self.sample_rate_hz!r}"
            )
        if (
            not math.isfinite(self.max_signal_frequency_hz)
            or self.max_signal_frequency_hz < 0.0
        ):
            raise DiagnosticPlanError(
                "channel.max_signal_frequency_hz: must be finite and "
                f"non-negative, got {self.max_signal_frequency_hz!r}"
            )
        observability_class = candidate.observability_class
        if observability_class in _CYCLIC_CLASSES:
            if self.max_signal_frequency_hz <= 0.0:
                raise DiagnosticPlanError(
                    "channel.max_signal_frequency_hz: cyclic channels must "
                    "declare a positive signal band"
                )
            if self.sample_rate_hz < 2.0 * self.max_signal_frequency_hz:
                raise DiagnosticPlanError(
                    "channel.sample_rate_hz: Nyquist violation, "
                    f"{self.sample_rate_hz!r} Hz cannot resolve "
                    f"{self.max_signal_frequency_hz!r} Hz"
                )
        if observability_class is ObservabilityClass.EVENT_RELATIVE:
            if self.timing_uncertainty_s is None or not (
                math.isfinite(self.timing_uncertainty_s)
                and self.timing_uncertainty_s > 0.0
            ):
                raise DiagnosticPlanError(
                    "channel.timing_uncertainty_s: event-relative channels "
                    "must declare a finite positive timing uncertainty, "
                    f"got {self.timing_uncertainty_s!r}"
                )
        elif self.timing_uncertainty_s is not None:
            raise DiagnosticPlanError(
                "channel.timing_uncertainty_s: only event-relative channels "
                "declare a timing uncertainty"
            )
        expected = set(candidate.required_evidence)
        declared = set(self.evidence_bindings)
        if declared != expected:
            missing = sorted(expected - declared)
            extra = sorted(declared - expected)
            raise DiagnosticPlanError(
                "channel.evidence_bindings: keys must equal the class-fixed "
                f"vocabulary; missing={missing!r}, extra={extra!r}"
            )
        for slot, statement in self.evidence_bindings.items():
            if not statement:
                raise DiagnosticPlanError(
                    f"channel.evidence_bindings[{slot!r}]: must be non-empty"
                )
        clock_key = _CLOCK_KEY[observability_class]
        if self.evidence_bindings[clock_key] != self.clock_identifier:
            raise DiagnosticPlanError(
                f"channel.evidence_bindings[{clock_key!r}]: must reference the "
                f"bound clock {self.clock_identifier!r}"
            )
        if self.synthetic is not True:
            raise DiagnosticPlanError(
                "channel.synthetic: every channel in this repository is "
                "synthetic; no real diagnostic is described"
            )

    @property
    def observability_class(self) -> ObservabilityClass:
        """Return the catalogue class of the addressed candidate.

        Returns
        -------
        ObservabilityClass
            Class fixed by the embedded catalogue subset.
        """
        return _CANDIDATE_INDEX[self.candidate_id].observability_class


@dataclass(frozen=True, slots=True)
class DeferredCandidate:
    """Explicit deferral of one applicable candidate.

    Parameters
    ----------
    candidate_id
        Applicable candidate left unplanned in this lane.
    reason
        Non-empty statement of why the deferral is honest.

    Raises
    ------
    DiagnosticPlanError
        If the candidate is not applicable or the reason is empty.
    """

    candidate_id: str
    reason: str

    def __post_init__(self) -> None:
        """Validate the deferral.

        Raises
        ------
        DiagnosticPlanError
            If the candidate is not applicable or the reason is empty.
        """
        if self.candidate_id not in _CANDIDATE_INDEX:
            raise DiagnosticPlanError(
                f"deferral.candidate_id: {self.candidate_id!r} is not "
                "applicable to SCPN-Z-PINCH-CORE"
            )
        if not self.reason:
            raise DiagnosticPlanError("deferral.reason: must be non-empty")


@dataclass(frozen=True, slots=True)
class DiagnosticPlan:
    """Validated diagnostic and clock plan for the owned configurations.

    Parameters
    ----------
    identifier
        Plan identifier.
    binding
        Pin to the SPO observability-profile catalogue release; must
        equal :data:`CATALOGUE_BINDING` exactly.
    clocks
        Declared clocks, sorted by identifier.
    channels
        Declared synthetic channels, sorted by identifier.
    deferrals
        Explicit deferrals, sorted by candidate identifier.

    Raises
    ------
    DiagnosticPlanError
        If any cross-object invariant is violated.
    """

    identifier: str
    binding: ObservabilityBinding
    clocks: tuple[ClockModel, ...]
    channels: tuple[DiagnosticChannelPlan, ...]
    deferrals: tuple[DeferredCandidate, ...]

    def __post_init__(self) -> None:
        """Validate cross-object invariants of the plan.

        Raises
        ------
        DiagnosticPlanError
            If any cross-object invariant is violated.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"plan.identifier: malformed identifier {self.identifier!r}"
            )
        if self.binding != CATALOGUE_BINDING:
            raise DiagnosticPlanError(
                "plan.binding: must pin the embedded catalogue release "
                f"{OBSERVABILITY_CATALOGUE_VERSION} "
                f"({OBSERVABILITY_CATALOGUE_DIGEST})"
            )
        clock_ids = tuple(clock.identifier for clock in self.clocks)
        if tuple(sorted(set(clock_ids))) != clock_ids:
            raise DiagnosticPlanError("plan.clocks: must be unique and sorted")
        channel_ids = tuple(channel.identifier for channel in self.channels)
        if tuple(sorted(set(channel_ids))) != channel_ids:
            raise DiagnosticPlanError("plan.channels: must be unique and sorted")
        deferral_ids = tuple(deferral.candidate_id for deferral in self.deferrals)
        if tuple(sorted(set(deferral_ids))) != deferral_ids:
            raise DiagnosticPlanError("plan.deferrals: must be unique and sorted")
        clocks_by_id = {clock.identifier: clock for clock in self.clocks}
        for channel in self.channels:
            clock = clocks_by_id.get(channel.clock_identifier)
            if clock is None:
                raise DiagnosticPlanError(
                    f"plan.channels[{channel.identifier!r}]: clock "
                    f"{channel.clock_identifier!r} is not declared"
                )
            observability_class = channel.observability_class
            if clock.kind not in _COMPATIBLE_CLOCK_KINDS[observability_class]:
                raise DiagnosticPlanError(
                    f"plan.channels[{channel.identifier!r}]: clock kind "
                    f"{clock.kind.value!r} is incompatible with class "
                    f"{observability_class.value!r}"
                )
            if (
                observability_class is ObservabilityClass.EVENT_RELATIVE
                and channel.timing_uncertainty_s is not None
                and clock.resolution_s > channel.timing_uncertainty_s
            ):
                raise DiagnosticPlanError(
                    f"plan.channels[{channel.identifier!r}]: clock resolution "
                    f"{clock.resolution_s!r} s cannot support the declared "
                    f"timing uncertainty {channel.timing_uncertainty_s!r} s"
                )
        planned = {channel.candidate_id for channel in self.channels}
        deferred = set(deferral_ids)
        overlap = sorted(planned & deferred)
        if overlap:
            raise DiagnosticPlanError(
                f"plan: candidates {overlap!r} are both planned and deferred"
            )
        applicable = set(_CANDIDATE_INDEX)
        covered = planned | deferred
        if covered != applicable:
            missing = sorted(applicable - covered)
            unknown = sorted(covered - applicable)
            raise DiagnosticPlanError(
                "plan: applicable candidates must be planned or explicitly "
                f"deferred; missing={missing!r}, unknown={unknown!r}"
            )

    def consistency_report(self) -> tuple[ConsistencyFinding, ...]:
        """Report device-typical band findings without failing.

        Returns
        -------
        tuple of ConsistencyFinding
            Findings from documented z-pinch diagnostic practice; empty
            when every declaration sits in its typical band. Findings
            are advisory instruments, not machine claims.
        """
        findings: list[ConsistencyFinding] = []
        clocks_by_id = {clock.identifier: clock for clock in self.clocks}
        low, high = INSTABILITY_BAND_HZ
        for channel in self.channels:
            observability_class = channel.observability_class
            if (
                channel.candidate_id == "self_magnetic.resolved_instability_mode"
                and not (low <= channel.max_signal_frequency_hz <= high)
            ):
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].max_signal_frequency_hz",
                        message=(
                            "declared instability band "
                            f"{channel.max_signal_frequency_hz:.1f} "
                            "Hz is outside the sausage/kink pinch "
                            "instability scale 0.1-100 MHz "
                            "(Shumlak and Hartman 1995)"
                        ),
                    )
                )
            if (
                observability_class is ObservabilityClass.EVENT_RELATIVE
                and channel.timing_uncertainty_s is not None
                and channel.timing_uncertainty_s > DRIVE_TIMING_CEILING_S
            ):
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].timing_uncertainty_s",
                        message=(
                            f"timing uncertainty {channel.timing_uncertainty_s:.2e} s"
                            " is coarser than the ~100 ns pinch "
                            "drive timescale "
                            "(Shumlak and Hartman 1995)"
                        ),
                    )
                )
            clock = clocks_by_id[channel.clock_identifier]
            if clock.resolution_s > 1.0 / channel.sample_rate_hz:
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].sample_rate_hz",
                        message=(
                            f"clock {clock.identifier} resolution "
                            f"{clock.resolution_s:.2e} s cannot distinguish "
                            "consecutive samples at "
                            f"{channel.sample_rate_hz:.1f} Hz"
                        ),
                    )
                )
        return tuple(findings)

    def to_record(self) -> dict[str, Any]:
        """Project the plan to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Nested record with every declared component.
        """
        return {
            "identifier": self.identifier,
            "binding": {
                "catalogue_version": self.binding.catalogue_version,
                "catalogue_digest_sha256": self.binding.catalogue_digest_sha256,
                "reactor_registry_version": self.binding.reactor_registry_version,
                "reactor_registry_digest_sha256": (
                    self.binding.reactor_registry_digest_sha256
                ),
            },
            "clocks": [
                {
                    "identifier": clock.identifier,
                    "kind": clock.kind.value,
                    "epoch": clock.epoch,
                    "resolution_s": clock.resolution_s,
                    "uncertainty_s": clock.uncertainty_s,
                }
                for clock in self.clocks
            ],
            "channels": [
                {
                    "identifier": channel.identifier,
                    "candidate_id": channel.candidate_id,
                    "carrier": channel.carrier.value,
                    "clock_identifier": channel.clock_identifier,
                    "sample_rate_hz": channel.sample_rate_hz,
                    "max_signal_frequency_hz": channel.max_signal_frequency_hz,
                    "timing_uncertainty_s": channel.timing_uncertainty_s,
                    "evidence_bindings": dict(
                        sorted(channel.evidence_bindings.items())
                    ),
                    "synthetic": channel.synthetic,
                }
                for channel in self.channels
            ],
            "deferrals": [
                {
                    "candidate_id": deferral.candidate_id,
                    "reason": deferral.reason,
                }
                for deferral in self.deferrals
            ],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the plan canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact plan.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


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
    known = {"identifier", "binding", "clocks", "channels", "deferrals"}
    unknown = sorted(set(record) - known)
    if unknown:
        raise DiagnosticPlanError(f"record: unknown fields {unknown!r}")
    binding = _require_mapping(record, "binding")
    clocks = []
    for entry in _require_list(record, "clocks"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("clocks[]: must be an object")
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
        channels.append(
            DiagnosticChannelPlan(
                identifier=_string(entry, "identifier"),
                candidate_id=_string(entry, "candidate_id"),
                carrier=_enum_value(entry, "carrier", SemanticCarrier),
                clock_identifier=_string(entry, "clock_identifier"),
                sample_rate_hz=_number(entry, "sample_rate_hz"),
                max_signal_frequency_hz=_number(entry, "max_signal_frequency_hz"),
                timing_uncertainty_s=_optional_number(entry, "timing_uncertainty_s"),
                evidence_bindings=_evidence_bindings(entry),
                synthetic=_boolean(entry, "synthetic"),
            )
        )
    deferrals = []
    for entry in _require_list(record, "deferrals"):
        if not isinstance(entry, dict):
            raise DiagnosticPlanError("deferrals[]: must be an object")
        deferrals.append(
            DeferredCandidate(
                candidate_id=_string(entry, "candidate_id"),
                reason=_string(entry, "reason"),
            )
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
    )


def plan_from_bytes(data: bytes) -> DiagnosticPlan:
    """Build a validated diagnostic plan from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DiagnosticPlan
        The fully validated plan.

    Raises
    ------
    DiagnosticPlanError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DiagnosticPlanError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticPlanError(f"record: invalid JSON document: {exc}") from exc
    return plan_from_record(record)
