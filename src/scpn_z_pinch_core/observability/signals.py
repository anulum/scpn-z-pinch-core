# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — signal and channel declarations

"""Signal and diagnostic-channel declarations.

:class:`SignalDeclaration` declares one signal of a channel,
:class:`DiagnosticChannelPlan` one synthetic, review-only, non-actuating
channel bound to a candidate profile, and :class:`DeferredCandidate` a
candidate the plan deliberately leaves unbound with its reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.binding import (
    _CANDIDATE_INDEX,
)
from scpn_z_pinch_core.observability.vocabulary import (
    _CLOCK_KEY,
    _CYCLIC_CLASSES,
    IDENTIFIER,
    ObservabilityClass,
    SemanticCarrier,
    SignalRole,
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
