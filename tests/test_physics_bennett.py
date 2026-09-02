# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Bennett equilibrium tests

"""Analytic identities, scaling and refusal branches of the Bennett model.

All parameter sets are synthetic fixtures; none describes a real machine.
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
)
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    PROTON_MASS_KG,
    BennettEquilibrium,
    bennett_equilibrium,
)

COLUMN = PinchColumn(column_radius_m=0.005, column_length_m=0.5)
DISCHARGE = Discharge(peak_current_ma=0.1, ion_line_density_per_m=1.0e18)


def synthetic_equilibrium(ion_mass_kg: float = DEUTERON_MASS_KG) -> BennettEquilibrium:
    """Build the reference synthetic Bennett equilibrium."""
    return bennett_equilibrium(COLUMN, DISCHARGE, ion_mass_kg)


def test_temperature_equals_the_discharge_instrument() -> None:
    """The model temperature is the discharge's Bennett temperature, exactly."""
    assert synthetic_equilibrium().temperature_ev == DISCHARGE.bennett_temperature_ev()


def test_pressure_balance_closes_to_machine_precision() -> None:
    """On-axis pressure equals 2 B_theta(a)^2 / mu0 for the Bennett profile."""
    equilibrium = synthetic_equilibrium()
    magnetic = 2.0 * equilibrium.edge_field_t**2 / MU0
    assert equilibrium.axis_pressure_pa == pytest.approx(magnetic, rel=1e-15)


def test_integral_pressure_balance_bennett_condition() -> None:
    """mu0 I^2 / (8 pi) = 2 N k T holds for the equal-temperature model."""
    equilibrium = synthetic_equilibrium()
    left = MU0 * equilibrium.current_a**2 / (8.0 * math.pi)
    right = (
        2.0
        * equilibrium.line_density_per_m
        * equilibrium.temperature_ev
        * ELEMENTARY_CHARGE_C
    )
    assert left == pytest.approx(right, rel=1e-15)


def test_density_profile_integrates_to_the_line_density() -> None:
    """2 pi int n(r) r dr over the plane recovers N (midpoint rule)."""
    equilibrium = synthetic_equilibrium()
    scale = equilibrium.scale_radius_m
    total = 0.0
    steps = 200_000
    outer = 400.0 * scale
    width = outer / steps
    for index in range(steps):
        radius = (index + 0.5) * width
        total += 2.0 * math.pi * equilibrium.density_at(radius) * radius * width
    assert total == pytest.approx(equilibrium.line_density_per_m, rel=1e-5)


def test_field_and_enclosed_current_are_consistent() -> None:
    """B_theta(r) = mu0 I(r) / (2 pi r) at every sampled radius."""
    equilibrium = synthetic_equilibrium()
    for ratio in (0.1, 0.5, 1.0, 2.0, 10.0):
        radius = ratio * equilibrium.scale_radius_m
        expected = (
            MU0 * equilibrium.enclosed_current_at(radius) / (2.0 * math.pi * radius)
        )
        assert equilibrium.field_at(radius) == pytest.approx(expected, rel=1e-15)
    assert equilibrium.field_at(equilibrium.scale_radius_m) == pytest.approx(
        equilibrium.edge_field_t, rel=1e-15
    )
    assert equilibrium.field_at(0.0) == 0.0
    assert equilibrium.enclosed_current_at(0.0) == 0.0


def test_profile_values_on_axis_and_at_the_scale_radius() -> None:
    """The profile is n_0 on axis and n_0 / 4 at r = a."""
    equilibrium = synthetic_equilibrium()
    assert equilibrium.density_at(0.0) == equilibrium.axis_density_per_m3
    assert equilibrium.pressure_at(0.0) == equilibrium.axis_pressure_pa
    assert equilibrium.density_at(equilibrium.scale_radius_m) == pytest.approx(
        equilibrium.axis_density_per_m3 / 4.0
    )
    assert equilibrium.pressure_at(equilibrium.scale_radius_m) == pytest.approx(
        equilibrium.axis_pressure_pa / 4.0
    )


def test_alfven_quantities_follow_their_definitions() -> None:
    """v_A = B / sqrt(mu0 n_0 m_i) and tau_A = a / v_A."""
    equilibrium = synthetic_equilibrium()
    density = equilibrium.axis_density_per_m3 * DEUTERON_MASS_KG
    assert equilibrium.alfven_speed_m_s == pytest.approx(
        equilibrium.edge_field_t / math.sqrt(MU0 * density), rel=1e-15
    )
    assert equilibrium.alfven_transit_time_s == pytest.approx(
        equilibrium.scale_radius_m / equilibrium.alfven_speed_m_s, rel=1e-15
    )


def test_temperature_scales_with_current_squared_and_inverse_line_density() -> None:
    """Doubling the current quadruples T; doubling N halves it."""
    base = synthetic_equilibrium()
    hotter = bennett_equilibrium(
        COLUMN,
        Discharge(peak_current_ma=0.2, ion_line_density_per_m=1.0e18),
        PROTON_MASS_KG,
    )
    denser = bennett_equilibrium(
        COLUMN,
        Discharge(peak_current_ma=0.1, ion_line_density_per_m=2.0e18),
        PROTON_MASS_KG,
    )
    assert hotter.temperature_ev == pytest.approx(4.0 * base.temperature_ev)
    assert denser.temperature_ev == pytest.approx(0.5 * base.temperature_ev)


def test_lighter_ions_raise_the_alfven_speed() -> None:
    """v_A scales as the inverse square root of the ion mass."""
    proton = synthetic_equilibrium(PROTON_MASS_KG)
    deuteron = synthetic_equilibrium(DEUTERON_MASS_KG)
    assert proton.alfven_speed_m_s == pytest.approx(
        deuteron.alfven_speed_m_s * math.sqrt(DEUTERON_MASS_KG / PROTON_MASS_KG)
    )


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf])
def test_invalid_ion_mass_is_rejected(bad: float) -> None:
    """Non-positive or non-finite ion masses are rejected, never clamped."""
    with pytest.raises(DeviceConfigurationError, match="ion_mass_kg"):
        bennett_equilibrium(COLUMN, DISCHARGE, bad)


@pytest.mark.parametrize("bad", [-1.0e-9, math.nan, -math.inf])
def test_negative_or_non_finite_radius_is_rejected(bad: float) -> None:
    """Every profile accessor refuses a negative or non-finite radius."""
    equilibrium = synthetic_equilibrium()
    for accessor in (
        equilibrium.density_at,
        equilibrium.pressure_at,
        equilibrium.field_at,
        equilibrium.enclosed_current_at,
    ):
        with pytest.raises(DeviceConfigurationError, match="radius_m"):
            accessor(bad)


def test_record_carries_every_field() -> None:
    """The record names every equilibrium field with its SI suffix."""
    record = synthetic_equilibrium().to_record()
    assert set(record) == {
        "scale_radius_m",
        "current_a",
        "line_density_per_m",
        "ion_mass_kg",
        "temperature_ev",
        "axis_density_per_m3",
        "axis_pressure_pa",
        "edge_field_t",
        "alfven_speed_m_s",
        "alfven_transit_time_s",
    }
    assert record["current_a"] == 1.0e5
