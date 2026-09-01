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

SHOT_DURATION_CEILING_S: Final = 1.0e-03
ELEMENT_COUNT_BAND: Final = (4, 256)


class FrameKind(StrEnum):
    """Reference-frame kind a declared frame may take."""

    MACHINE_CARTESIAN = "machine_cartesian"
    MACHINE_CYLINDRICAL = "machine_cylindrical"
    FLUX_SURFACE = "flux_surface"
    BOOZER = "boozer"
    FIELD_LINE = "field_line"
    CHAMBER_CARTESIAN = "chamber_cartesian"
    BEAMLINE = "beamline"
    BLANKET_ZONE = "blanket_zone"


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


class SignalRole(StrEnum):
    """Role one declared signal plays inside a channel's inventory."""

    CARRIER = "carrier"
    TIMING_MARKER = "timing_marker"
    AMPLITUDE = "amplitude"
    AUXILIARY = "auxiliary"


class TransformationKind(StrEnum):
    """Kind of a declared mapping between two declared reference frames."""

    RIGID = "rigid"
    FLUX_MAPPING = "flux_mapping"
    PROJECTION = "projection"


ALLOWED_FRAME_KINDS: Final = frozenset(
    {
        FrameKind.MACHINE_CYLINDRICAL,
    }
)

_ADMISSIBLE_TRANSFORMATIONS: Final[dict[frozenset[FrameKind], TransformationKind]] = {
    frozenset({FrameKind.MACHINE_CYLINDRICAL, FrameKind.FLUX_SURFACE}): (
        TransformationKind.FLUX_MAPPING
    ),
    frozenset(
        {FrameKind.FLUX_SURFACE, FrameKind.BOOZER}
    ): TransformationKind.FLUX_MAPPING,
    frozenset({FrameKind.FIELD_LINE, FrameKind.MACHINE_CYLINDRICAL}): (
        TransformationKind.FLUX_MAPPING
    ),
    frozenset({FrameKind.BLANKET_ZONE, FrameKind.MACHINE_CYLINDRICAL}): (
        TransformationKind.PROJECTION
    ),
    frozenset(
        {FrameKind.CHAMBER_CARTESIAN, FrameKind.BEAMLINE}
    ): TransformationKind.RIGID,
}
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
class ReferenceFrame:
    """One declared reference-frame identity.

    Parameters
    ----------
    identifier
        Plan-local frame identifier.
    kind
        Frame kind; must be allowed for this repository.
    description
        Statement of the frame convention; non-empty.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    kind: FrameKind
    description: str

    def __post_init__(self) -> None:
        """Validate the frame declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"frame.identifier: malformed identifier {self.identifier!r}"
            )
        if self.kind not in ALLOWED_FRAME_KINDS:
            raise DiagnosticPlanError(
                f"frame.kind: {self.kind.value!r} is not an allowed frame "
                "kind for this repository"
            )
        if not self.description:
            raise DiagnosticPlanError("frame.description: must be non-empty")


@dataclass(frozen=True, slots=True)
class ClockRelation:
    """One declared synchronisation bound between two declared clocks.

    A relation declares synthetic offset and uncertainty BOUNDS between
    two clock identities; it claims no correlation evidence, and no
    clock is thereby mapped to physical wall time.

    Parameters
    ----------
    child_identifier
        Clock whose epoch is being bounded.
    parent_identifier
        Clock the bound is stated against.
    max_offset_s
        Declared worst-case offset magnitude; finite and non-negative.
    uncertainty_s
        Declared uncertainty of the bound; finite and non-negative.
    method
        Statement of HOW the bound would be established; non-empty.
    mapping_state
        Must be ``"unmapped"``: no clock is mapped to wall time.
    evidence_claimed
        Must be ``False``: no correlation evidence exists or is claimed.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    child_identifier: str
    parent_identifier: str
    max_offset_s: float
    uncertainty_s: float
    method: str
    mapping_state: str
    evidence_claimed: bool

    def __post_init__(self) -> None:
        """Validate the relation declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        for field, value in (
            ("child_identifier", self.child_identifier),
            ("parent_identifier", self.parent_identifier),
        ):
            if IDENTIFIER.fullmatch(value) is None:
                raise DiagnosticPlanError(
                    f"relation.{field}: malformed identifier {value!r}"
                )
        if self.child_identifier == self.parent_identifier:
            raise DiagnosticPlanError("relation: a clock cannot be related to itself")
        for bound_field, bound_value in (
            ("max_offset_s", self.max_offset_s),
            ("uncertainty_s", self.uncertainty_s),
        ):
            if not math.isfinite(bound_value) or bound_value < 0.0:
                raise DiagnosticPlanError(
                    f"relation.{bound_field}: must be finite and "
                    f"non-negative, got {bound_value!r}"
                )
        if not self.method:
            raise DiagnosticPlanError("relation.method: must be non-empty")
        if self.mapping_state != "unmapped":
            raise DiagnosticPlanError(
                "relation.mapping_state: must be 'unmapped'; no clock is "
                f"mapped to wall time, got {self.mapping_state!r}"
            )
        if self.evidence_claimed is not False:
            raise DiagnosticPlanError(
                "relation.evidence_claimed: must be False; no correlation "
                "evidence exists or is claimed"
            )


