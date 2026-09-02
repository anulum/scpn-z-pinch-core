# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Bennett equilibrium model

"""Bennett equilibrium of a z-pinch column (level-0 device physics).

The model is the classical Bennett pinch (W. H. Bennett, Phys. Rev. 45
(1934) 890) in the form reviewed by M. G. Haines, Plasma Phys. Control.
Fusion 53 (2011) 093001, section 2: the integral pressure balance
``mu0 I^2 / (8 pi) = N k (T_e + T_i)``, the Bennett density profile
``n(r) = n_0 / (1 + r^2 / a^2)^2`` with ``n_0 = N / (pi a^2)``, the
azimuthal field of that profile ``B_theta(r) = mu0 I r / (2 pi (a^2 + r^2))``,
and the Alfven speed and transit time of the column evaluated with the
on-axis density. Every quantity is a closed-form evaluation of the
published model on a validated device configuration; nothing here solves
an equilibrium equation, and no value describes a real machine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.parameters import (
    ELEMENTARY_CHARGE_C,
    MU0,
    Discharge,
    PinchColumn,
    require_non_negative,
    require_positive,
)

PROTON_MASS_KG: Final = 1.67262192369e-27
DEUTERON_MASS_KG: Final = 3.3435837724e-27


@dataclass(frozen=True, slots=True)
class BennettEquilibrium:
    """Closed-form Bennett equilibrium of one validated configuration.

    Parameters
    ----------
    scale_radius_m
        Bennett scale radius ``a`` in metres; the validated column radius.
    current_a
        Pinch current ``I`` in amperes.
    line_density_per_m
        Ion line density ``N`` in inverse metres.
    ion_mass_kg
        Ion mass in kilograms used for the mass density.
    temperature_ev
        Bennett temperature ``T`` (equal ion and electron temperatures)
        in electronvolts.
    axis_density_per_m3
        On-axis density ``n_0 = N / (pi a^2)`` in inverse cubic metres.
    axis_pressure_pa
        On-axis kinetic pressure ``p_0 = 2 n_0 k T`` in pascals.
    edge_field_t
        Azimuthal field at the scale radius ``B_theta(a) = mu0 I / (4 pi a)``
        in tesla.
    alfven_speed_m_s
        ``v_A = B_theta(a) / sqrt(mu0 n_0 m_i)`` in metres per second.
    alfven_transit_time_s
        ``tau_A = a / v_A`` in seconds.
    """

    scale_radius_m: float
    current_a: float
    line_density_per_m: float
    ion_mass_kg: float
    temperature_ev: float
    axis_density_per_m3: float
    axis_pressure_pa: float
    edge_field_t: float
    alfven_speed_m_s: float
    alfven_transit_time_s: float

    def density_at(self, radius_m: float) -> float:
        """Evaluate the Bennett density profile.

        Parameters
        ----------
        radius_m
            Radius in metres; finite and non-negative.

        Returns
        -------
        float
            ``n(r) = n_0 / (1 + (r / a)^2)^2`` in inverse cubic metres.

        Raises
        ------
        DeviceConfigurationError
            If the radius is non-finite or negative.
        """
        ratio = _radius_ratio(radius_m, self.scale_radius_m)
        return self.axis_density_per_m3 / ((1.0 + ratio * ratio) ** 2)

    def pressure_at(self, radius_m: float) -> float:
        """Evaluate the kinetic pressure profile.

        Parameters
        ----------
        radius_m
            Radius in metres; finite and non-negative.

        Returns
        -------
        float
            ``p(r) = p_0 / (1 + (r / a)^2)^2`` in pascals.

        Raises
        ------
        DeviceConfigurationError
            If the radius is non-finite or negative.
        """
        ratio = _radius_ratio(radius_m, self.scale_radius_m)
        return self.axis_pressure_pa / ((1.0 + ratio * ratio) ** 2)

    def field_at(self, radius_m: float) -> float:
        """Evaluate the azimuthal field of the Bennett profile.

        Parameters
        ----------
        radius_m
            Radius in metres; finite and non-negative.

        Returns
        -------
        float
            ``B_theta(r) = mu0 I r / (2 pi (a^2 + r^2))`` in tesla.

        Raises
        ------
        DeviceConfigurationError
            If the radius is non-finite or negative.
        """
        _radius_ratio(radius_m, self.scale_radius_m)
        return (
            MU0
            * self.current_a
            * radius_m
            / (2.0 * math.pi * (self.scale_radius_m**2 + radius_m**2))
        )

    def enclosed_current_at(self, radius_m: float) -> float:
        """Evaluate the current enclosed inside a radius.

        Parameters
        ----------
        radius_m
            Radius in metres; finite and non-negative.

        Returns
        -------
        float
            ``I(r) = I r^2 / (a^2 + r^2)`` in amperes.

        Raises
        ------
        DeviceConfigurationError
            If the radius is non-finite or negative.
        """
        _radius_ratio(radius_m, self.scale_radius_m)
        return self.current_a * radius_m**2 / (self.scale_radius_m**2 + radius_m**2)

    def to_record(self) -> dict[str, float]:
        """Project the equilibrium to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every field of the equilibrium under its SI-suffixed name.
        """
        return {
            "scale_radius_m": self.scale_radius_m,
            "current_a": self.current_a,
            "line_density_per_m": self.line_density_per_m,
            "ion_mass_kg": self.ion_mass_kg,
            "temperature_ev": self.temperature_ev,
            "axis_density_per_m3": self.axis_density_per_m3,
            "axis_pressure_pa": self.axis_pressure_pa,
            "edge_field_t": self.edge_field_t,
            "alfven_speed_m_s": self.alfven_speed_m_s,
            "alfven_transit_time_s": self.alfven_transit_time_s,
        }


def _radius_ratio(radius_m: float, scale_radius_m: float) -> float:
    """Validate a profile radius and return ``r / a``.

    Parameters
    ----------
    radius_m
        Radius in metres.
    scale_radius_m
        Bennett scale radius in metres.

    Returns
    -------
    float
        The dimensionless radius.

    Raises
    ------
    DeviceConfigurationError
        If the radius is non-finite or negative.
    """
    require_non_negative("radius_m", radius_m)
    return radius_m / scale_radius_m


def bennett_equilibrium(
    column: PinchColumn, discharge: Discharge, ion_mass_kg: float
) -> BennettEquilibrium:
    """Evaluate the Bennett equilibrium of a validated configuration.

    Parameters
    ----------
    column
        Validated pinch-column geometry; its radius is the Bennett scale
        radius ``a``.
    discharge
        Validated discharge; its current and line density enter the
        pressure balance.
    ion_mass_kg
        Ion mass in kilograms; strictly positive (see
        :data:`PROTON_MASS_KG` and :data:`DEUTERON_MASS_KG`).

    Returns
    -------
    BennettEquilibrium
        The closed-form equilibrium quantities.

    Raises
    ------
    DeviceConfigurationError
        If the ion mass is non-finite or not strictly positive.

    Notes
    -----
    The temperature is the equal-species Bennett temperature already
    exposed by :meth:`Discharge.bennett_temperature_ev`, so the two
    surfaces can never disagree. Operation order is fixed so that the
    native kernels reproduce every value bit for bit.
    """
    require_positive("ion_mass_kg", ion_mass_kg)
    scale_radius_m = column.column_radius_m
    current_a = discharge.peak_current_ma * 1.0e6
    line_density_per_m = discharge.ion_line_density_per_m
    temperature_ev = discharge.bennett_temperature_ev()
    axis_density_per_m3 = line_density_per_m / (math.pi * scale_radius_m**2)
    axis_pressure_pa = 2.0 * axis_density_per_m3 * temperature_ev * ELEMENTARY_CHARGE_C
    edge_field_t = MU0 * current_a / (4.0 * math.pi * scale_radius_m)
    alfven_speed_m_s = edge_field_t / math.sqrt(MU0 * axis_density_per_m3 * ion_mass_kg)
    alfven_transit_time_s = scale_radius_m / alfven_speed_m_s
    return BennettEquilibrium(
        scale_radius_m=scale_radius_m,
        current_a=current_a,
        line_density_per_m=line_density_per_m,
        ion_mass_kg=ion_mass_kg,
        temperature_ev=temperature_ev,
        axis_density_per_m3=axis_density_per_m3,
        axis_pressure_pa=axis_pressure_pa,
        edge_field_t=edge_field_t,
        alfven_speed_m_s=alfven_speed_m_s,
        alfven_transit_time_s=alfven_transit_time_s,
    )
