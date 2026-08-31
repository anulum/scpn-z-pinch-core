# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — parameter model tests

"""Every validation branch of the z-pinch parameter model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import (
    ELEMENTARY_CHARGE_C,
    MU0,
    Discharge,
    PinchColumn,
    require_finite,
    require_positive,
)


def synthetic_column(**overrides: float) -> PinchColumn:
    """Build a valid synthetic pinch column with optional overrides."""
    values: dict[str, float] = {"column_radius_m": 0.005, "column_length_m": 0.5}
    values.update(overrides)
    return PinchColumn(**values)


def synthetic_discharge(**overrides: float) -> Discharge:
    """Build a valid synthetic discharge with optional overrides."""
    values: dict[str, float] = {
        "peak_current_ma": 0.1,
        "ion_line_density_per_m": 1.0e18,
    }
    values.update(overrides)
    return Discharge(**values)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


def test_valid_column_constructs() -> None:
    """A valid pinch column constructs unchanged."""
    assert synthetic_column().column_radius_m == 0.005


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"column_radius_m": 0.0}, "column_radius_m"),
        ({"column_length_m": -1.0}, "column_length_m"),
        ({"column_radius_m": math.nan}, "column_radius_m"),
    ],
)
def test_invalid_column_is_rejected(overrides: dict[str, float], fragment: str) -> None:
    """Each column violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_column(**overrides)


def test_bennett_temperature_formula() -> None:
    """The Bennett temperature follows the cited relation exactly."""
    discharge = synthetic_discharge()
    expected = MU0 * (0.1e6) ** 2 / (16.0 * math.pi * 1.0e18 * ELEMENTARY_CHARGE_C)
    assert discharge.bennett_temperature_ev() == pytest.approx(expected)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"peak_current_ma": 0.0}, "peak_current_ma"),
        ({"ion_line_density_per_m": -1.0}, "ion_line_density_per_m"),
        ({"ion_line_density_per_m": math.inf}, "ion_line_density_per_m"),
    ],
)
def test_invalid_discharge_is_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each discharge violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_discharge(**overrides)
