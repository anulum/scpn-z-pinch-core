# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — frames diagnostic tests

"""Reference frames and the plan rules that keep the frame set connected.

A single-frame plan needs no transformation; a multi-frame plan that
leaves a frame unreachable is refused.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import pytest

from observability_fixtures import (
    CLOCK_TOPOLOGY,
    REFERENCE_TRANSFORMATIONS,
    synthetic_plan,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    DiagnosticPlan,
    FrameKind,
    ReferenceFrame,
)


def test_frame_rejects_disallowed_kind() -> None:
    """A frame kind outside the repository's allowed set is rejected."""
    with pytest.raises(DiagnosticPlanError, match="allowed frame"):
        ReferenceFrame(
            identifier="frm_bad",
            kind=FrameKind.FLUX_SURFACE,
            description="x",
        )


def test_frame_rejects_malformed_identifier() -> None:
    """A malformed frame identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"frame\.identifier"):
        ReferenceFrame(
            identifier="Frame!",
            kind=FrameKind.MACHINE_CYLINDRICAL,
            description="x",
        )


def test_frame_rejects_empty_description() -> None:
    """An empty frame description is rejected."""
    with pytest.raises(DiagnosticPlanError, match="description"):
        ReferenceFrame(
            identifier="frm_ok",
            kind=FrameKind.MACHINE_CYLINDRICAL,
            description="",
        )


def test_plan_rejects_duplicate_frames() -> None:
    """Duplicate frame identifiers are rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match=r"plan\.frames"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=(*plan.frames, plan.frames[0]),
            clock_relations=plan.clock_relations,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )
