# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — diagnostic plan composition

"""Composition of a whole diagnostic plan.

:class:`DiagnosticPlan` composes channels, clocks, frames, transformations
and the clock topology for one owned configuration, checks them against
each other and the pinned catalogue, and serialises canonically; the
SHA-256 digest of those bytes identifies the exact plan.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from scpn_z_pinch_core.configuration import ConsistencyFinding
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.binding import (
    _CANDIDATE_INDEX,
    CATALOGUE_BINDING,
    ObservabilityBinding,
)
from scpn_z_pinch_core.observability.clocks import (
    ClockModel,
    ClockRelation,
    ClockTopology,
)
from scpn_z_pinch_core.observability.frames import (
    FrameTransformation,
    ReferenceFrame,
)
from scpn_z_pinch_core.observability.signals import (
    DeferredCandidate,
    DiagnosticChannelPlan,
)
from scpn_z_pinch_core.observability.vocabulary import (
    _COMPATIBLE_CLOCK_KINDS,
    DRIVE_TIMING_CEILING_S,
    ELEMENT_COUNT_BAND,
    IDENTIFIER,
    INSTABILITY_BAND_HZ,
    OBSERVABILITY_CATALOGUE_DIGEST,
    OBSERVABILITY_CATALOGUE_VERSION,
    SHOT_DURATION_CEILING_S,
    ClockKind,
    ObservabilityClass,
    SignalRole,
)


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
