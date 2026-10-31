# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — z-pinch parameter model

"""Validated parameter objects of a z-pinch configuration.

The derived quantity implements one standard result and nothing more:
the Bennett-relation temperature ``T = mu0 I^2 / (16 pi N e)`` for equal
ion and electron temperatures (W. H. Bennett, Phys. Rev. 45 (1934)
890). It is a rough consistency instrument with documented applicability
bounds; no claim about any real machine follows from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.errors import DeviceConfigurationError

MU0: Final = 4.0e-7 * math.pi
"""Vacuum permeability in H/m under the pre-2019 SI convention ``4 pi x 10^-7``.

The cited pinch literature uses this value. Since the 2019 SI revision the
permeability is measured: CODATA 2018 gives ``1.25663706212 x 10^-6``, about
``5.4 x 10^-10`` relative above the convention, and CODATA 2022 gives
``1.25663706127 x 10^-6``, about ``1.3 x 10^-10`` below it. Outputs linear in
``mu0`` move by the same relative amount, far below any advisory band here.
"""
ELEMENTARY_CHARGE_C: Final = 1.602176634e-19
"""Elementary charge in coulombs, exact by the 2019 SI definition."""


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


def require_non_negative(name: str, value: float) -> float:
    """Return ``value`` when finite and non-negative.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or negative.
    """
    require_finite(name, value)
    if value < 0.0:
        raise DeviceConfigurationError(f"{name}: must be non-negative, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class PinchColumn:
    """Pinch-column geometry parameters.

    Parameters
    ----------
    column_radius_m
        Pinch-column radius in metres; strictly positive.
    column_length_m
        Pinch-column length in metres; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or not strictly positive.
    """

    column_radius_m: float
    column_length_m: float

    def __post_init__(self) -> None:
        """Validate the column invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or not strictly positive.
        """
        require_positive("column_radius_m", self.column_radius_m)
        require_positive("column_length_m", self.column_length_m)


@dataclass(frozen=True, slots=True)
class Discharge:
    """Discharge parameters of a z-pinch configuration.

    Parameters
    ----------
    peak_current_ma
        Peak pinch current ``I`` in mega-amperes; strictly positive.
    ion_line_density_per_m
        Ion line density ``N`` in inverse metres; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or not strictly positive.
    """

    peak_current_ma: float
    ion_line_density_per_m: float

    def __post_init__(self) -> None:
        """Validate the discharge invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or not strictly positive.
        """
        require_positive("peak_current_ma", self.peak_current_ma)
        require_positive("ion_line_density_per_m", self.ion_line_density_per_m)

    def bennett_temperature_ev(self) -> float:
        """Bennett-relation temperature of the validated discharge.

        Returns
        -------
        float
            ``T = mu0 I^2 / (16 pi N e)`` in electronvolts, assuming
            equal ion and electron temperatures (Bennett, Phys. Rev. 45
            (1934) 890); a consistency instrument, not a performance
            claim.
        """
        current_a = self.peak_current_ma * 1.0e6
        return (
            MU0
            * current_a**2
            / (16.0 * math.pi * self.ion_line_density_per_m * ELEMENTARY_CHARGE_C)
        )
