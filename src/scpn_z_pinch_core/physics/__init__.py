# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — level-0 device physics package

"""Level-0 device physics of the z-pinch family.

Four cited closed-form models evaluated on the validated device
configuration: the Bennett equilibrium, ideal-MHD growth-rate estimates
with the Kadomtsev m=0 criterion, the Shumlak-Hartman sheared-flow
criterion, and the Pease-Braginskii current. Every function is a
closed-form evaluation; no equilibrium or stability equation is solved
and no value describes a real machine. Design record: ADR 0005.
"""

from __future__ import annotations

from scpn_z_pinch_core.physics.bennett import (
    DEUTERON_MASS_KG,
    PROTON_MASS_KG,
    BennettEquilibrium,
    bennett_equilibrium,
)
from scpn_z_pinch_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    level0_physics,
)
from scpn_z_pinch_core.physics.pease_braginskii import (
    BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12,
    SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32,
    PeaseBraginskiiAssessment,
    pease_braginskii_assessment,
    pease_braginskii_current,
)
from scpn_z_pinch_core.physics.sheared_flow import (
    SHUMLAK_HARTMAN_COEFFICIENT,
    ShearAssessment,
    minimum_stabilising_shear,
    shear_assessment,
)
from scpn_z_pinch_core.physics.stability import (
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    GrowthRateEstimate,
    KadomtsevAssessment,
    growth_rate_estimate,
    kadomtsev_assessment,
)

__all__ = [
    "BREMSSTRAHLUNG_COEFFICIENT_W_M3_J12",
    "DEUTERON_MASS_KG",
    "IDEAL_MONATOMIC_ADIABATIC_INDEX",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "PROTON_MASS_KG",
    "SHUMLAK_HARTMAN_COEFFICIENT",
    "SPITZER_CONDUCTIVITY_COEFFICIENT_S_PER_M_J32",
    "BennettEquilibrium",
    "GrowthRateEstimate",
    "KadomtsevAssessment",
    "Level0PhysicsRecord",
    "ModelInputs",
    "PeaseBraginskiiAssessment",
    "ShearAssessment",
    "bennett_equilibrium",
    "growth_rate_estimate",
    "kadomtsev_assessment",
    "level0_physics",
    "minimum_stabilising_shear",
    "pease_braginskii_assessment",
    "pease_braginskii_current",
    "shear_assessment",
]
