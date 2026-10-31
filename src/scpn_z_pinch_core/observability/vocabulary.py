# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — diagnostic and clock vocabulary

"""Vocabulary of the diagnostic and clock declarations.

The pinned catalogue identities, the numeric bands every declaration is
checked against, the enumerations of frames, observability classes,
semantic carriers, clocks, signal roles and transformations, and the fixed
admissibility tables that relate them. Nothing here depends on another
part of the observability package.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Final

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
