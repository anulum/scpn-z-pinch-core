<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Z Pinch Core — ADR 0004
-->

# ADR 0004 — Signal inventories, frame transformations, and clock topology

Status: accepted (2026-09-01). Extends ADR 0003 (diagnostic and clock
semantics) and its deepening (typed frames, clock relations, acquisition
geometry).

## Context

After the deepening slice the diagnostic plan still described three
things only in prose: what signals a composite channel would carry, how
the declared reference frames relate, and how the declared physical
clocks are organised. The SCPN Phase Orchestrator intake consumes the
plan through exact key sets per schema version, so any new member is a
coordinated contract change, not a local convenience.

## Decision

1. Every channel declares a typed signal inventory (`SignalDeclaration`)
   with exactly one carrier, a timing marker in seconds exactly for
   event-relative channels, and a single phase/radian carrier for
   numerical-only channels. Quantity and unit are declared tokens; no SI
   or UCUM validation is performed or claimed, and no declaration can
   create or override a candidate, carrier, observation, or phase — the
   candidate profile remains authoritative.
2. Frame transformations (`FrameTransformation`) are admitted only for
   fixed frame-kind pairs with a fixed kind, are unique per frame pair,
   sorted, and must connect every declared frame; `equilibrium_dependent`
   holds exactly for flux mappings and `evidence_claimed` is always
   false.
3. A clock topology (`ClockDomain`, `ClockTopology`) partitions the
   physical clocks into rooted domains; the simulation clock belongs to
   none; members relate to their root and non-reference roots relate to
   the reference root; relations are acyclic. The reference plan declares
   the one domain the committed clocks support.
4. The producer-owned envelope becomes `1.2.0`. Consumers dispatch by
   exact schema version; `1.1.0` documents are historical custody only
   and are refused by the `1.2.0` codec.

## Consequences

The plan describes HOW signals, frames, and clocks would bind, at a
higher resolution, and nothing more. Evidence maturity is unchanged
(`computational_prototype`); the descriptor is unchanged; no ingress,
observation, mapping to wall time, or control authority is declared.
