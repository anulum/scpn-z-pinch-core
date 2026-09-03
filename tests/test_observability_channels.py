# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — channels diagnostic tests

"""Diagnostic channel plans: identity, carrier, sampling and evidence.

Sampling is checked against the declared signal frequency, the clock
binding against the declared clock, and the evidence keys against the
binding they name.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import dataclasses

import pytest

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    DERIVED_BINDINGS,
    EVENT_BINDINGS,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    SIGNALS_CH_CURRENT_VOLTAGE_TRAIN,
    SIGNALS_CH_PINCH_MODE_ARRAY,
    SIGNALS_CH_SYNTHETIC_OSCILLATOR,
    channel_derived,
    channel_event_train,
    channel_oscillator,
    clock_facility,
    clock_shot,
    clock_simulation,
    derived_channel,
    signal_declaration,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    CATALOGUE_BINDING,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    ObservabilityClass,
    SemanticCarrier,
    SignalDeclaration,
    SignalRole,
)


def test_channel_rejects_empty_signal_inventory() -> None:
    """A channel must declare at least one signal."""
    with pytest.raises(DiagnosticPlanError, match="at least one signal"):
        derived_channel(signals=())


def test_channel_rejects_unsorted_or_duplicate_signals() -> None:
    """Signal identifiers must be unique and sorted."""
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        derived_channel(signals=tuple(reversed(SIGNALS_CH_PINCH_MODE_ARRAY)))
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        derived_channel(
            signals=(*SIGNALS_CH_PINCH_MODE_ARRAY, SIGNALS_CH_PINCH_MODE_ARRAY[-1])
        )


@pytest.mark.parametrize("count", [0, 2])
def test_channel_requires_exactly_one_carrier_signal(count: int) -> None:
    """Exactly one carrier signal is required."""
    carriers = tuple(
        signal_declaration(
            identifier=f"sig_zz_carrier_{index}", role=SignalRole.CARRIER
        )
        for index in range(count)
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one carrier"):
        derived_channel(signals=(signal_declaration(identifier="sig_aa"), *carriers))


def test_non_event_channel_rejects_timing_marker() -> None:
    """Only event-relative channels declare a timing marker."""
    marker = signal_declaration(
        identifier="sig_zz_marker", unit="s", role=SignalRole.TIMING_MARKER
    )
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        derived_channel(signals=(*SIGNALS_CH_PINCH_MODE_ARRAY, marker))


@pytest.mark.parametrize(
    "signals",
    [
        (
            SIGNALS_CH_SYNTHETIC_OSCILLATOR[0],
            signal_declaration(identifier="sig_zz_extra"),
        ),
        (
            signal_declaration(
                identifier="sig_phase",
                quantity="angle",
                unit="rad",
                role=SignalRole.CARRIER,
            ),
        ),
        (
            signal_declaration(
                identifier="sig_phase",
                quantity="phase",
                unit="deg",
                role=SignalRole.CARRIER,
            ),
        ),
    ],
)
def test_numerical_channel_declares_single_phase_carrier(
    signals: tuple[SignalDeclaration, ...],
) -> None:
    """Numerical-only channels declare exactly one phase carrier in radians."""
    with pytest.raises(DiagnosticPlanError, match="numerical-only"):
        dataclasses.replace(channel_oscillator(), signals=signals)


def test_event_channel_requires_exactly_one_timing_marker() -> None:
    """Event-relative channels declare exactly one timing marker."""
    reference = channel_event_train()
    without_marker = tuple(
        signal
        for signal in reference.signals
        if signal.role is not SignalRole.TIMING_MARKER
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one timing_marker"):
        dataclasses.replace(reference, signals=without_marker)
    doubled = tuple(
        sorted(
            (
                *reference.signals,
                signal_declaration(
                    identifier="sig_zz_onset", unit="s", role=SignalRole.TIMING_MARKER
                ),
            ),
            key=lambda signal: signal.identifier,
        )
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one timing_marker"):
        dataclasses.replace(reference, signals=doubled)


def test_event_channel_timing_marker_must_be_in_seconds() -> None:
    """The timing marker is declared in seconds."""
    reference = channel_event_train()
    signals = tuple(
        dataclasses.replace(signal, unit="ms")
        if signal.role is SignalRole.TIMING_MARKER
        else signal
        for signal in reference.signals
    )
    with pytest.raises(DiagnosticPlanError, match="seconds"):
        dataclasses.replace(reference, signals=signals)


def test_channel_rejects_malformed_identifier() -> None:
    """A malformed channel identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"channel\.identifier"):
        derived_channel(identifier="Channel!")


def test_channel_rejects_unknown_candidate() -> None:
    """A candidate outside the embedded subset is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not applicable"):
        derived_channel(candidate_id="closed.resolved_mhd_mode")


def test_channel_rejects_inadmissible_carrier() -> None:
    """A carrier outside the class table is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not admissible"):
        derived_channel(carrier=SemanticCarrier.EVENT_CYCLE)


