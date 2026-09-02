# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — level-0 physics record

"""Level-0 physics record of one validated device configuration.

The record composes the four published level-0 models on the validated
:class:`~scpn_z_pinch_core.configuration.DeviceConfiguration` together
with the declared model inputs the configuration does not carry (ion
mass, mean ion charge, axial wavenumber, adiabatic index, Coulomb
logarithm, and the radius ratio at which the Kadomtsev criterion is
reported). It serialises canonically with a SHA-256 digest, in the same
style as the configuration itself, and states its own non-claims: every
number is a closed-form evaluation of a cited model on a synthetic
configuration, at ``computational_prototype`` maturity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_z_pinch_core.configuration import DeviceConfiguration
from scpn_z_pinch_core.parameters import require_positive
from scpn_z_pinch_core.physics.bennett import (
    BennettEquilibrium,
    bennett_equilibrium,
)
from scpn_z_pinch_core.physics.pease_braginskii import (
    PeaseBraginskiiAssessment,
    pease_braginskii_assessment,
)
from scpn_z_pinch_core.physics.sheared_flow import ShearAssessment, shear_assessment
from scpn_z_pinch_core.physics.stability import (
    GrowthRateEstimate,
    KadomtsevAssessment,
    growth_rate_estimate,
    kadomtsev_assessment,
)

LEVEL0_SCHEMA: Final = "scpn.z-pinch-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
LEVEL0_NON_CLAIMS: Final = (
    "closed-form evaluation of cited published models on a synthetic configuration",
    "no equilibrium or stability equation is solved",
    "no yield, gain, reactivity or breakeven statement",
    "no value describes or validates any real machine",
)


@dataclass(frozen=True, slots=True)
class ModelInputs:
    """Declared inputs of the level-0 models beyond the configuration.

    Parameters
    ----------
    ion_mass_kg
        Ion mass in kilograms; strictly positive.
    mean_ion_charge
        Mean ion charge state ``z``; strictly positive.
    axial_wavenumber_per_m
        Declared axial wavenumber ``k`` for the stability estimates;
        strictly positive.
    adiabatic_index
        Adiabatic index for the Kadomtsev criterion; strictly positive.
    coulomb_logarithm
        Coulomb logarithm for the Pease-Braginskii current; strictly
        positive.
    kadomtsev_radius_ratio
        Radius ratio ``r / a`` at which the Kadomtsev criterion is
        reported; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or not strictly positive.
    """

    ion_mass_kg: float
    mean_ion_charge: float
    axial_wavenumber_per_m: float
    adiabatic_index: float
    coulomb_logarithm: float
    kadomtsev_radius_ratio: float

    def __post_init__(self) -> None:
        """Validate every declared input.

        Raises
        ------
        DeviceConfigurationError
            If any input is non-finite or not strictly positive.
        """
        require_positive("ion_mass_kg", self.ion_mass_kg)
        require_positive("mean_ion_charge", self.mean_ion_charge)
        require_positive("axial_wavenumber_per_m", self.axial_wavenumber_per_m)
        require_positive("adiabatic_index", self.adiabatic_index)
        require_positive("coulomb_logarithm", self.coulomb_logarithm)
        require_positive("kadomtsev_radius_ratio", self.kadomtsev_radius_ratio)

    def to_record(self) -> dict[str, float]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every field under its name.
        """
        return {
            "ion_mass_kg": self.ion_mass_kg,
            "mean_ion_charge": self.mean_ion_charge,
            "axial_wavenumber_per_m": self.axial_wavenumber_per_m,
            "adiabatic_index": self.adiabatic_index,
            "coulomb_logarithm": self.coulomb_logarithm,
            "kadomtsev_radius_ratio": self.kadomtsev_radius_ratio,
        }


@dataclass(frozen=True, slots=True)
class Level0PhysicsRecord:
    """The four level-0 models evaluated on one configuration.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the record was built from.
    inputs
        Declared model inputs.
    equilibrium
        Bennett equilibrium.
    growth
        Ideal-MHD growth-rate estimate for the declared wavenumber.
    kadomtsev
        Kadomtsev m=0 criterion at the declared radius ratio.
    shear
        Shumlak-Hartman shear criterion for the declared shear.
    pease_braginskii
        Pease-Braginskii current and regime.
    """

    configuration_digest_sha256: str
    inputs: ModelInputs
    equilibrium: BennettEquilibrium
    growth: GrowthRateEstimate
    kadomtsev: KadomtsevAssessment
    shear: ShearAssessment
    pease_braginskii: PeaseBraginskiiAssessment

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            Schema identity, non-claims, and every model record.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "non_claims": list(LEVEL0_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "inputs": self.inputs.to_record(),
            "equilibrium": self.equilibrium.to_record(),
            "growth": self.growth.to_record(),
            "kadomtsev": self.kadomtsev.to_record(),
            "shear": self.shear.to_record(),
            "pease_braginskii": self.pease_braginskii.to_record(),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(
    configuration: DeviceConfiguration, inputs: ModelInputs
) -> Level0PhysicsRecord:
    """Evaluate every level-0 model on a validated configuration.

    Parameters
    ----------
    configuration
        Validated device configuration.
    inputs
        Declared model inputs.

    Returns
    -------
    Level0PhysicsRecord
        The composed record.
    """
    equilibrium = bennett_equilibrium(
        configuration.column, configuration.discharge, inputs.ion_mass_kg
    )
    return Level0PhysicsRecord(
        configuration_digest_sha256=configuration.digest_sha256(),
        inputs=inputs,
        equilibrium=equilibrium,
        growth=growth_rate_estimate(equilibrium, inputs.axial_wavenumber_per_m),
        kadomtsev=kadomtsev_assessment(
            inputs.kadomtsev_radius_ratio, inputs.adiabatic_index
        ),
        shear=shear_assessment(
            equilibrium, inputs.axial_wavenumber_per_m, configuration.flow_shear_per_s
        ),
        pease_braginskii=pease_braginskii_assessment(
            equilibrium.current_a, inputs.coulomb_logarithm, inputs.mean_ion_charge
        ),
    )
