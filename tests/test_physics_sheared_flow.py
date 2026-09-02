# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — sheared-flow criterion tests

"""Shumlak-Hartman threshold and disposition for declared shears.

All parameter sets are synthetic fixtures; none describes a real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import Discharge, PinchColumn
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    SHUMLAK_HARTMAN_COEFFICIENT,
    bennett_equilibrium,
    minimum_stabilising_shear,
    shear_assessment,
)

EQUILIBRIUM = bennett_equilibrium(
    PinchColumn(column_radius_m=0.005, column_length_m=0.5),
    Discharge(peak_current_ma=0.1, ion_line_density_per_m=1.0e18),
    DEUTERON_MASS_KG,
)


def test_threshold_is_one_tenth_k_alfven() -> None:
    """The published threshold form 0.1 k v_A is evaluated exactly."""
    assert SHUMLAK_HARTMAN_COEFFICIENT == 0.1
    assert minimum_stabilising_shear(EQUILIBRIUM, 200.0) == (
        0.1 * 200.0 * EQUILIBRIUM.alfven_speed_m_s
    )


def test_disposition_flips_exactly_at_the_threshold() -> None:
    """Shear above the threshold stabilises; at or below it does not."""
    minimum = minimum_stabilising_shear(EQUILIBRIUM, 200.0)
    above = shear_assessment(EQUILIBRIUM, 200.0, math.nextafter(minimum, math.inf))
    at = shear_assessment(EQUILIBRIUM, 200.0, minimum)
    static = shear_assessment(EQUILIBRIUM, 200.0, 0.0)
    assert above.kink_stabilised is True
    assert at.kink_stabilised is False
    assert static.kink_stabilised is False
    assert at.minimum_shear_per_s == minimum
    assert at.declared_shear_per_s == minimum
    assert at.alfven_speed_m_s == EQUILIBRIUM.alfven_speed_m_s
    assert set(at.to_record()) == {
        "axial_wavenumber_per_m",
        "alfven_speed_m_s",
        "minimum_shear_per_s",
        "declared_shear_per_s",
        "kink_stabilised",
    }


def test_threshold_scales_with_wavenumber() -> None:
    """Longer wavelengths need less shear."""
    assert minimum_stabilising_shear(EQUILIBRIUM, 50.0) == pytest.approx(
        0.25 * minimum_stabilising_shear(EQUILIBRIUM, 200.0)
    )


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan])
def test_invalid_wavenumber_is_rejected(bad: float) -> None:
    """Non-positive or non-finite wavenumbers are rejected."""
    with pytest.raises(DeviceConfigurationError, match="axial_wavenumber_per_m"):
        shear_assessment(EQUILIBRIUM, bad, 1.0e6)


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf])
def test_negative_or_non_finite_shear_is_rejected(bad: float) -> None:
    """A negative or non-finite declared shear is rejected."""
    with pytest.raises(DeviceConfigurationError, match="declared_shear_per_s"):
        shear_assessment(EQUILIBRIUM, 200.0, bad)