@dataclass(frozen=True, slots=True)
class SignalDeclaration:
    """One declared signal inside a channel's inventory.

    A signal declaration names WHAT a channel would carry; it is a
    declaration only. The quantity and unit tokens are declared strings —
    no SI or UCUM validation is performed or claimed — and no declaration
    creates or overrides a candidate, carrier, observation, or phase: the
    candidate profile remains authoritative.

    Parameters
    ----------
    identifier
        Channel-local signal identifier.
    quantity
        Declared physical quantity name; non-empty.
    unit
        Declared unit token; non-empty, no whitespace.
    role
        Role of the signal inside the channel inventory.
    description
        Statement of what the signal would carry; non-empty.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    quantity: str
    unit: str
    role: SignalRole
    description: str

    def __post_init__(self) -> None:
        """Validate the signal declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"signal.identifier: malformed identifier {self.identifier!r}"
            )
        if not self.quantity:
            raise DiagnosticPlanError("signal.quantity: must be non-empty")
        if not self.unit or any(character.isspace() for character in self.unit):
            raise DiagnosticPlanError(
                "signal.unit: must be a non-empty token without whitespace, "
                f"got {self.unit!r}"
            )
        if not self.description:
            raise DiagnosticPlanError("signal.description: must be non-empty")


@dataclass(frozen=True, slots=True)
class FrameTransformation:
    """One declared mapping between two declared reference frames.

    A transformation declares HOW coordinates in the source frame would be
    expressed in the target frame; the method is a declaration and no
    metrological evidence is claimed.

    Parameters
    ----------
    source_identifier
        Declared frame the mapping starts from.
    target_identifier
        Declared frame the mapping lands in.
    kind
        Mapping kind; must be admissible for the two frame kinds.
    equilibrium_dependent
        Must be ``True`` exactly for ``flux_mapping`` (the mapping depends
        on an equilibrium reconstruction) and ``False`` otherwise.
    method
        Statement of HOW the mapping would be established; non-empty.
    evidence_claimed
        Must be ``False``: no mapping evidence exists or is claimed.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    source_identifier: str
    target_identifier: str
    kind: TransformationKind
    equilibrium_dependent: bool
    method: str
    evidence_claimed: bool

    def __post_init__(self) -> None:
        """Validate the transformation declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        for field, value in (
            ("source_identifier", self.source_identifier),
            ("target_identifier", self.target_identifier),
        ):
            if IDENTIFIER.fullmatch(value) is None:
                raise DiagnosticPlanError(
                    f"transformation.{field}: malformed identifier {value!r}"
                )
        if self.source_identifier == self.target_identifier:
            raise DiagnosticPlanError(
                "transformation: a frame cannot be transformed to itself"
            )
        expected_dependency = self.kind is TransformationKind.FLUX_MAPPING
        if self.equilibrium_dependent is not expected_dependency:
            raise DiagnosticPlanError(
                "transformation.equilibrium_dependent: must be "
                f"{expected_dependency!r} for kind {self.kind.value!r}"
            )
        if not self.method:
            raise DiagnosticPlanError("transformation.method: must be non-empty")
        if self.evidence_claimed is not False:
            raise DiagnosticPlanError(
                "transformation.evidence_claimed: must be False; no mapping "
                "evidence exists or is claimed"
            )


