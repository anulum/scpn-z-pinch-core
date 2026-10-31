# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — reference frames and frame transformations

"""Reference frames and the transformations between them.

:class:`ReferenceFrame` declares one frame of a diagnostic plan and
:class:`FrameTransformation` one declared mapping between two frames,
restricted to the kind-admissibility table of the vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.vocabulary import (
    ALLOWED_FRAME_KINDS,
    IDENTIFIER,
    FrameKind,
    TransformationKind,
)


@dataclass(frozen=True, slots=True)
class ReferenceFrame:
    """One declared reference-frame identity.

    Parameters
    ----------
    identifier
        Plan-local frame identifier.
    kind
        Frame kind; must be allowed for this repository.
    description
        Statement of the frame convention; non-empty.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    kind: FrameKind
    description: str

    def __post_init__(self) -> None:
        """Validate the frame declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"frame.identifier: malformed identifier {self.identifier!r}"
            )
        if self.kind not in ALLOWED_FRAME_KINDS:
            raise DiagnosticPlanError(
                f"frame.kind: {self.kind.value!r} is not an allowed frame "
                "kind for this repository"
            )
        if not self.description:
            raise DiagnosticPlanError("frame.description: must be non-empty")


@dataclass(frozen=True, slots=True)
class FrameTransformation:
    """One declared mapping between two declared reference frames.

    A transformation declares HOW coordinates in the source frame would be
    expressed in the target frame; the method is a declaration and no
    metrological evidence is claimed.

    Parameters
    ----------
    source_identifier
        Declared frame the mapping starts from.
    target_identifier
        Declared frame the mapping lands in.
    kind
        Mapping kind; must be admissible for the two frame kinds.
    equilibrium_dependent
        Must be ``True`` exactly for ``flux_mapping`` (the mapping depends
        on an equilibrium reconstruction) and ``False`` otherwise.
    method
        Statement of HOW the mapping would be established; non-empty.
    evidence_claimed
        Must be ``False``: no mapping evidence exists or is claimed.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    source_identifier: str
    target_identifier: str
    kind: TransformationKind
    equilibrium_dependent: bool
    method: str
    evidence_claimed: bool

    def __post_init__(self) -> None:
        """Validate the transformation declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        for field, value in (
            ("source_identifier", self.source_identifier),
            ("target_identifier", self.target_identifier),
        ):
            if IDENTIFIER.fullmatch(value) is None:
                raise DiagnosticPlanError(
                    f"transformation.{field}: malformed identifier {value!r}"
                )
        if self.source_identifier == self.target_identifier:
            raise DiagnosticPlanError(
                "transformation: a frame cannot be transformed to itself"
            )
        expected_dependency = self.kind is TransformationKind.FLUX_MAPPING
        if self.equilibrium_dependent is not expected_dependency:
            raise DiagnosticPlanError(
                "transformation.equilibrium_dependent: must be "
                f"{expected_dependency!r} for kind {self.kind.value!r}"
            )
        if not self.method:
            raise DiagnosticPlanError("transformation.method: must be non-empty")
        if self.evidence_claimed is not False:
            raise DiagnosticPlanError(
                "transformation.evidence_claimed: must be False; no mapping "
                "evidence exists or is claimed"
            )
