# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — native kernel parity tests

"""Bit-exact parity between the Python floor and the native kernels.

The native module is an optional build (rust/, distribution
scpn-z-pinch-native); these tests are skipped hermetically when it is
absent and compare float64 bit patterns, never tolerances, when present.
All parameter sets are synthetic fixtures; none describes a real machine.
"""

from __future__ import annotations

import struct

import pytest

from scpn_z_pinch_core.parameters import Discharge, PinchColumn
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    PROTON_MASS_KG,
    bennett_equilibrium,
    growth_rate_estimate,
    kadomtsev_assessment,
    minimum_stabilising_shear,
    pease_braginskii_current,
)

native = pytest.importorskip("scpn_z_pinch_native")

GRID = [
    (radius, current, density, mass)
    for radius in (5.0e-4, 5.0e-3, 5.0e-2)
    for current in (0.01, 0.1, 1.0, 3.0)
    for density in (1.0e17, 1.0e18, 1.0e20)
    for mass in (PROTON_MASS_KG, DEUTERON_MASS_KG)
]


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


@pytest.mark.parametrize(("radius", "current", "density", "mass"), GRID)
def test_bennett_equilibrium_is_bit_exact(
    radius: float, current: float, density: float, mass: float
) -> None:
    """Every equilibrium quantity agrees bit for bit across the grid."""
    floor = bennett_equilibrium(
        PinchColumn(column_radius_m=radius, column_length_m=0.5),
        Discharge(peak_current_ma=current, ion_line_density_per_m=density),
        mass,
    )
    got = native.bennett_equilibrium(radius, current, density, mass)
    expected = (
        floor.current_a,
        floor.temperature_ev,
        floor.axis_density_per_m3,
        floor.axis_pressure_pa,
        floor.edge_field_t,
        floor.alfven_speed_m_s,
        floor.alfven_transit_time_s,
    )
    assert [bits(value) for value in got] == [bits(value) for value in expected]
    for ratio in (0.0, 0.3, 1.0, 4.0):
        sample = ratio * radius
        assert bits(native.density_at(floor.axis_density_per_m3, radius, sample)) == (
            bits(floor.density_at(sample))
        )
        assert bits(native.field_at(floor.current_a, radius, sample)) == bits(
            floor.field_at(sample)
        )


@pytest.mark.parametrize("wavenumber", [1.0, 200.0, 12_345.678])
def test_stability_and_shear_are_bit_exact(wavenumber: float) -> None:
    """Growth rate, e-folding time and shear threshold agree bit for bit."""
    floor = bennett_equilibrium(
        PinchColumn(column_radius_m=0.005, column_length_m=0.5),
        Discharge(peak_current_ma=0.1, ion_line_density_per_m=1.0e18),
        DEUTERON_MASS_KG,
    )
    estimate = growth_rate_estimate(floor, wavenumber)
    rate, fold = native.growth_rate_estimate(floor.alfven_speed_m_s, wavenumber)
    assert bits(rate) == bits(estimate.growth_rate_per_s)
    assert bits(fold) == bits(estimate.e_folding_time_s)
    assert bits(
        native.minimum_stabilising_shear(floor.alfven_speed_m_s, wavenumber)
    ) == (bits(minimum_stabilising_shear(floor, wavenumber)))


@pytest.mark.parametrize("ratio", [1.0e-3, 0.5, 1.0, 2.0, 1.0e3])
@pytest.mark.parametrize("index", [IDEAL_MONATOMIC_ADIABATIC_INDEX, 2.0, 2.5])
def test_kadomtsev_is_bit_exact(ratio: float, index: float) -> None:
    """Both sides of the criterion and the disposition agree exactly."""
    floor = kadomtsev_assessment(ratio, index)
    exponent, beta, threshold, stable = native.kadomtsev_assessment(ratio, index)
    assert bits(exponent) == bits(floor.profile_exponent)
    assert bits(beta) == bits(floor.local_beta)
    assert bits(threshold) == bits(floor.threshold)
    assert stable is floor.sausage_stable


@pytest.mark.parametrize("coulomb", [5.0, 10.0, 17.3])
@pytest.mark.parametrize("charge", [1.0, 2.0, 6.5])
def test_pease_braginskii_is_bit_exact(coulomb: float, charge: float) -> None:
    """The critical current agrees bit for bit."""
    assert bits(native.pease_braginskii_current(coulomb, charge)) == bits(
        pease_braginskii_current(coulomb, charge)
    )
