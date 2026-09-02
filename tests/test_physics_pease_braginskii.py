# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Pease-Braginskii current tests

"""Published reference value, scaling and refusal branches of I_PB.

All parameter sets are synthetic fixtures; none describes a real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import ELEMENTARY_CHARGE_C, MU0
from scpn_z_pinch_core.physics import (
    BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12,
    SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32,
    pease_braginskii_assessment,
    pease_braginskii_current,
)


def test_coefficients_are_the_formulary_values_in_si() -> None:
    """The SI coefficients are the NRL formulary numbers with T in joules."""
    assert (
        pytest.approx(1.0 / (1.03e-4 * ELEMENTARY_CHARGE_C**1.5))
        == SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32
    )
    assert (
        pytest.approx(1.69e-38 / math.sqrt(ELEMENTARY_CHARGE_C))
        == BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12
    )


def test_hydrogenic_reference_value_is_about_one_point_four_megaampere() -> None:
    """Hydrogenic z = 1 at ln Lambda = 10 gives the quoted 1.4 MA within 3 %."""
    current = pease_braginskii_current(10.0, 1.0)
    assert current == pytest.approx(1.4e6, rel=0.03)
    assert current == pytest.approx(1.3701757e6, rel=1e-6)


def test_published_closed_form_is_evaluated_exactly() -> None:
    """(pi / mu0) sqrt(48 ln L / (sigma_0 A)) (1 + z) / z term by term."""
    expected = (
        (math.pi / MU0)
        * math.sqrt(
            48.0
            * 7.0
            / (
                SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32
                * BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12
            )
        )
        * (1.0 + 2.0)
        / 2.0
    )
    assert pease_braginskii_current(7.0, 2.0) == expected


def test_current_scales_with_root_coulomb_logarithm() -> None:
    """I_PB^2 is proportional to ln Lambda."""
    assert pease_braginskii_current(40.0, 1.0) == pytest.approx(
        2.0 * pease_braginskii_current(10.0, 1.0)
    )


def test_regime_labels_both_sides_of_the_critical_current() -> None:
    """The ratio and label follow the configured current."""
    critical = pease_braginskii_current(10.0, 1.0)
    below = pease_braginskii_assessment(1.0e5, 10.0, 1.0)
    at = pease_braginskii_assessment(critical, 10.0, 1.0)
    above = pease_braginskii_assessment(2.0 * critical, 10.0, 1.0)
    assert below.regime == "below_pease_braginskii"
    assert below.current_ratio == pytest.approx(1.0e5 / critical)
    assert at.regime == "at_or_above_pease_braginskii"
    assert at.current_ratio == 1.0
    assert above.regime == "at_or_above_pease_braginskii"
    assert above.pease_braginskii_current_a == critical
    assert set(above.to_record()) == {
        "coulomb_logarithm",
        "mean_ion_charge",
        "pease_braginskii_current_a",
        "current_a",
        "current_ratio",
        "regime",
    }


@pytest.mark.parametrize(
    ("current", "coulomb", "charge", "fragment"),
    [
        (0.0, 10.0, 1.0, "current_a"),
        (math.nan, 10.0, 1.0, "current_a"),
        (1.0e5, 0.0, 1.0, "coulomb_logarithm"),
        (1.0e5, -3.0, 1.0, "coulomb_logarithm"),
        (1.0e5, 10.0, 0.0, "mean_ion_charge"),
        (1.0e5, 10.0, math.inf, "mean_ion_charge"),
    ],
)
def test_invalid_inputs_are_rejected(
    current: float, coulomb: float, charge: float, fragment: str
) -> None:
    """Each invalid input is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        pease_braginskii_assessment(current, coulomb, charge)