@dataclass(frozen=True, slots=True)
class ClockDomain:
    """One declared clock domain: a root clock and the clocks bound to it.

    Parameters
    ----------
    identifier
        Plan-local domain identifier.
    root_clock_identifier
        Declared clock the domain is referenced to; must be a member.
    member_clock_identifiers
        Declared clocks in the domain; unique, sorted, non-empty.
    scope
        Statement of the facility subsystem the domain represents; a
        declaration only.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    root_clock_identifier: str
    member_clock_identifiers: tuple[str, ...]
    scope: str

    def __post_init__(self) -> None:
        """Validate the domain declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"domain.identifier: malformed identifier {self.identifier!r}"
            )
        if IDENTIFIER.fullmatch(self.root_clock_identifier) is None:
            raise DiagnosticPlanError(
                "domain.root_clock_identifier: malformed identifier "
                f"{self.root_clock_identifier!r}"
            )
        if not self.member_clock_identifiers:
            raise DiagnosticPlanError(
                "domain.member_clock_identifiers: must list at least one clock"
            )
        if (
            tuple(sorted(set(self.member_clock_identifiers)))
            != self.member_clock_identifiers
        ):
            raise DiagnosticPlanError(
                "domain.member_clock_identifiers: must be unique and sorted"
            )
        if self.root_clock_identifier not in self.member_clock_identifiers:
            raise DiagnosticPlanError(
                "domain.root_clock_identifier: the root must be a member"
            )
        if not self.scope:
            raise DiagnosticPlanError("domain.scope: must be non-empty")