def test_channel_rejects_malformed_clock_identifier() -> None:
    """A malformed clock reference is rejected."""
    with pytest.raises(DiagnosticPlanError, match="clock_identifier"):
        derived_channel(clock_identifier="Clock!")


@pytest.mark.parametrize("rate", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_sample_rate(rate: float) -> None:
    """Non-positive or non-finite sampling rates are rejected."""
    with pytest.raises(DiagnosticPlanError, match="sample_rate_hz"):
        derived_channel(sample_rate_hz=rate)


@pytest.mark.parametrize("frequency", [-1.0, float("inf")])
def test_channel_rejects_bad_signal_frequency(frequency: float) -> None:
    """Negative or non-finite signal frequencies are rejected."""
    with pytest.raises(DiagnosticPlanError, match="max_signal_frequency_hz"):
        derived_channel(max_signal_frequency_hz=frequency)


def test_channel_rejects_cyclic_zero_band() -> None:
    """A cyclic channel must declare a positive signal band."""
    with pytest.raises(DiagnosticPlanError, match="positive signal band"):
        derived_channel(max_signal_frequency_hz=0.0)


def test_channel_rejects_nyquist_violation() -> None:
    """Sampling below twice the signal band is rejected."""
    with pytest.raises(DiagnosticPlanError, match="Nyquist"):
        derived_channel(sample_rate_hz=5.0e05)


@pytest.mark.parametrize("timing", [None, 0.0, -1.0e-6, float("nan")])
def test_event_channel_requires_timing_uncertainty(timing: float | None) -> None:
    """Event-relative channels must declare a positive timing bound."""
    bindings = dict(EVENT_BINDINGS)
    with pytest.raises(DiagnosticPlanError, match="timing_uncertainty_s"):
        DiagnosticChannelPlan(
            identifier="ch_current_voltage_train",
            candidate_id="self_magnetic.drive_waveform",
            carrier=SemanticCarrier.EVENT_CYCLE,
            clock_identifier="clk_shot",
            sample_rate_hz=1.0e08,
            max_signal_frequency_hz=0.0,
            timing_uncertainty_s=timing,
            acquisition_start_s=0.0,
            acquisition_duration_s=0.0001,
            element_count=1,
            evidence_bindings=bindings,
            signals=SIGNALS_CH_CURRENT_VOLTAGE_TRAIN,
            synthetic=True,
        )


def test_non_event_channel_rejects_timing_uncertainty() -> None:
    """Only event-relative channels declare a timing uncertainty."""
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        derived_channel(timing_uncertainty_s=1.0e-5)


def test_channel_rejects_evidence_key_mismatch() -> None:
    """Missing and extra evidence slots are both rejected."""
    bindings = dict(DERIVED_BINDINGS)
    del bindings["mode_identity"]
    bindings["surprise"] = "x"
    with pytest.raises(DiagnosticPlanError, match=r"missing=.*extra="):
        derived_channel(evidence_bindings=bindings)


def test_channel_rejects_empty_evidence_statement() -> None:
    """An empty evidence statement is rejected."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["quality"] = ""
    with pytest.raises(DiagnosticPlanError, match="quality"):
        derived_channel(evidence_bindings=bindings)


def test_channel_rejects_clock_binding_mismatch() -> None:
    """The clock evidence slot must reference the bound clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_other"
    with pytest.raises(DiagnosticPlanError, match="must reference the bound clock"):
        derived_channel(evidence_bindings=bindings)


def test_channel_rejects_non_synthetic() -> None:
    """No channel in this repository may claim to be real."""
    with pytest.raises(DiagnosticPlanError, match="synthetic"):
        derived_channel(synthetic=False)


def test_channel_exposes_observability_class() -> None:
    """The class property resolves through the embedded catalogue."""
    assert channel_derived().observability_class is ObservabilityClass.DERIVED_CYCLIC


def test_plan_rejects_unsorted_channels() -> None:
    """Channels must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.channels"):
        DiagnosticPlan(
            identifier="z_pinch_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_derived(),
                channel_event_train(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


@pytest.mark.parametrize("start", [float("nan"), float("inf")])
def test_channel_rejects_bad_acquisition_start(start: float) -> None:
    """A non-finite acquisition start is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_start_s"):
        derived_channel(acquisition_start_s=start)


@pytest.mark.parametrize("duration", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_acquisition_duration(duration: float) -> None:
    """A non-positive acquisition duration is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_duration_s"):
        derived_channel(acquisition_duration_s=duration)


@pytest.mark.parametrize("count", [0, -3, True])
def test_channel_rejects_bad_element_count(count: object) -> None:
    """A non-integer or sub-unit element count is rejected."""
    with pytest.raises(DiagnosticPlanError, match="element_count"):
        derived_channel(element_count=count)
