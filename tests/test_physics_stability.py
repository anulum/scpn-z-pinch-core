# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — ideal-MHD stability estimate tests

"""Growth-rate estimate and Kadomtsev criterion on the Bennett profile.

All parameter sets are synthetic fixtures; none describes a real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import Discharge, PinchColumn
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    bennett_equilibrium,
    growth_rate_estimate,
    kadomtsev_assessment,
)

EQUILIBRIUM = bennett_equilibrium(
    PinchColumn(column_radius_m=0.005, column_length_m=0.5),
    Discharge(peak_current_ma=0.1, ion_line_density_per_m=1.0e18),
    DEUTERON_MASS_KG,
)


def test_growth_rate_is_k_times_alfven_speed() -> None:
    """The rate is ``k v_A`` and the e-folding time is its inverse."""
    estimate = growth_rate_estimate(EQUILIBRIUM, 200.0)
    assert estimate.growth_rate_per_s == 200.0 * EQUILIBRIUM.alfven_speed_m_s
    assert estimate.e_folding_time_s == 1.0 / estimate.growth_rate_per_s
    assert estimate.alfven_speed_m_s == EQUILIBRIUM.alfven_speed_m_s
    assert set(estimate.to_record()) == {
        "axial_wavenumber_per_m",
        "alfven_speed_m_s",
        "growth_rate_per_s",
        "e_folding_time_s",
    }


def test_growth_rate_scales_linearly_with_wavenumber() -> None:
    """Doubling k doubles the estimate."""
    one = growth_rate_estimate(EQUILIBRIUM, 100.0)
    two = growth_rate_estimate(EQUILIBRIUM, 200.0)
    assert two.growth_rate_per_s == pytest.approx(2.0 * one.growth_rate_per_s)


def test_e_folding_at_scale_wavenumber_equals_alfven_transit() -> None:
    """For k = 1 / a the e-folding time is the Alfven transit time."""
    estimate = growth_rate_estimate(EQUILIBRIUM, 1.0 / EQUILIBRIUM.scale_radius_m)
    assert estimate.e_folding_time_s == pytest.approx(
        EQUILIBRIUM.alfven_transit_time_s, rel=1e-15
    )


@pytest.mark.parametrize("bad", [0.0, -5.0, math.nan, math.inf])
def test_invalid_wavenumber_is_rejected(bad: float) -> None:
    """Non-positive or non-finite wavenumbers are rejected."""
    with pytest.raises(DeviceConfigurationError, match="axial_wavenumber_per_m"):
        growth_rate_estimate(EQUILIBRIUM, bad)


def test_kadomtsev_closed_forms_on_the_bennett_profile() -> None:
    """Profile exponent 4x^2/(1+x^2) and beta = 1/x^2 at x = 1."""
    assessment = kadomtsev_assessment(1.0, IDEAL_MONATOMIC_ADIABATIC_INDEX)
    assert assessment.profile_exponent == 2.0
    assert assessment.local_beta == 1.0
    assert assessment.threshold == pytest.approx(4.0 * (5.0 / 3.0) / (2.0 + 5.0 / 3.0))
    assert assessment.sausage_stable is False
    assert set(assessment.to_record()) == {
        "radius_ratio",
        "adiabatic_index",
        "profile_exponent",
        "local_beta",
        "threshold",
        "sausage_stable",
    }


@pytest.mark.parametrize("ratio", [1.0e-3, 0.1, 0.5, 1.0, 2.0, 10.0, 1.0e3])
def test_bennett_profile_is_sausage_unstable_everywhere_for_five_thirds(
    ratio: float,
) -> None:
    """The published conclusion: unstable at every radius for gamma_ad = 5/3."""
    assert kadomtsev_assessment(
        ratio, IDEAL_MONATOMIC_ADIABATIC_INDEX
    ).sausage_stable is (False)


@pytest.mark.parametrize("ratio", [0.1, 1.0, 10.0])
def test_criterion_reduces_to_two_below_adiabatic_index(ratio: float) -> None:
    """The reduced criterion 2 < gamma_ad flips exactly above two."""
    assert kadomtsev_assessment(ratio, 2.5).sausage_stable is True
    assert kadomtsev_assessment(ratio, 2.0).sausage_stable is False


def test_profile_exponent_tends_to_four_far_outside() -> None:
    """-d ln p / d ln r approaches four for r >> a."""
    assert kadomtsev_assessment(1.0e4, 5.0 / 3.0).profile_exponent == pytest.approx(
        4.0, rel=1e-7
    )


@pytest.mark.parametrize(
    ("ratio", "index", "fragment"),
    [
        (0.0, 5.0 / 3.0, "radius_ratio"),
        (-1.0, 5.0 / 3.0, "radius_ratio"),
        (math.nan, 5.0 / 3.0, "radius_ratio"),
        (1.0, 0.0, "adiabatic_index"),
        (1.0, math.inf, "adiabatic_index"),
    ],
)
def test_invalid_kadomtsev_inputs_are_rejected(
    ratio: float, index: float, fragment: str
) -> None:
    """Each invalid criterion input is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        kadomtsev_assessment(ratio, index)
