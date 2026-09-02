# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — ideal-MHD stability estimates of the Bennett pinch

"""Ideal-MHD stability estimates of the Bennett pinch (level-0 physics).

Two published statements are evaluated, nothing more:

- the order-of-magnitude growth rate ``gamma ~ k v_A`` of the m=0 sausage
  and m=1 kink modes of an unstabilised z-pinch for a declared axial
  wavenumber (M. G. Haines, Plasma Phys. Control. Fusion 53 (2011)
  093001, section 5), and
- the Kadomtsev m=0 criterion (B. B. Kadomtsev, Reviews of Plasma Physics
  vol. 2 (1966) 153; Haines 2011, section 5): the pressure profile is
  sausage-stable at a radius where ``-d ln p / d ln r < 4 gamma_ad /
  (2 + gamma_ad beta)`` with ``beta = 2 mu0 p / B_theta^2``. For the
  Bennett profile both sides are closed forms of ``x = r / a``:
  ``-d ln p / d ln r = 4 x^2 / (1 + x^2)`` and ``beta = 1 / x^2``.

These are marginal-stability estimates of specific published models. No
linear eigenvalue problem is solved here; that is solver mathematics and
stays outside this repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.parameters import require_positive
from scpn_z_pinch_core.physics.bennett import BennettEquilibrium

IDEAL_MONATOMIC_ADIABATIC_INDEX: Final = 5.0 / 3.0


@dataclass(frozen=True, slots=True)
class GrowthRateEstimate:
    """Order-of-magnitude ideal-MHD growth-rate estimate.

    Parameters
    ----------
    axial_wavenumber_per_m
        Declared axial wavenumber ``k`` in inverse metres.
    alfven_speed_m_s
        Alfven speed of the equilibrium in metres per second.
    growth_rate_per_s
        ``gamma ~ k v_A`` in inverse seconds; applies to both the m=0 and
        the m=1 mode at this level of approximation.
    e_folding_time_s
        ``1 / gamma`` in seconds.
    """

    axial_wavenumber_per_m: float
    alfven_speed_m_s: float
    growth_rate_per_s: float
    e_folding_time_s: float

    def to_record(self) -> dict[str, float]:
        """Project the estimate to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every field under its SI-suffixed name.
        """
        return {
            "axial_wavenumber_per_m": self.axial_wavenumber_per_m,
            "alfven_speed_m_s": self.alfven_speed_m_s,
            "growth_rate_per_s": self.growth_rate_per_s,
            "e_folding_time_s": self.e_folding_time_s,
        }


@dataclass(frozen=True, slots=True)
class KadomtsevAssessment:
    """Kadomtsev m=0 criterion evaluated at one radius of the Bennett profile.

    Parameters
    ----------
    radius_ratio
        Dimensionless radius ``x = r / a``; strictly positive.
    adiabatic_index
        Adiabatic index ``gamma_ad``; strictly positive.
    profile_exponent
        ``-d ln p / d ln r = 4 x^2 / (1 + x^2)``.
    local_beta
        ``beta = 2 mu0 p / B_theta^2 = 1 / x^2``.
    threshold
        ``4 gamma_ad / (2 + gamma_ad beta)``.
    sausage_stable
        ``True`` exactly when ``profile_exponent < threshold``.
    """

    radius_ratio: float
    adiabatic_index: float
    profile_exponent: float
    local_beta: float
    threshold: float
    sausage_stable: bool

    def to_record(self) -> dict[str, float | bool]:
        """Project the assessment to a JSON-serialisable record.

        Returns
        -------
        dict[str, float or bool]
            Every field under its name.
        """
        return {
            "radius_ratio": self.radius_ratio,
            "adiabatic_index": self.adiabatic_index,
            "profile_exponent": self.profile_exponent,
            "local_beta": self.local_beta,
            "threshold": self.threshold,
            "sausage_stable": self.sausage_stable,
        }


def growth_rate_estimate(
    equilibrium: BennettEquilibrium, axial_wavenumber_per_m: float
) -> GrowthRateEstimate:
    """Estimate the ideal-MHD growth rate for a declared wavenumber.

    Parameters
    ----------
    equilibrium
        Bennett equilibrium supplying the Alfven speed.
    axial_wavenumber_per_m
        Declared axial wavenumber ``k``; strictly positive. No spectrum
        is computed; the caller declares the mode.

    Returns
    -------
    GrowthRateEstimate
        ``gamma ~ k v_A`` and its e-folding time.

    Raises
    ------
    DeviceConfigurationError
        If the wavenumber is non-finite or not strictly positive.
    """
    require_positive("axial_wavenumber_per_m", axial_wavenumber_per_m)
    growth_rate_per_s = axial_wavenumber_per_m * equilibrium.alfven_speed_m_s
    return GrowthRateEstimate(
        axial_wavenumber_per_m=axial_wavenumber_per_m,
        alfven_speed_m_s=equilibrium.alfven_speed_m_s,
        growth_rate_per_s=growth_rate_per_s,
        e_folding_time_s=1.0 / growth_rate_per_s,
    )


def kadomtsev_assessment(
    radius_ratio: float, adiabatic_index: float
) -> KadomtsevAssessment:
    """Evaluate the Kadomtsev m=0 criterion on the Bennett profile.

    Parameters
    ----------
    radius_ratio
        Dimensionless radius ``x = r / a``; strictly positive (the
        criterion is singular on the axis where ``beta`` diverges).
    adiabatic_index
        Adiabatic index ``gamma_ad``; strictly positive (see
        :data:`IDEAL_MONATOMIC_ADIABATIC_INDEX`).

    Returns
    -------
    KadomtsevAssessment
        Both sides of the criterion and the disposition.

    Raises
    ------
    DeviceConfigurationError
        If either input is non-finite or not strictly positive.

    Notes
    -----
    Substituting the Bennett closed forms, the criterion reduces to
    ``2 < gamma_ad`` independently of the radius: for the ideal
    monatomic index 5/3 the Bennett profile is sausage-unstable at every
    radius, which is the published conclusion (Haines 2011, section 5).
    """
    require_positive("radius_ratio", radius_ratio)
    require_positive("adiabatic_index", adiabatic_index)
    squared = radius_ratio * radius_ratio
    profile_exponent = 4.0 * squared / (1.0 + squared)
    local_beta = 1.0 / squared
    threshold = 4.0 * adiabatic_index / (2.0 + adiabatic_index * local_beta)
    return KadomtsevAssessment(
        radius_ratio=radius_ratio,
        adiabatic_index=adiabatic_index,
        profile_exponent=profile_exponent,
        local_beta=local_beta,
        threshold=threshold,
        sausage_stable=profile_exponent < threshold,
    )
