# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — sheared-axial-flow stabilisation criterion

"""Sheared-axial-flow stabilisation criterion (level-0 device physics).

U. Shumlak and C. W. Hartman, Phys. Rev. Lett. 75 (1995) 3285, found
from linear ideal-MHD calculations that a sheared axial flow stabilises
the m=1 kink mode of a z-pinch when the shear exceeds
``dv_z / dr > 0.1 k v_A`` for the axial wavenumber ``k``. This module
evaluates that threshold for a declared wavenumber and compares the
shear the configuration declares against it. No flow profile is solved
and no spectrum is computed; the disposition is a statement of the
published criterion for the declared numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.parameters import require_non_negative, require_positive
from scpn_z_pinch_core.physics.bennett import BennettEquilibrium

SHUMLAK_HARTMAN_COEFFICIENT: Final = 0.1


@dataclass(frozen=True, slots=True)
class ShearAssessment:
    """Shumlak-Hartman kink criterion for one declared shear.

    Parameters
    ----------
    axial_wavenumber_per_m
        Declared axial wavenumber ``k`` in inverse metres.
    alfven_speed_m_s
        Alfven speed of the equilibrium in metres per second.
    minimum_shear_per_s
        ``0.1 k v_A`` in inverse seconds.
    declared_shear_per_s
        Axial flow shear the configuration declares, in inverse seconds.
    kink_stabilised
        ``True`` exactly when ``declared_shear_per_s > minimum_shear_per_s``.
    """

    axial_wavenumber_per_m: float
    alfven_speed_m_s: float
    minimum_shear_per_s: float
    declared_shear_per_s: float
    kink_stabilised: bool

    def to_record(self) -> dict[str, float | bool]:
        """Project the assessment to a JSON-serialisable record.

        Returns
        -------
        dict[str, float or bool]
            Every field under its SI-suffixed name.
        """
        return {
            "axial_wavenumber_per_m": self.axial_wavenumber_per_m,
            "alfven_speed_m_s": self.alfven_speed_m_s,
            "minimum_shear_per_s": self.minimum_shear_per_s,
            "declared_shear_per_s": self.declared_shear_per_s,
            "kink_stabilised": self.kink_stabilised,
        }


def minimum_stabilising_shear(
    equilibrium: BennettEquilibrium, axial_wavenumber_per_m: float
) -> float:
    """Evaluate the Shumlak-Hartman shear threshold.

    Parameters
    ----------
    equilibrium
        Bennett equilibrium supplying the Alfven speed.
    axial_wavenumber_per_m
        Declared axial wavenumber ``k``; strictly positive.

    Returns
    -------
    float
        ``0.1 k v_A`` in inverse seconds.

    Raises
    ------
    DeviceConfigurationError
        If the wavenumber is non-finite or not strictly positive.
    """
    require_positive("axial_wavenumber_per_m", axial_wavenumber_per_m)
    return (
        SHUMLAK_HARTMAN_COEFFICIENT
        * axial_wavenumber_per_m
        * equilibrium.alfven_speed_m_s
    )


def shear_assessment(
    equilibrium: BennettEquilibrium,
    axial_wavenumber_per_m: float,
    declared_shear_per_s: float,
) -> ShearAssessment:
    """Compare a declared shear against the published threshold.

    Parameters
    ----------
    equilibrium
        Bennett equilibrium supplying the Alfven speed.
    axial_wavenumber_per_m
        Declared axial wavenumber ``k``; strictly positive.
    declared_shear_per_s
        Declared axial flow shear; finite and non-negative (the static
        class declares exactly zero).

    Returns
    -------
    ShearAssessment
        Threshold, declared value, and disposition.

    Raises
    ------
    DeviceConfigurationError
        If the wavenumber is not strictly positive or the shear is
        non-finite or negative.
    """
    minimum = minimum_stabilising_shear(equilibrium, axial_wavenumber_per_m)
    require_non_negative("declared_shear_per_s", declared_shear_per_s)
    return ShearAssessment(
        axial_wavenumber_per_m=axial_wavenumber_per_m,
        alfven_speed_m_s=equilibrium.alfven_speed_m_s,
        minimum_shear_per_s=minimum,
        declared_shear_per_s=declared_shear_per_s,
        kink_stabilised=declared_shear_per_s > minimum,
    )
