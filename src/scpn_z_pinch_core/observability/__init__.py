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

This module is the public facade. The declarations live in one module per
responsibility, each importing only the ones before it:

- :mod:`~scpn_z_pinch_core.observability.vocabulary` — pins, bands, enumerations and
  admissibility tables;
- :mod:`~scpn_z_pinch_core.observability.binding` — catalogue binding and candidate
  profiles;
- :mod:`~scpn_z_pinch_core.observability.frames`;
- :mod:`~scpn_z_pinch_core.observability.clocks`;
- :mod:`~scpn_z_pinch_core.observability.signals` — signals, channels and deferrals;
- :mod:`~scpn_z_pinch_core.observability.plan` — the whole plan;
- :mod:`~scpn_z_pinch_core.observability.records` — strict parsing.

Import from this facade; the module layout is not a public contract.
"""

from __future__ import annotations

from scpn_z_pinch_core.observability.binding import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    CandidateProfile,
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
from scpn_z_pinch_core.observability.records import (
    plan_from_bytes,
    plan_from_record,
)
from scpn_z_pinch_core.observability.signals import (
    DeferredCandidate,
    DiagnosticChannelPlan,
    SignalDeclaration,
)
from scpn_z_pinch_core.observability.vocabulary import (
    ALLOWED_FRAME_KINDS,
    DRIVE_TIMING_CEILING_S,
    ELEMENT_COUNT_BAND,
    HEX_DIGEST,
    IDENTIFIER,
    INSTABILITY_BAND_HZ,
    OBSERVABILITY_CATALOGUE_DIGEST,
    OBSERVABILITY_CATALOGUE_VERSION,
    OWNED_CONFIGURATIONS,
    REACTOR_REGISTRY_DIGEST,
    REACTOR_REGISTRY_VERSION,
    SHOT_DURATION_CEILING_S,
    ClockKind,
    FrameKind,
    ObservabilityClass,
    SemanticCarrier,
    SignalRole,
    TransformationKind,
)

__all__ = [
    "ALLOWED_FRAME_KINDS",
    "APPLICABLE_CANDIDATES",
    "CATALOGUE_BINDING",
    "DRIVE_TIMING_CEILING_S",
    "ELEMENT_COUNT_BAND",
    "HEX_DIGEST",
    "IDENTIFIER",
    "INSTABILITY_BAND_HZ",
    "OBSERVABILITY_CATALOGUE_DIGEST",
    "OBSERVABILITY_CATALOGUE_VERSION",
    "OWNED_CONFIGURATIONS",
    "REACTOR_REGISTRY_DIGEST",
    "REACTOR_REGISTRY_VERSION",
    "SHOT_DURATION_CEILING_S",
    "CandidateProfile",
    "ClockDomain",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ClockTopology",
    "DeferredCandidate",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "FrameKind",
    "FrameTransformation",
    "ObservabilityBinding",
    "ObservabilityClass",
    "ReferenceFrame",
    "SemanticCarrier",
    "SignalDeclaration",
    "SignalRole",
    "TransformationKind",
    "plan_from_bytes",
    "plan_from_record",
]
