# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — catalogue binding and candidate profiles

"""Catalogue binding and the applicable candidate profiles.

:class:`ObservabilityBinding` pins the SCPN Phase Orchestrator
observability-profile catalogue release and reactor registry this package
is aligned with; :data:`CATALOGUE_BINDING` is that pin. The applicable
candidate subset is embedded as data in :data:`APPLICABLE_CANDIDATES`, so
the package never imports Phase Orchestrator code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.vocabulary import (
    _ADMISSIBLE_CARRIERS,
    _REQUIRED_EVIDENCE,
    HEX_DIGEST,
    IDENTIFIER,
    OBSERVABILITY_CATALOGUE_DIGEST,
    OBSERVABILITY_CATALOGUE_VERSION,
    OWNED_CONFIGURATIONS,
    REACTOR_REGISTRY_DIGEST,
    REACTOR_REGISTRY_VERSION,
    ObservabilityClass,
    SemanticCarrier,
)


@dataclass(frozen=True, slots=True)
class ObservabilityBinding:
    """Pin to one SPO observability-profile catalogue release.

    Parameters
    ----------
    catalogue_version
        Catalogue release version; non-empty.
    catalogue_digest_sha256
        Catalogue digest as 64 lowercase hexadecimal characters.
    reactor_registry_version
        Reactor registry release the catalogue is bound to; non-empty.
    reactor_registry_digest_sha256
        Reactor registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DiagnosticPlanError
        If any pin component is malformed.
    """

    catalogue_version: str
    catalogue_digest_sha256: str
    reactor_registry_version: str
    reactor_registry_digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the catalogue pin.

        Raises
        ------
        DiagnosticPlanError
            If any pin component is malformed.
        """
        if not self.catalogue_version:
            raise DiagnosticPlanError("binding.catalogue_version: must be non-empty")
        if not self.reactor_registry_version:
            raise DiagnosticPlanError(
                "binding.reactor_registry_version: must be non-empty"
            )
        for field, digest in (
            ("catalogue_digest_sha256", self.catalogue_digest_sha256),
            ("reactor_registry_digest_sha256", self.reactor_registry_digest_sha256),
        ):
            if HEX_DIGEST.fullmatch(digest) is None:
                raise DiagnosticPlanError(
                    f"binding.{field}: must be 64 lowercase hexadecimal "
                    f"characters, got {digest!r}"
                )


CATALOGUE_BINDING: Final = ObservabilityBinding(
    catalogue_version=OBSERVABILITY_CATALOGUE_VERSION,
    catalogue_digest_sha256=OBSERVABILITY_CATALOGUE_DIGEST,
    reactor_registry_version=REACTOR_REGISTRY_VERSION,
    reactor_registry_digest_sha256=REACTOR_REGISTRY_DIGEST,
)


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """One SPO catalogue candidate restricted to this repository.

    Applicability means only that the phenomenon is meaningful to
    investigate for the listed configurations. It asserts no
    implementation, measurement, observability, or readiness.

    Parameters
    ----------
    candidate_id
        Exact SPO catalogue candidate identifier.
    phenomenon
        Catalogue phenomenon statement.
    configurations
        Owned configurations the candidate applies to; unique and sorted.
    observability_class
        Epistemic route fixed by the catalogue.

    Raises
    ------
    DiagnosticPlanError
        If any component contradicts the catalogue structure.
    """

    candidate_id: str
    phenomenon: str
    configurations: tuple[str, ...]
    observability_class: ObservabilityClass

    def __post_init__(self) -> None:
        """Validate the embedded candidate row.

        Raises
        ------
        DiagnosticPlanError
            If any component contradicts the catalogue structure.
        """
        if IDENTIFIER.fullmatch(self.candidate_id) is None:
            raise DiagnosticPlanError(
                f"candidate.candidate_id: malformed identifier {self.candidate_id!r}"
            )
        if not self.phenomenon:
            raise DiagnosticPlanError("candidate.phenomenon: must be non-empty")
        if not self.configurations:
            raise DiagnosticPlanError(
                "candidate.configurations: must list at least one configuration"
            )
        if tuple(sorted(set(self.configurations))) != self.configurations:
            raise DiagnosticPlanError(
                "candidate.configurations: must be unique and sorted"
            )
        for configuration in self.configurations:
            if configuration not in OWNED_CONFIGURATIONS:
                raise DiagnosticPlanError(
                    "candidate.configurations: "
                    f"{configuration!r} is not owned by SCPN-Z-PINCH-CORE"
                )

    @property
    def admissible_carriers(self) -> frozenset[SemanticCarrier]:
        """Return the carriers the catalogue admits for this class.

        Returns
        -------
        frozenset of SemanticCarrier
            Admissible carriers fixed by the observability class.
        """
        return _ADMISSIBLE_CARRIERS[self.observability_class]

    @property
    def required_evidence(self) -> tuple[str, ...]:
        """Return the class-fixed evidence vocabulary.

        Returns
        -------
        tuple of str
            Evidence slot names fixed by the observability class.
        """
        return _REQUIRED_EVIDENCE[self.observability_class]


APPLICABLE_CANDIDATES: Final = (
    CandidateProfile(
        candidate_id="model.synthetic_oscillator_coordinate",
        phenomenon="model-owned synthetic oscillator coordinate",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.NUMERICAL_ONLY,
    ),
    CandidateProfile(
        candidate_id="self_magnetic.drive_waveform",
        phenomenon="pulsed-power current and voltage event progression",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.EVENT_RELATIVE,
    ),
    CandidateProfile(
        candidate_id="self_magnetic.resolved_instability_mode",
        phenomenon="resolved sausage, kink, or other pinch mode",
        configurations=("sheared_flow_z_pinch", "z_pinch"),
        observability_class=ObservabilityClass.DERIVED_CYCLIC,
    ),
)


_CANDIDATE_INDEX: Final = {
    candidate.candidate_id: candidate for candidate in APPLICABLE_CANDIDATES
}
