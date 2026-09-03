# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — shared diagnostic and clock test fixtures

"""Shared fixtures for the diagnostic plan and clock semantics tests.

The catalogue bindings, signal inventories, clocks, frames, relations and
channel builders used by more than one surface live here so that each test
module states only what is particular to its own surface.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from typing import Any

from scpn_z_pinch_core.observability import (
    CATALOGUE_BINDING,
    ClockDomain,
    ClockKind,
    ClockModel,
    ClockRelation,
    ClockTopology,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    FrameTransformation,
    ReferenceFrame,
    SemanticCarrier,
    SignalDeclaration,
    SignalRole,
    TransformationKind,
)

DERIVED_BINDINGS = {
    "calibration": "synthetic coil transfer functions",
    "clock_epoch": "clk_facility",
    "mode_identity": "declared instability mode labels",
    "observability_threshold": "declared amplitude floor",
    "observation_operator": "synthetic coil-array projection operator",
    "operator_validation": "operator exercised on synthetic fields",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "reference_signal": "synthetic reference oscillator",
    "uncertainty": "declared amplitude and phase bounds",
    "validity": "synthetic validity window",
}


EVENT_BINDINGS = {
    "clock_epoch": "clk_shot",
    "event_reference": "synthetic current-start marker",
    "provenance": "synthetic fixture",
    "repetition_evidence": "synthetic repeated cycle labels",
    "timing_uncertainty": "declared bound",
    "validity": "synthetic validity window",
}


NUMERICAL_BINDINGS = {
    "initial_condition": "synthetic initial state",
    "model_revision": "model revision identifier",
    "provenance": "synthetic fixture",
    "simulation_clock": "clk_sim",
    "solver_validity": "declared solver validity envelope",
}


REFERENCE_FRAMES = (
    ReferenceFrame(
        identifier="frm_pinch_axis",
        kind=FrameKind.MACHINE_CYLINDRICAL,
        description="pinch-axis cylindrical frame",
    ),
)


CLOCK_RELATIONS = (
    ClockRelation(
        child_identifier="clk_shot",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method=(
            "synthetic declaration: trigger timestamped against the "
            "facility oscillator; no correlation evidence claimed"
        ),
        mapping_state="unmapped",
        evidence_claimed=False,
    ),
)


SIGNALS_CH_CURRENT_VOLTAGE_TRAIN = (
    SignalDeclaration(
        identifier="sig_peak_current",
        quantity="current",
        unit="A",
        role=SignalRole.AMPLITUDE,
        description="synthetic peak discharge current",
    ),
    SignalDeclaration(
        identifier="sig_pulse_cycle",
        quantity="cycle_index",
        unit="1",
        role=SignalRole.CARRIER,
        description="synthetic repeated-cycle label per event",
    ),
    SignalDeclaration(
        identifier="sig_pulse_duration",
        quantity="time",
        unit="s",
        role=SignalRole.AUXILIARY,
        description="synthetic event duration",
    ),
    SignalDeclaration(
        identifier="sig_pulse_onset",
        quantity="time",
        unit="s",
        role=SignalRole.TIMING_MARKER,
        description="synthetic event onset marker",
    ),
)


SIGNALS_CH_PINCH_MODE_ARRAY = (
    SignalDeclaration(
        identifier="sig_mode_amplitude",
        quantity="magnetic_flux_density",
        unit="T",
        role=SignalRole.AMPLITUDE,
        description="synthetic pinch-mode amplitude",
    ),
    SignalDeclaration(
        identifier="sig_mode_number",
        quantity="mode_number",
        unit="1",
        role=SignalRole.AUXILIARY,
        description="declared toroidal or azimuthal mode label",
    ),
    SignalDeclaration(
        identifier="sig_mode_phase",
        quantity="phase",
        unit="rad",
        role=SignalRole.CARRIER,
        description="synthetic mode phase",
    ),
)


SIGNALS_CH_SYNTHETIC_OSCILLATOR = (
    SignalDeclaration(
        identifier="sig_phase",
        quantity="phase",
        unit="rad",
        role=SignalRole.CARRIER,
        description="model-owned synthetic oscillator phase",
    ),
)


REFERENCE_TRANSFORMATIONS: tuple[FrameTransformation, ...] = ()


CLOCK_TOPOLOGY = ClockTopology(
    domains=(
        ClockDomain(
            identifier="dom_facility",
            root_clock_identifier="clk_facility",
            member_clock_identifiers=("clk_facility", "clk_shot"),
            scope="facility master timing and the shot trigger bound to it",
        ),
    ),
    reference_domain_identifier="dom_facility",
)


def clock_facility() -> ClockModel:
    """Build the synthetic facility master clock."""
    return ClockModel(
        identifier="clk_facility",
        kind=ClockKind.FACILITY_MONOTONIC,
        epoch="facility master oscillator zero",
        resolution_s=1.0e-10,
        uncertainty_s=5.0e-11,
    )


def clock_shot() -> ClockModel:
    """Build the synthetic bank-trigger epoch clock."""
    return ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="pulsed-power bank trigger t0",
        resolution_s=1.0e-9,
        uncertainty_s=1.0e-9,
    )


def clock_simulation() -> ClockModel:
    """Build the synthetic simulation clock."""
    return ClockModel(
        identifier="clk_sim",
        kind=ClockKind.SIMULATION,
        epoch="solver step zero",
        resolution_s=1.0e-9,
        uncertainty_s=0.0,
    )


def channel_event_train() -> DiagnosticChannelPlan:
    """Build the synthetic pulsed-power current/voltage event channel."""
    return DiagnosticChannelPlan(
        identifier="ch_current_voltage_train",
        candidate_id="self_magnetic.drive_waveform",
        carrier=SemanticCarrier.EVENT_CYCLE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e08,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=5.0e-09,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.0001,
        element_count=1,
        evidence_bindings=dict(EVENT_BINDINGS),
        signals=SIGNALS_CH_CURRENT_VOLTAGE_TRAIN,
        synthetic=True,
    )


def channel_derived() -> DiagnosticChannelPlan:
    """Build the synthetic pinch-mode probe-array channel."""
    return DiagnosticChannelPlan(
        identifier="ch_pinch_mode_array",
        candidate_id="self_magnetic.resolved_instability_mode",
        carrier=SemanticCarrier.COMPLEX_MODE,
        clock_identifier="clk_facility",
        sample_rate_hz=1.0e08,
        max_signal_frequency_hz=1.0e06,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.0001,
        element_count=16,
        evidence_bindings=dict(DERIVED_BINDINGS),
        signals=SIGNALS_CH_PINCH_MODE_ARRAY,
        synthetic=True,
    )


def channel_oscillator() -> DiagnosticChannelPlan:
    """Build the synthetic model-oscillator channel."""
    return DiagnosticChannelPlan(
        identifier="ch_synthetic_oscillator",
        candidate_id="model.synthetic_oscillator_coordinate",
        carrier=SemanticCarrier.NUMERICAL_PHASE,
        clock_identifier="clk_sim",
        sample_rate_hz=1.0e4,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=1e-05,
        element_count=1,
        evidence_bindings=dict(NUMERICAL_BINDINGS),
        signals=SIGNALS_CH_SYNTHETIC_OSCILLATOR,
        synthetic=True,
    )


def synthetic_plan() -> DiagnosticPlan:
    """Build a fully valid synthetic diagnostic plan."""
    return DiagnosticPlan(
        identifier="z_pinch_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(
            channel_event_train(),
            channel_derived(),
            channel_oscillator(),
        ),
        deferrals=(),
    )


def derived_channel(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the Mirnov channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_pinch_mode_array",
        "candidate_id": "self_magnetic.resolved_instability_mode",
        "carrier": SemanticCarrier.COMPLEX_MODE,
        "clock_identifier": "clk_facility",
        "sample_rate_hz": 1.0e08,
        "max_signal_frequency_hz": 1.0e06,
        "timing_uncertainty_s": None,
        "acquisition_start_s": 0.0,
        "acquisition_duration_s": 0.0001,
        "element_count": 16,
        "evidence_bindings": dict(DERIVED_BINDINGS),
        "signals": SIGNALS_CH_PINCH_MODE_ARRAY,
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def plan_with(**overrides: Any) -> DiagnosticPlan:
    """Rebuild the synthetic plan with keyword overrides applied."""
    plan = synthetic_plan()
    values: dict[str, Any] = {
        "identifier": plan.identifier,
        "binding": plan.binding,
        "clocks": plan.clocks,
        "frames": plan.frames,
        "clock_relations": plan.clock_relations,
        "frame_transformations": plan.frame_transformations,
        "clock_topology": plan.clock_topology,
        "channels": plan.channels,
        "deferrals": plan.deferrals,
    }
    values.update(overrides)
    return DiagnosticPlan(**values)


def signal_declaration(**overrides: Any) -> SignalDeclaration:
    """Build an auxiliary signal with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "sig_zz_extra",
        "quantity": "current",
        "unit": "A",
        "role": SignalRole.AUXILIARY,
        "description": "synthetic auxiliary signal",
    }
    values.update(overrides)
    return SignalDeclaration(**values)


def frame_transformation(**overrides: Any) -> FrameTransformation:
    """Build a transformation with keyword overrides applied."""
    values: dict[str, Any] = {
        "source_identifier": "frm_pinch_axis",
        "target_identifier": "frm_zz_extra",
        "kind": TransformationKind.RIGID,
        "equilibrium_dependent": False,
        "method": "synthetic declaration",
        "evidence_claimed": False,
    }
    values.update(overrides)
    return FrameTransformation(**values)
