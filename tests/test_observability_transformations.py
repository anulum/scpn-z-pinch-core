# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — transformations diagnostic tests

"""Frame transformations and the plan rules that govern them.

Ordering, duplication, undeclared targets and inadmissible kinds are
each refused, as is a transformation that claims evidence it does not carry.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import pytest

from observability_fixtures import (
    frame_transformation,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import TransformationKind


@pytest.mark.parametrize("field", ["source_identifier", "target_identifier"])
def test_transformation_rejects_malformed_identifier(field: str) -> None:
    """Malformed frame identifiers are rejected."""
    with pytest.raises(DiagnosticPlanError, match=rf"transformation\.{field}"):
        frame_transformation(**{field: "Frame!"})


def test_transformation_rejects_self_mapping() -> None:
    """A frame cannot be transformed to itself."""
    with pytest.raises(DiagnosticPlanError, match="to itself"):
        frame_transformation(target_identifier="frm_pinch_axis")


@pytest.mark.parametrize(
    ("kind", "dependent"),
    [
        (TransformationKind.FLUX_MAPPING, False),
        (TransformationKind.RIGID, True),
        (TransformationKind.PROJECTION, True),
    ],
)
def test_transformation_rejects_equilibrium_flag_mismatch(
    kind: TransformationKind, dependent: bool
) -> None:
    """Only flux mappings depend on an equilibrium reconstruction."""
    with pytest.raises(DiagnosticPlanError, match="equilibrium_dependent"):
        frame_transformation(kind=kind, equilibrium_dependent=dependent)


def test_transformation_rejects_empty_method() -> None:
    """An empty method statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"transformation\.method"):
        frame_transformation(method="")


def test_transformation_rejects_claimed_evidence() -> None:
    """No mapping evidence may be claimed."""
    with pytest.raises(DiagnosticPlanError, match="evidence_claimed"):
        frame_transformation(evidence_claimed=True)