@dataclass(frozen=True, slots=True)
class ClockTopology:
    """Declared partition of the physical clocks into domains.

    Parameters
    ----------
    domains
        Declared domains, sorted by identifier; at least one.
    reference_domain_identifier
        Domain whose root is the plan's timing reference; must be declared.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    domains: tuple[ClockDomain, ...]
    reference_domain_identifier: str

    def __post_init__(self) -> None:
        """Validate the topology declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if not self.domains:
            raise DiagnosticPlanError(
                "topology.domains: must declare at least one domain"
            )
        domain_ids = tuple(domain.identifier for domain in self.domains)
        if tuple(sorted(set(domain_ids))) != domain_ids:
            raise DiagnosticPlanError("topology.domains: must be unique and sorted")
        if self.reference_domain_identifier not in domain_ids:
            raise DiagnosticPlanError(
                "topology.reference_domain_identifier: "
                f"{self.reference_domain_identifier!r} is not a declared domain"
            )


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
    acquisition_start_s
        Acquisition window start relative to the bound clock's epoch;
        finite (negative means pre-trigger).
    acquisition_duration_s
        Acquisition window length; finite and positive.
    element_count
        Number of declared sensing elements; integer, at least one.
    evidence_bindings
        Statement per evidence slot of HOW the slot would be bound; keys
        must exactly equal the candidate's class-fixed vocabulary.
    signals
        Declared signal inventory of the channel; non-empty, unique and
        sorted by identifier, exactly one ``carrier`` signal, a
        ``timing_marker`` (unit ``"s"``) exactly for event-relative
        channels, and a single ``phase``/``rad`` carrier for
        numerical-only channels.
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
    acquisition_start_s: float
    acquisition_duration_s: float
    element_count: int
    evidence_bindings: dict[str, str]
    signals: tuple[SignalDeclaration, ...]
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
        if not math.isfinite(self.acquisition_start_s):
            raise DiagnosticPlanError(
                "channel.acquisition_start_s: must be finite, "
                f"got {self.acquisition_start_s!r}"
            )
        if (
            not math.isfinite(self.acquisition_duration_s)
            or self.acquisition_duration_s <= 0.0
        ):
            raise DiagnosticPlanError(
                "channel.acquisition_duration_s: must be finite and "
                f"positive, got {self.acquisition_duration_s!r}"
            )
        if isinstance(self.element_count, bool) or not isinstance(
            self.element_count, int
        ):
            raise DiagnosticPlanError(
                f"channel.element_count: must be an integer, got {self.element_count!r}"
            )
        if self.element_count < 1:
            raise DiagnosticPlanError(
                f"channel.element_count: must be at least 1, got {self.element_count!r}"
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
        self._validate_signals(observability_class)
        if self.synthetic is not True:
            raise DiagnosticPlanError(
                "channel.synthetic: every channel in this repository is "
                "synthetic; no real diagnostic is described"
            )

    def _validate_signals(self, observability_class: ObservabilityClass) -> None:
        """Validate the signal inventory against the channel's class.

        Parameters
        ----------
        observability_class
            Class of the addressed candidate.

        Raises
        ------
        DiagnosticPlanError
            If the inventory violates the model.
        """
        if not self.signals:
            raise DiagnosticPlanError(
                "channel.signals: must declare at least one signal"
            )
        signal_ids = tuple(signal.identifier for signal in self.signals)
        if tuple(sorted(set(signal_ids))) != signal_ids:
            raise DiagnosticPlanError("channel.signals: must be unique and sorted")
        carriers = [
            signal for signal in self.signals if signal.role is SignalRole.CARRIER
        ]
        if len(carriers) != 1:
            raise DiagnosticPlanError(
                "channel.signals: exactly one carrier signal is required, "
                f"got {len(carriers)}"
            )
        markers = [
            signal for signal in self.signals if signal.role is SignalRole.TIMING_MARKER
        ]
        if observability_class is ObservabilityClass.EVENT_RELATIVE:
            if len(markers) != 1:
                raise DiagnosticPlanError(
                    "channel.signals: event-relative channels declare exactly one "
                    f"timing_marker signal, got {len(markers)}"
                )
            if markers[0].unit != "s":
                raise DiagnosticPlanError(
                    "channel.signals: the timing_marker signal must be declared in "
                    f"seconds ('s'), got {markers[0].unit!r}"
                )
        elif markers:
            raise DiagnosticPlanError(
                "channel.signals: only event-relative channels declare a timing_marker"
            )
        if observability_class is ObservabilityClass.NUMERICAL_ONLY and (
            len(self.signals) != 1
            or carriers[0].quantity != "phase"
            or carriers[0].unit != "rad"
        ):
            raise DiagnosticPlanError(
                "channel.signals: numerical-only channels declare exactly one "
                "carrier signal of quantity 'phase' in 'rad'"
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
    frames
        Declared reference frames, sorted by identifier.
    clock_relations
        Declared clock synchronisation bounds, sorted by child then
        parent identifier.
    frame_transformations
        Declared mappings between declared frames, sorted by source then
        target identifier; at most one per frame pair; when two or more
        frames are declared the mappings must connect all of them.
    clock_topology
        Declared partition of the non-simulation clocks into domains.

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
    frames: tuple[ReferenceFrame, ...]
    clock_relations: tuple[ClockRelation, ...]
    frame_transformations: tuple[FrameTransformation, ...]
    clock_topology: ClockTopology

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
        frame_ids = tuple(frame.identifier for frame in self.frames)
        if tuple(sorted(set(frame_ids))) != frame_ids:
            raise DiagnosticPlanError("plan.frames: must be unique and sorted")
        relation_keys = tuple(
            (relation.child_identifier, relation.parent_identifier)
            for relation in self.clock_relations
        )
        if tuple(sorted(set(relation_keys))) != relation_keys:
            raise DiagnosticPlanError("plan.clock_relations: must be unique and sorted")
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
        for relation in self.clock_relations:
            for role, identifier in (
                ("child", relation.child_identifier),
                ("parent", relation.parent_identifier),
            ):
                clock = clocks_by_id.get(identifier)
                if clock is None:
                    raise DiagnosticPlanError(
                        f"plan.clock_relations: {role} clock {identifier!r} "
                        "is not declared"
                    )
                if clock.kind is ClockKind.SIMULATION:
                    raise DiagnosticPlanError(
                        "plan.clock_relations: the simulation clock keeps "
                        "model time and cannot be related to physical clocks"
                    )
        related_children = {
            relation.child_identifier for relation in self.clock_relations
        }
        facility_ids = [
            clock.identifier
            for clock in self.clocks
            if clock.kind is ClockKind.FACILITY_MONOTONIC
        ]
        if facility_ids:
            for clock in self.clocks:
                if (
                    clock.kind is ClockKind.SHOT_EVENT_EPOCH
                    and clock.identifier not in related_children
                ):
                    raise DiagnosticPlanError(
                        f"plan.clock_relations: epoch clock "
                        f"{clock.identifier!r} must declare a bound against "
                        "a facility clock"
                    )
        self._validate_transformations(
            {frame.identifier: frame for frame in self.frames}
        )
        self._validate_topology({clock.identifier: clock for clock in self.clocks})
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

    def _validate_transformations(
        self, frames_by_id: dict[str, ReferenceFrame]
    ) -> None:
        """Validate the declared frame transformations.

        Parameters
        ----------
        frames_by_id
            Declared frames keyed by identifier.

        Raises
        ------
        DiagnosticPlanError
            If any transformation invariant is violated.
        """
        if self.frame_transformations:
            raise DiagnosticPlanError(
                "plan.frame_transformations: no admissible transformation exists "
                "between the frame kinds this repository may declare"
            )
        if len(frames_by_id) > 1:
            raise DiagnosticPlanError(
                "plan.frames: a second frame cannot be connected in this repository"
            )

    def _validate_topology(self, clocks_by_id: dict[str, ClockModel]) -> None:
        """Validate the declared clock topology against clocks and relations.

        Parameters
        ----------
        clocks_by_id
            Declared clocks keyed by identifier.

        Raises
        ------
        DiagnosticPlanError
            If any topology invariant is violated.
        """
        topology = self.clock_topology
        membership: dict[str, str] = {}
        for domain in topology.domains:
            for member in domain.member_clock_identifiers:
                clock = clocks_by_id.get(member)
                if clock is None:
                    raise DiagnosticPlanError(
                        f"plan.clock_topology: clock {member!r} is not declared"
                    )
                if clock.kind is ClockKind.SIMULATION:
                    raise DiagnosticPlanError(
                        "plan.clock_topology: the simulation clock keeps model time "
                        "and belongs to no physical domain"
                    )
                if member in membership:
                    raise DiagnosticPlanError(
                        f"plan.clock_topology: clock {member!r} belongs to more than "
                        "one domain"
                    )
                membership[member] = domain.identifier
            root = clocks_by_id[domain.root_clock_identifier]
            has_facility = any(
                clocks_by_id[member].kind is ClockKind.FACILITY_MONOTONIC
                for member in domain.member_clock_identifiers
            )
            expected_kind = (
                ClockKind.FACILITY_MONOTONIC
                if has_facility
                else ClockKind.SHOT_EVENT_EPOCH
            )
            if root.kind is not expected_kind:
                raise DiagnosticPlanError(
                    f"plan.clock_topology: domain {domain.identifier!r} root must be "
                    f"of kind {expected_kind.value!r}, got {root.kind.value!r}"
                )
        unassigned = sorted(
            identifier
            for identifier, clock in clocks_by_id.items()
            if clock.kind is not ClockKind.SIMULATION and identifier not in membership
        )
        if unassigned:
            raise DiagnosticPlanError(
                f"plan.clock_topology: clocks {unassigned!r} belong to no domain"
            )
        parents: dict[str, set[str]] = {}
        for relation in self.clock_relations:
            parents.setdefault(relation.child_identifier, set()).add(
                relation.parent_identifier
            )
        reference_root = next(
            domain.root_clock_identifier
            for domain in topology.domains
            if domain.identifier == topology.reference_domain_identifier
        )
        for domain in topology.domains:
            for member in domain.member_clock_identifiers:
                if member != domain.root_clock_identifier and (
                    domain.root_clock_identifier not in parents.get(member, set())
                ):
                    raise DiagnosticPlanError(
                        f"plan.clock_topology: clock {member!r} must declare a "
                        f"relation to its domain root {domain.root_clock_identifier!r}"
                    )
            if domain.identifier != topology.reference_domain_identifier:
                cross = parents.get(domain.root_clock_identifier, set())
                if reference_root not in cross:
                    raise DiagnosticPlanError(
                        "plan.clock_topology: domain root "
                        f"{domain.root_clock_identifier!r} must declare a relation "
                        f"to the reference root {reference_root!r}"
                    )
        visiting: set[str] = set()
        finished: set[str] = set()

        def _visit(identifier: str) -> None:
            if identifier in finished:
                return
            if identifier in visiting:
                raise DiagnosticPlanError(
                    "plan.clock_relations: relations must not form a cycle"
                )
            visiting.add(identifier)
            for parent in sorted(parents.get(identifier, set())):
                _visit(parent)
            visiting.discard(identifier)
            finished.add(identifier)

        for identifier in sorted(clocks_by_id):
            _visit(identifier)

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
            if channel.acquisition_duration_s > SHOT_DURATION_CEILING_S:
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].acquisition_duration_s",
                        message=(
                            "acquisition window "
                            f"{channel.acquisition_duration_s:.2e} s is "
                            "longer than the z-pinch discharge scale of up to "
                            "~1 ms (Shumlak and Hartman 1995)"
                        ),
                    )
                )
            low_count, high_count = ELEMENT_COUNT_BAND
            if channel.element_count > 1 and not (
                low_count <= channel.element_count <= high_count
            ):
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].element_count",
                        message=(
                            f"array size {channel.element_count} is outside "
                            "the common multi-element diagnostic range "
                            "4-256 elements"
                        ),
                    )
                )
            if (
                channel.observability_class is ObservabilityClass.DERIVED_CYCLIC
                and channel.element_count > 1
                and not any(
                    signal.role is SignalRole.AMPLITUDE for signal in channel.signals
                )
            ):
                findings.append(
                    ConsistencyFinding(
                        field=f"channels[{channel.identifier}].signals",
                        message=(
                            "a multi-element cyclic array declares no amplitude "
                            "signal in its inventory"
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
                    "acquisition_start_s": channel.acquisition_start_s,
                    "acquisition_duration_s": (channel.acquisition_duration_s),
                    "element_count": channel.element_count,
                    "evidence_bindings": dict(
                        sorted(channel.evidence_bindings.items())
                    ),
                    "signals": [
                        {
                            "identifier": signal.identifier,
                            "quantity": signal.quantity,
                            "unit": signal.unit,
                            "role": signal.role.value,
                            "description": signal.description,
                        }
                        for signal in channel.signals
                    ],
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
            "frames": [
                {
                    "identifier": frame.identifier,
                    "kind": frame.kind.value,
                    "description": frame.description,
                }
                for frame in self.frames
            ],
            "clock_relations": [
                {
                    "child_identifier": relation.child_identifier,
                    "parent_identifier": relation.parent_identifier,
                    "max_offset_s": relation.max_offset_s,
                    "uncertainty_s": relation.uncertainty_s,
                    "method": relation.method,
                    "mapping_state": relation.mapping_state,
                    "evidence_claimed": relation.evidence_claimed,
                }
                for relation in self.clock_relations
            ],
            "frame_transformations": [
                {
                    "source_identifier": transformation.source_identifier,
                    "target_identifier": transformation.target_identifier,
                    "kind": transformation.kind.value,
                    "equilibrium_dependent": transformation.equilibrium_dependent,
                    "method": transformation.method,
                    "evidence_claimed": transformation.evidence_claimed,
                }
                for transformation in self.frame_transformations
            ],
            "clock_topology": {
                "domains": [
                    {
                        "identifier": domain.identifier,
                        "root_clock_identifier": domain.root_clock_identifier,
                        "member_clock_identifiers": list(
                            domain.member_clock_identifiers
                        ),
                        "scope": domain.scope,
                    }
                    for domain in self.clock_topology.domains
                ],
                "reference_domain_identifier": (
                    self.clock_topology.reference_domain_identifier
                ),
            },
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
        If the document is not valid strict JSON or violates the model.
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
    plan = plan_from_record(record)
    if plan.canonical_bytes() != data:
        raise DiagnosticPlanError("record: non-canonical document is rejected")
    return plan
