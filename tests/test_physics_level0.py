# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — level-0 physics record tests

"""Composition, canonical serialisation and wiring of the level-0 record.

All parameter sets are synthetic fixtures; none describes a real machine.
"""

from __future__ import annotations

import hashlib
import json
import math

import pytest

import scpn_z_pinch_core
from scpn_z_pinch_core import (
    DeviceConfiguration,
    Discharge,
    PinchColumn,
    RegistryBinding,
)
from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    ModelInputs,
    bennett_equilibrium,
    growth_rate_estimate,
    kadomtsev_assessment,
    level0_physics,
    pease_braginskii_assessment,
    shear_assessment,
)

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)


def synthetic_configuration(
    identifier: str = "sheared_flow_z_pinch", flow_shear_per_s: float = 1.0e6
) -> DeviceConfiguration:
    """Build a valid synthetic configuration."""
    return DeviceConfiguration(
        identifier=identifier,
        column=PinchColumn(column_radius_m=0.005, column_length_m=0.5),
        discharge=Discharge(peak_current_ma=0.1, ion_line_density_per_m=1.0e18),
        flow_shear_per_s=flow_shear_per_s,
        registry=REGISTRY,
    )


def synthetic_inputs(**overrides: float) -> ModelInputs:
    """Build valid synthetic model inputs with optional overrides."""
    values: dict[str, float] = {
        "ion_mass_kg": DEUTERON_MASS_KG,
        "mean_ion_charge": 1.0,
        "axial_wavenumber_per_m": 200.0,
        "adiabatic_index": IDEAL_MONATOMIC_ADIABATIC_INDEX,
        "coulomb_logarithm": 10.0,
        "kadomtsev_radius_ratio": 1.0,
    }
    values.update(overrides)
    return ModelInputs(**values)


def test_record_composes_the_four_models_from_the_same_equilibrium() -> None:
    """Every component equals the standalone model evaluated on the same inputs."""
    configuration = synthetic_configuration()
    inputs = synthetic_inputs()
    record = level0_physics(configuration, inputs)
    equilibrium = bennett_equilibrium(
        configuration.column, configuration.discharge, DEUTERON_MASS_KG
    )
    assert record.equilibrium == equilibrium
    assert record.growth == growth_rate_estimate(equilibrium, 200.0)
    assert record.kadomtsev == kadomtsev_assessment(
        1.0, IDEAL_MONATOMIC_ADIABATIC_INDEX
    )
    assert record.shear == shear_assessment(equilibrium, 200.0, 1.0e6)
    assert record.pease_braginskii == pease_braginskii_assessment(
        equilibrium.current_a, 10.0, 1.0
    )
    assert record.configuration_digest_sha256 == configuration.digest_sha256()
    assert record.inputs == inputs


def test_static_class_reports_no_stabilisation() -> None:
    """The static z_pinch class carries zero shear and is not stabilised."""
    record = level0_physics(
        synthetic_configuration("z_pinch", flow_shear_per_s=0.0), synthetic_inputs()
    )
    assert record.shear.declared_shear_per_s == 0.0
    assert record.shear.kink_stabilised is False


def test_canonical_bytes_digest_and_non_claims() -> None:
    """Serialisation is canonical, digestible, and carries the fixed non-claims."""
    record = level0_physics(synthetic_configuration(), synthetic_inputs())
    data = record.canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data)
    assert decoded["schema"] == LEVEL0_SCHEMA == "scpn.z-pinch-level0-physics.v1"
    assert decoded["schema_version"] == LEVEL0_SCHEMA_VERSION == "1.0.0"
    assert decoded["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert list(decoded) == sorted(decoded)
    assert record.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert decoded["inputs"] == synthetic_inputs().to_record()
    assert decoded["equilibrium"]["current_a"] == 1.0e5
    assert decoded["pease_braginskii"]["regime"] == "below_pease_braginskii"


def test_record_is_deterministic() -> None:
    """Two evaluations of the same inputs are byte-identical."""
    first = level0_physics(synthetic_configuration(), synthetic_inputs())
    second = level0_physics(synthetic_configuration(), synthetic_inputs())
    assert first.canonical_bytes() == second.canonical_bytes()


@pytest.mark.parametrize(
    "field",
    [
        "ion_mass_kg",
        "mean_ion_charge",
        "axial_wavenumber_per_m",
        "adiabatic_index",
        "coulomb_logarithm",
        "kadomtsev_radius_ratio",
    ],
)
@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf])
def test_every_model_input_is_validated(field: str, bad: float) -> None:
    """Each declared input rejects non-positive and non-finite values."""
    with pytest.raises(DeviceConfigurationError, match=field):
        synthetic_inputs(**{field: bad})


def test_physics_api_is_reachable_from_the_public_package() -> None:
    """The level-0 surface is exported at package level."""
    for name in (
        "ModelInputs",
        "Level0PhysicsRecord",
        "level0_physics",
        "bennett_equilibrium",
        "pease_braginskii_current",
    ):
        assert name in scpn_z_pinch_core.__all__
        assert hasattr(scpn_z_pinch_core, name)
