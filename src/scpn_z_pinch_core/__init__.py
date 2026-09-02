# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device capability package

"""Device capability models of the SCPN z-pinch device family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics`` and ``level0_device_physics`` capabilities
at ``computational_prototype`` maturity: validated parameter objects,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, documented consistency estimates, four cited
closed-form level-0 physics models evaluated on the validated
configuration, canonical serialisation with SHA-256 digests, and
data-only pins to the SPO registries. No claim about any real machine or
diagnostic is made anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_z_pinch_core.configuration import (
    BENNETT_WINDOW_EV,
    OWNED_CONFIGURATIONS,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_z_pinch_core.errors import DeviceConfigurationError, DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    CandidateProfile,
    ClockKind,
    ClockModel,
    ClockRelation,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    ObservabilityBinding,
    ObservabilityClass,
    ReferenceFrame,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)
from scpn_z_pinch_core.parameters import (
    ELEMENTARY_CHARGE_C,
    MU0,
    Discharge,
    PinchColumn,
)
from scpn_z_pinch_core.physics import (
    DEUTERON_MASS_KG,
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    PROTON_MASS_KG,
    SHUMLAK_HARTMAN_COEFFICIENT,
    BennettEquilibrium,
    GrowthRateEstimate,
    KadomtsevAssessment,
    Level0PhysicsRecord,
    ModelInputs,
    PeaseBraginskiiAssessment,
    ShearAssessment,
    bennett_equilibrium,
    growth_rate_estimate,
    kadomtsev_assessment,
    level0_physics,
    minimum_stabilising_shear,
    pease_braginskii_assessment,
    pease_braginskii_current,
    shear_assessment,
)
from scpn_z_pinch_core.plan_envelope import (
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

__version__: Final = "0.1.0.dev0"

__all__ = [
    "APPLICABLE_CANDIDATES",
    "BENNETT_WINDOW_EV",
    "CATALOGUE_BINDING",
    "DEUTERON_MASS_KG",
    "ELEMENTARY_CHARGE_C",
    "IDEAL_MONATOMIC_ADIABATIC_INDEX",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "MU0",
    "OWNED_CONFIGURATIONS",
    "PROTON_MASS_KG",
    "SHUMLAK_HARTMAN_COEFFICIENT",
    "BennettEquilibrium",
    "CandidateProfile",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "DiagnosticPlanError",
    "Discharge",
    "FrameKind",
    "GrowthRateEstimate",
    "KadomtsevAssessment",
    "Level0PhysicsRecord",
    "ModelInputs",
    "ObservabilityBinding",
    "ObservabilityClass",
    "PeaseBraginskiiAssessment",
    "PinchColumn",
    "PlanEnvelope",
    "ReferenceFrame",
    "RegistryBinding",
    "SemanticCarrier",
    "ShearAssessment",
    "__version__",
    "bennett_equilibrium",
    "configuration_from_bytes",
    "configuration_from_record",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "growth_rate_estimate",
    "kadomtsev_assessment",
    "level0_physics",
    "minimum_stabilising_shear",
    "pease_braginskii_assessment",
    "pease_braginskii_current",
    "plan_from_bytes",
    "plan_from_record",
    "shear_assessment",
    "verify_envelope",
]
