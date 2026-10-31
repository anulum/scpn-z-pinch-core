# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — clock relations, domains and topology

"""Clock identities, their relations, domains and topology.

:class:`ClockModel` declares one clock, :class:`ClockRelation` one declared
relation between two clocks, and :class:`ClockDomain` and
:class:`ClockTopology` partition the physical clocks into rooted domains
with a star of relations to the reference root.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability.vocabulary import (
    IDENTIFIER,
    ClockKind,
)


@dataclass(frozen=True, slots=True)
class ClockRelation:
    """One declared synchronisation bound between two declared clocks.

    A relation declares synthetic offset and uncertainty BOUNDS between
    two clock identities; it claims no correlation evidence, and no
    clock is thereby mapped to physical wall time.

    Parameters
    ----------
    child_identifier
        Clock whose epoch is being bounded.
    parent_identifier
        Clock the bound is stated against.
    max_offset_s
        Declared worst-case offset magnitude; finite and non-negative.
    uncertainty_s
        Declared uncertainty of the bound; finite and non-negative.
    method
        Statement of HOW the bound would be established; non-empty.
    mapping_state
        Must be ``"unmapped"``: no clock is mapped to wall time.
    evidence_claimed
        Must be ``False``: no correlation evidence exists or is claimed.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    child_identifier: str
    parent_identifier: str
    max_offset_s: float
    uncertainty_s: float
    method: str
    mapping_state: str
    evidence_claimed: bool

    def __post_init__(self) -> None:
        """Validate the relation declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        for field, value in (
            ("child_identifier", self.child_identifier),
            ("parent_identifier", self.parent_identifier),
        ):
            if IDENTIFIER.fullmatch(value) is None:
                raise DiagnosticPlanError(
                    f"relation.{field}: malformed identifier {value!r}"
                )
        if self.child_identifier == self.parent_identifier:
            raise DiagnosticPlanError("relation: a clock cannot be related to itself")
        for bound_field, bound_value in (
            ("max_offset_s", self.max_offset_s),
            ("uncertainty_s", self.uncertainty_s),
        ):
            if not math.isfinite(bound_value) or bound_value < 0.0:
                raise DiagnosticPlanError(
                    f"relation.{bound_field}: must be finite and "
                    f"non-negative, got {bound_value!r}"
                )
        if not self.method:
            raise DiagnosticPlanError("relation.method: must be non-empty")
        if self.mapping_state != "unmapped":
            raise DiagnosticPlanError(
                "relation.mapping_state: must be 'unmapped'; no clock is "
                f"mapped to wall time, got {self.mapping_state!r}"
            )
        if self.evidence_claimed is not False:
            raise DiagnosticPlanError(
                "relation.evidence_claimed: must be False; no correlation "
                "evidence exists or is claimed"
            )


@dataclass(frozen=True, slots=True)
class ClockDomain:
    """One declared clock domain: a root clock and the clocks bound to it.

    Parameters
    ----------
    identifier
        Plan-local domain identifier.
    root_clock_identifier
        Declared clock the domain is referenced to; must be a member.
    member_clock_identifiers
        Declared clocks in the domain; unique, sorted, non-empty.
    scope
        Statement of the facility subsystem the domain represents; a
        declaration only.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    root_clock_identifier: str
    member_clock_identifiers: tuple[str, ...]
    scope: str

    def __post_init__(self) -> None:
        """Validate the domain declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"domain.identifier: malformed identifier {self.identifier!r}"
            )
        if IDENTIFIER.fullmatch(self.root_clock_identifier) is None:
            raise DiagnosticPlanError(
                "domain.root_clock_identifier: malformed identifier "
                f"{self.root_clock_identifier!r}"
            )
        if not self.member_clock_identifiers:
            raise DiagnosticPlanError(
                "domain.member_clock_identifiers: must list at least one clock"
            )
        if (
            tuple(sorted(set(self.member_clock_identifiers)))
            != self.member_clock_identifiers
        ):
            raise DiagnosticPlanError(
                "domain.member_clock_identifiers: must be unique and sorted"
            )
        if self.root_clock_identifier not in self.member_clock_identifiers:
            raise DiagnosticPlanError(
                "domain.root_clock_identifier: the root must be a member"
            )
        if not self.scope:
            raise DiagnosticPlanError("domain.scope: must be non-empty")


@dataclass(frozen=True, slots=True)
class ClockTopology:
    """Declared partition of the physical clocks into domains.

    Parameters
    ----------
    domains
        Declared domains, sorted by identifier; at least one.
    reference_domain_identifier
        Domain whose root is the plan's timing reference; must be declared.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    domains: tuple[ClockDomain, ...]
    reference_domain_identifier: str

    def __post_init__(self) -> None:
        """Validate the topology declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if not self.domains:
            raise DiagnosticPlanError(
                "topology.domains: must declare at least one domain"
            )
        domain_ids = tuple(domain.identifier for domain in self.domains)
        if tuple(sorted(set(domain_ids))) != domain_ids:
            raise DiagnosticPlanError("topology.domains: must be unique and sorted")
        if self.reference_domain_identifier not in domain_ids:
            raise DiagnosticPlanError(
                "topology.reference_domain_identifier: "
                f"{self.reference_domain_identifier!r} is not a declared domain"
            )


@dataclass(frozen=True, slots=True)
class ClockModel:
    """One declared clock identity.

    Parameters
    ----------
    identifier
        Plan-local clock identifier.
    kind
        Clock domain the identifier represents.
    epoch
        Statement of the epoch convention; non-empty.
    resolution_s
        Smallest resolvable increment in seconds; finite and positive.
    uncertainty_s
        Declared timing uncertainty in seconds; finite and non-negative.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the model.
    """

    identifier: str
    kind: ClockKind
    epoch: str
    resolution_s: float
    uncertainty_s: float

    def __post_init__(self) -> None:
        """Validate the clock declaration.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the model.
        """
        if IDENTIFIER.fullmatch(self.identifier) is None:
            raise DiagnosticPlanError(
                f"clock.identifier: malformed identifier {self.identifier!r}"
            )
        if not self.epoch:
            raise DiagnosticPlanError("clock.epoch: must be non-empty")
        if not math.isfinite(self.resolution_s) or self.resolution_s <= 0.0:
            raise DiagnosticPlanError(
                "clock.resolution_s: must be finite and positive, "
                f"got {self.resolution_s!r}"
            )
        if not math.isfinite(self.uncertainty_s) or self.uncertainty_s < 0.0:
            raise DiagnosticPlanError(
                "clock.uncertainty_s: must be finite and non-negative, "
                f"got {self.uncertainty_s!r}"
            )
