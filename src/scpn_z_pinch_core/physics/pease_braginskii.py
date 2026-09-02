# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — Pease-Braginskii current

"""Pease-Braginskii current of a z-pinch (level-0 device physics).

R. S. Pease, Proc. Phys. Soc. B 70 (1957) 11 and S. I. Braginskii, Sov.
Phys. JETP 6 (1958) 494 showed that a Bennett pinch has a critical current
at which ohmic heating balances bremsstrahlung: below it the column
expands, above it the column contracts (radiative collapse). The
published closed form implemented here is equation (2.20) of D. Klir,
The Study of a Fibre Z-Pinch, PhD thesis, Czech Technical University in
Prague (2005), arXiv:physics/0703207, derived under the stated closures:
optically thin plasma, uniform temperature, uniform current density,
bremsstrahlung as the only loss, a parabolic density profile
``n_i(r) = n_max (1 - r^2 / R^2)``, Spitzer conductivity
``sigma = sigma_0 (k T_e)^{3/2} / (z ln Lambda)`` and bremsstrahlung power
density ``A z^3 n_i^2 (k T_e)^{1/2}``::

    I_PB = (pi / mu0) sqrt(48 ln Lambda / (sigma_0 A)) (1 + z) / z

The two coefficients are the NRL Plasma Formulary values converted to
SI with the temperature in joules (the half-integer powers of the
elementary charge are formed with ``sqrt`` only, so the native kernels
reproduce them bit for bit): parallel Spitzer resistivity
``1.03e-4 z ln Lambda T_eV^{-3/2}`` ohm metre and bremsstrahlung
``1.69e-38 n_e sum(Z^2 n_Z) T_eV^{1/2}`` watt per cubic metre. For a
hydrogenic plasma (``z = 1``) with ``ln Lambda = 10`` the expression
gives 1.37 MA, the value the literature quotes as approximately 1.4 MA
(Haines, Plasma Phys. Control. Fusion 53 (2011) 093001, section 3).

The current is independent of radius and line density; the ratio of the
configured current to it labels the regime. Nothing here is a yield,
gain or breakeven statement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.parameters import ELEMENTARY_CHARGE_C, MU0, require_positive

SPITZER_RESISTIVITY_OHM_M_EV: Final = 1.03e-4
BREMSSTRAHLUNG_W_M3_EV: Final = 1.69e-38
SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32: Final = 1.0 / (
    SPITZER_RESISTIVITY_OHM_M_EV
    * (ELEMENTARY_CHARGE_C * math.sqrt(ELEMENTARY_CHARGE_C))
)
BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12: Final = BREMSSTRAHLUNG_W_M3_EV / math.sqrt(
    ELEMENTARY_CHARGE_C
)


@dataclass(frozen=True, slots=True)
class PeaseBraginskiiAssessment:
    """Pease-Braginskii current and the regime of one configuration.

    Parameters
    ----------
    coulomb_logarithm
        Declared Coulomb logarithm ``ln Lambda``; strictly positive.
    mean_ion_charge
        Declared mean ion charge state ``z``; strictly positive.
    pease_braginskii_current_a
        ``I_PB`` in amperes.
    current_a
        Configured pinch current in amperes.
    current_ratio
        ``I / I_PB``.
    regime
        ``"below_pease_braginskii"`` when the ratio is below one (ohmic
        heating exceeds bremsstrahlung; expansion), otherwise
        ``"at_or_above_pease_braginskii"`` (radiative contraction).
    """

    coulomb_logarithm: float
    mean_ion_charge: float
    pease_braginskii_current_a: float
    current_a: float
    current_ratio: float
    regime: str

    def to_record(self) -> dict[str, float | str]:
        """Project the assessment to a JSON-serialisable record.

        Returns
        -------
        dict[str, float or str]
            Every field under its SI-suffixed name.
        """
        return {
            "coulomb_logarithm": self.coulomb_logarithm,
            "mean_ion_charge": self.mean_ion_charge,
            "pease_braginskii_current_a": self.pease_braginskii_current_a,
            "current_a": self.current_a,
            "current_ratio": self.current_ratio,
            "regime": self.regime,
        }


def pease_braginskii_current(coulomb_logarithm: float, mean_ion_charge: float) -> float:
    """Evaluate the Pease-Braginskii current.

    Parameters
    ----------
    coulomb_logarithm
        Declared Coulomb logarithm ``ln Lambda``; strictly positive.
    mean_ion_charge
        Declared mean ion charge state ``z``; strictly positive.

    Returns
    -------
    float
        ``I_PB = (pi / mu0) sqrt(48 ln Lambda / (sigma_0 A)) (1 + z) / z``
        in amperes.

    Raises
    ------
    DeviceConfigurationError
        If either input is non-finite or not strictly positive.
    """
    require_positive("coulomb_logarithm", coulomb_logarithm)
    require_positive("mean_ion_charge", mean_ion_charge)
    root = math.sqrt(
        48.0
        * coulomb_logarithm
        / (
            SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32
            * BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12
        )
    )
    return (math.pi / MU0) * root * (1.0 + mean_ion_charge) / mean_ion_charge


def pease_braginskii_assessment(
    current_a: float, coulomb_logarithm: float, mean_ion_charge: float
) -> PeaseBraginskiiAssessment:
    """Label the regime of a configured current against ``I_PB``.

    Parameters
    ----------
    current_a
        Configured pinch current in amperes; strictly positive.
    coulomb_logarithm
        Declared Coulomb logarithm; strictly positive.
    mean_ion_charge
        Declared mean ion charge state; strictly positive.

    Returns
    -------
    PeaseBraginskiiAssessment
        The critical current, the ratio and the regime label.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or not strictly positive.
    """
    require_positive("current_a", current_a)
    critical = pease_braginskii_current(coulomb_logarithm, mean_ion_charge)
    ratio = current_a / critical
    return PeaseBraginskiiAssessment(
        coulomb_logarithm=coulomb_logarithm,
        mean_ion_charge=mean_ion_charge,
        pease_braginskii_current_a=critical,
        current_a=current_a,
        current_ratio=ratio,
        regime=(
            "below_pease_braginskii" if ratio < 1.0 else "at_or_above_pease_braginskii"
        ),
    )
