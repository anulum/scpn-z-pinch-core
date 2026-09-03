# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device capability package

"""Device capability models of the SCPN z-pinch device family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics``, ``level0_device_physics``,
``device_3d_model`` and ``device_cad_model`` capabilities at
``computational_prototype`` maturity: validated parameter objects,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, documented consistency estimates, four cited
closed-form level-0 physics models evaluated on the validated
configuration, a validated device geometry with a deterministic tier-G1
3D model built on the pinned shared kernel library and open-format
exports, the tier-G2 B-rep CAD model of the same design with a
normalised deterministic STEP export, canonical serialisation with
SHA-256 digests, and data-only pins to the SPO registries. No claim
about any real machine or diagnostic is made anywhere in this package.
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
from scpn_z_pinch_core.errors import (
    DeviceConfigurationError,
    DeviceGeometryError,
    DiagnosticPlanError,
)
from scpn_z_pinch_core.geometry import (
    BODY_NAMES,
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    GEOMETRY_FIELDS,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    BodyCADEvidence,
    DeviceGeometry,
    DeviceModel3D,
    DeviceModelCAD,
    build_device_cad,
    build_device_model,
    geometry_from_bytes,
    geometry_from_record,
    glb_bytes,
    glb_extras,
    stl_bytes,
    write_glb,
    write_step,
    write_stl,
)
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
    "BODY_NAMES",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "CATALOGUE_BINDING",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "DEUTERON_MASS_KG",
    "ELEMENTARY_CHARGE_C",
    "GEOMETRY_FIELDS",
    "IDEAL_MONATOMIC_ADIABATIC_INDEX",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "MU0",
    "OWNED_CONFIGURATIONS",
    "PROTON_MASS_KG",
    "SHUMLAK_HARTMAN_COEFFICIENT",
    "BennettEquilibrium",
    "BodyCADEvidence",
    "CandidateProfile",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DeviceGeometry",
    "DeviceGeometryError",
    "DeviceModel3D",
    "DeviceModelCAD",
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
    "build_device_cad",
    "build_device_model",
    "configuration_from_bytes",
    "configuration_from_record",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "growth_rate_estimate",
    "kadomtsev_assessment",
    "level0_physics",
    "minimum_stabilising_shear",
    "pease_braginskii_assessment",
    "pease_braginskii_current",
    "plan_from_bytes",
    "plan_from_record",
    "shear_assessment",
    "stl_bytes",
    "verify_envelope",
    "write_glb",
    "write_step",
    "write_stl",
]
