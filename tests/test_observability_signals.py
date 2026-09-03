# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — signals diagnostic tests

"""Signal declarations and the inventory rules a channel imposes on them.

Identity, quantity, unit token and description are each refused separately
so a failure names the field that was wrong.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import pytest

from observability_fixtures import (
    signal_declaration,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError


def test_signal_rejects_malformed_identifier() -> None:
    """A malformed signal identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"signal\.identifier"):
        signal_declaration(identifier="Sig!")


def test_signal_rejects_empty_quantity() -> None:
    """An empty quantity is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"signal\.quantity"):
        signal_declaration(quantity="")


@pytest.mark.parametrize("unit", ["", "m s", "\tA"])
def test_signal_rejects_bad_unit_token(unit: str) -> None:
    """The unit must be a non-empty token without whitespace."""
    with pytest.raises(DiagnosticPlanError, match=r"signal\.unit"):
        signal_declaration(unit=unit)


def test_signal_rejects_empty_description() -> None:
    """An empty description is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"signal\.description"):
        signal_declaration(description="")
