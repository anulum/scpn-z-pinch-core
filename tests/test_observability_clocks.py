# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — clocks diagnostic tests

"""Clock models, their domains and topology, and the relations between them.

A clock is refused in the direction it is wrong: an unusable resolution,
an unassigned physical clock, a domain root of the wrong kind, a relation
cycle. The plan-level rules that bind clocks into a topology live here
with the objects they constrain.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import pytest

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    DERIVED_BINDINGS,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    channel_derived,
    channel_event_train,
    channel_oscillator,
    clock_facility,
    clock_shot,
    clock_simulation,
    derived_channel,
    plan_with,
    synthetic_plan,
)
from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    ClockDomain,
    ClockKind,
    ClockModel,
    ClockRelation,
    ClockTopology,
    DeferredCandidate,
    DiagnosticPlan,
)

SHOT_ONLY_TOPOLOGY = ClockTopology(
    domains=(
        ClockDomain(
            identifier="dom_shot",
            root_clock_identifier="clk_shot",
            member_clock_identifiers=("clk_shot",),
            scope="shot trigger only; no facility clock in this variant",
        ),
    ),
    reference_domain_identifier="dom_shot",
)


def _relation(child: str, parent: str) -> ClockRelation:
    """Build a synthetic unmapped relation between two declared clocks."""
    return ClockRelation(
        child_identifier=child,
        parent_identifier=parent,
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method="synthetic declaration; no correlation evidence claimed",
        mapping_state="unmapped",
        evidence_claimed=False,
    )


def _second_facility() -> ClockModel:
    """Build a second synthetic facility clock for multi-domain variants."""
    return ClockModel(
        identifier="clk_facility_b",
        kind=ClockKind.FACILITY_MONOTONIC,
        epoch="second facility oscillator zero",
        resolution_s=1.0e-8,
        uncertainty_s=5.0e-9,
    )


def _two_domain_topology() -> ClockTopology:
    """Build a two-domain topology over the reference clocks plus a second facility."""
    return ClockTopology(
        domains=(
            ClockDomain(
                identifier="dom_facility",
                root_clock_identifier="clk_facility",
                member_clock_identifiers=("clk_facility", "clk_shot"),
                scope="primary facility timing",
            ),
            ClockDomain(
                identifier="dom_facility_b",
                root_clock_identifier="clk_facility_b",
                member_clock_identifiers=("clk_facility_b",),
                scope="secondary facility timing",
            ),
        ),
        reference_domain_identifier="dom_facility",
    )


def _topology(*domains: ClockDomain, reference: str = "dom_facility") -> ClockTopology:
    """Build a topology from domains sorted by identifier."""
    return ClockTopology(
        domains=tuple(sorted(domains, key=lambda domain: domain.identifier)),
        reference_domain_identifier=reference,
    )


def test_clock_rejects_malformed_identifier() -> None:
    """A malformed clock identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"clock\.identifier"):
        ClockModel(
            identifier="Clock!",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


def test_clock_rejects_empty_epoch() -> None:
    """An empty epoch statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="epoch"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("resolution", [0.0, -1.0, float("nan"), float("inf")])
def test_clock_rejects_bad_resolution(resolution: float) -> None:
    """Non-positive or non-finite resolutions are rejected."""
    with pytest.raises(DiagnosticPlanError, match="resolution_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=resolution,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("uncertainty", [-1.0e-9, float("nan")])
def test_clock_rejects_bad_uncertainty(uncertainty: float) -> None:
    """Negative or non-finite uncertainties are rejected."""
    with pytest.raises(DiagnosticPlanError, match="uncertainty_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=uncertainty,
        )


def test_domain_rejects_malformed_identifiers() -> None:
    """Malformed domain and root identifiers are rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"domain\.identifier"):
        ClockDomain(
            identifier="Dom!",
            root_clock_identifier="clk_facility",
            member_clock_identifiers=("clk_facility",),
            scope="x",
        )
    with pytest.raises(
        DiagnosticPlanError, match=r"domain\.root_clock_identifier: malformed"
    ):
        ClockDomain(
            identifier="dom",
            root_clock_identifier="Clk!",
            member_clock_identifiers=("clk_facility",),
            scope="x",
        )


@pytest.mark.parametrize(
    ("members", "message"),
    [
        ((), "at least one clock"),
        (("clk_shot", "clk_facility"), "unique and sorted"),
        (("clk_facility", "clk_facility"), "unique and sorted"),
        (("clk_shot",), "root must be a member"),
    ],
)
def test_domain_rejects_bad_membership(members: tuple[str, ...], message: str) -> None:
    """Domain membership is unique, sorted, non-empty, and includes the root."""
    with pytest.raises(DiagnosticPlanError, match=message):
        ClockDomain(
            identifier="dom",
            root_clock_identifier="clk_facility",
            member_clock_identifiers=members,
            scope="x",
        )


def test_domain_rejects_empty_scope() -> None:
    """An empty scope statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"domain\.scope"):
        ClockDomain(
            identifier="dom",
            root_clock_identifier="clk_facility",
            member_clock_identifiers=("clk_facility",),
            scope="",
        )


def test_topology_rejects_empty_unsorted_or_unknown_reference() -> None:
    """A topology declares sorted domains and a declared reference domain."""
    domain = CLOCK_TOPOLOGY.domains[0]
    with pytest.raises(DiagnosticPlanError, match="at least one domain"):
        ClockTopology(domains=(), reference_domain_identifier="dom_facility")
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        ClockTopology(
            domains=(domain, domain), reference_domain_identifier="dom_facility"
        )
    with pytest.raises(DiagnosticPlanError, match="reference_domain_identifier"):
        ClockTopology(domains=(domain,), reference_domain_identifier="dom_zz")


def test_plan_rejects_domain_with_undeclared_clock() -> None:
    """Domain members must be declared clocks."""
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_facility",
        member_clock_identifiers=("clk_facility", "clk_shot", "clk_zz"),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        plan_with(clock_topology=_topology(domain))


def test_plan_rejects_simulation_clock_in_domain() -> None:
    """The simulation clock belongs to no physical domain."""
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_facility",
        member_clock_identifiers=("clk_facility", "clk_shot", "clk_sim"),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="no physical domain"):
        plan_with(clock_topology=_topology(domain))


def test_plan_rejects_clock_in_two_domains() -> None:
    """Each physical clock belongs to exactly one domain."""
    first = CLOCK_TOPOLOGY.domains[0]
    second = ClockDomain(
        identifier="dom_second",
        root_clock_identifier="clk_shot",
        member_clock_identifiers=("clk_shot",),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="more than one domain"):
        plan_with(clock_topology=_topology(first, second))


def test_plan_rejects_domain_root_of_wrong_kind() -> None:
    """A domain containing a facility clock is rooted at a facility clock."""
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_shot",
        member_clock_identifiers=("clk_facility", "clk_shot"),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="root must be of kind"):
        plan_with(clock_topology=_topology(domain))


def test_plan_rejects_unassigned_physical_clock() -> None:
    """Every physical clock belongs to a domain."""
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_facility",
        member_clock_identifiers=("clk_facility",),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="belong to no domain"):
        plan_with(clock_topology=_topology(domain))


def test_plan_requires_member_relation_to_domain_root() -> None:
    """Each non-root member declares a relation to its domain root."""
    plan = synthetic_plan()
    clocks = tuple(
        sorted((*plan.clocks, _second_facility()), key=lambda clock: clock.identifier)
    )
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_facility",
        member_clock_identifiers=("clk_facility", "clk_facility_b", "clk_shot"),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="relation to its domain root"):
        plan_with(clocks=clocks, clock_topology=_topology(domain))


def test_plan_requires_cross_domain_relation_to_reference_root() -> None:
    """Every non-reference domain root declares a relation to the reference root."""
    plan = synthetic_plan()
    clocks = tuple(
        sorted((*plan.clocks, _second_facility()), key=lambda clock: clock.identifier)
    )
    with pytest.raises(DiagnosticPlanError, match="reference root"):
        plan_with(clocks=clocks, clock_topology=_two_domain_topology())
    accepted = plan_with(
        clocks=clocks,
        clock_relations=tuple(
            sorted(
                (*plan.clock_relations, _relation("clk_facility_b", "clk_facility")),
                key=lambda relation: (
                    relation.child_identifier,
                    relation.parent_identifier,
                ),
            )
        ),
        clock_topology=_two_domain_topology(),
    )
    assert accepted.clock_topology.reference_domain_identifier == "dom_facility"


def test_plan_rejects_relation_cycle() -> None:
    """Clock relations must not form a cycle."""
    plan = synthetic_plan()
    clocks = tuple(
        sorted((*plan.clocks, _second_facility()), key=lambda clock: clock.identifier)
    )
    domain = ClockDomain(
        identifier="dom_facility",
        root_clock_identifier="clk_facility",
        member_clock_identifiers=("clk_facility", "clk_facility_b", "clk_shot"),
        scope="x",
    )
    with pytest.raises(DiagnosticPlanError, match="cycle"):
        plan_with(
            clocks=clocks,
            clock_relations=tuple(
                sorted(
                    (
                        *plan.clock_relations,
                        _relation("clk_facility_b", "clk_facility"),
                        _relation("clk_facility", "clk_facility_b"),
                    ),
                    key=lambda relation: (
                        relation.child_identifier,
                        relation.parent_identifier,
                    ),
                )
            ),
            clock_topology=_topology(domain),
        )


def test_plan_rejects_unsorted_clocks() -> None:
    """Clocks must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.clocks"):
        DiagnosticPlan(
            identifier="z_pinch_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_shot(), clock_facility(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_event_train(),
                channel_derived(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_undeclared_clock() -> None:
    """A channel bound to an undeclared clock is rejected."""
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        DiagnosticPlan(
            identifier="z_pinch_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_event_train(),
                channel_derived(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_incompatible_clock_kind() -> None:
    """A cyclic channel cannot bind to a shot-epoch clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_shot"
    channel = derived_channel(clock_identifier="clk_shot", evidence_bindings=bindings)
    with pytest.raises(DiagnosticPlanError, match="incompatible with class"):
        DiagnosticPlan(
            identifier="z_pinch_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_event_train(),
                channel,
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_relation_rejects_self_relation() -> None:
    """A clock cannot be related to itself."""
    with pytest.raises(DiagnosticPlanError, match="itself"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_shot",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_relation_rejects_bad_bounds(value: float) -> None:
    """Non-finite or negative relation bounds are rejected."""
    with pytest.raises(DiagnosticPlanError, match="finite and non-negative"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=value,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_relation_rejects_empty_method() -> None:
    """A relation without a method statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="method"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_plan_rejects_undeclared_relation_clock() -> None:
    """A relation naming an undeclared clock is rejected."""
    relation = ClockRelation(
        child_identifier="clk_zz_unknown",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method="x",
        mapping_state="unmapped",
        evidence_claimed=False,
    )
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, relation),
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_rejects_simulation_clock_relation() -> None:
    """The simulation clock cannot join a synchronisation relation."""
    relation = ClockRelation(
        child_identifier="clk_sim",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method="x",
        mapping_state="unmapped",
        evidence_claimed=False,
    )
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="simulation clock"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, relation),
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_requires_epoch_to_facility_bound() -> None:
    """An epoch clock without a facility bound is rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="must declare a bound"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(),
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_relation_rejects_malformed_identifier() -> None:
    """A malformed relation clock identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"relation\.child_identifier"):
        ClockRelation(
            child_identifier="Clock!",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_plan_without_facility_clock_needs_no_relation() -> None:
    """Without a facility clock, epoch clocks need no declared bound."""
    plan = synthetic_plan()
    facility_ids = {
        clock.identifier
        for clock in plan.clocks
        if clock.kind is ClockKind.FACILITY_MONOTONIC
    }
    clocks = tuple(
        clock for clock in plan.clocks if clock.identifier not in facility_ids
    )
    channels = tuple(
        channel
        for channel in plan.channels
        if channel.clock_identifier not in facility_ids
    )
    kept = {channel.candidate_id for channel in channels}
    deferrals = tuple(
        DeferredCandidate(
            candidate_id=candidate.candidate_id,
            reason="no facility clock in this variant",
        )
        for candidate in APPLICABLE_CANDIDATES
        if candidate.candidate_id not in kept
    )
    variant = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=clocks,
        frames=plan.frames,
        clock_relations=(),
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=SHOT_ONLY_TOPOLOGY,
        channels=channels,
        deferrals=deferrals,
    )
    assert variant.clock_relations == ()


def test_relation_rejects_mapped_state() -> None:
    """Any mapping state other than unmapped is rejected."""
    with pytest.raises(DiagnosticPlanError, match="mapping_state"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="mapped",
            evidence_claimed=False,
        )


def test_relation_rejects_claimed_evidence() -> None:
    """A relation may never claim correlation evidence."""
    with pytest.raises(DiagnosticPlanError, match="evidence_claimed"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=True,
        )


def test_plan_rejects_duplicate_relations() -> None:
    """Duplicate clock relations are rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match=r"plan\.clock_relations"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, plan.clock_relations[0]),
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )
