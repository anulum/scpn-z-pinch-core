# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — portable diagnostic-plan envelope

"""Producer-owned portable envelope over one diagnostic plan.

A :class:`PlanEnvelope` makes a diagnostic plan portable across project
boundaries by carrying, in one canonically serialised object, the
envelope schema and version, the exact producer identity and owned
configurations, the capability and its evidence maturity, the
synthetic/review-only/non-actuating authority statements, both SPO
registry pins, the SHA-256 digest of the inner canonical plan, the
producer revision, and the fixed no-observation/no-control non-claims.
Consumers verify the envelope against the plan bytes they received;
they never import this repository's source to do so — the installed
package's public parsers are the only codec. Nothing in an envelope is
an observation, a measurement, or a control proposal.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Final

from scpn_z_pinch_core.errors import DiagnosticPlanError
from scpn_z_pinch_core.observability import (
    CATALOGUE_BINDING,
    OWNED_CONFIGURATIONS,
    DiagnosticPlan,
    ObservabilityBinding,
)

ENVELOPE_SCHEMA: Final = "scpn.reactor-diagnostic-plan-envelope.v1"
ENVELOPE_SCHEMA_VERSION: Final = "1.0.0"
PROJECT: Final = "SCPN-Z-PINCH-CORE"
CAPABILITY: Final = "diagnostic_clock_semantics"
EVIDENCE_MATURITY: Final = "computational_prototype"
NON_CLAIMS: Final = (
    "no control action is proposed or authorised",
    "no physical observation is described or claimed",
)
_HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER: Final = re.compile(r"^[a-z][a-z0-9_.]*$")


@dataclass(frozen=True, slots=True)
class PlanEnvelope:
    """Portable, fail-closed declaration wrapper for one diagnostic plan.

    Parameters
    ----------
    schema
        Envelope schema identifier; must equal :data:`ENVELOPE_SCHEMA`.
    schema_version
        Envelope schema version; must equal
        :data:`ENVELOPE_SCHEMA_VERSION`.
    project
        Producer identity; must equal :data:`PROJECT`.
    configurations
        Exact owned configuration set; must equal the repository's
        owned configurations.
    capability
        Capability identifier; must equal :data:`CAPABILITY`.
    evidence_maturity
        Capability maturity; must equal :data:`EVIDENCE_MATURITY`.
    synthetic
        Must be ``True``; the plan is a synthetic declaration.
    authority
        Must be ``"review_only"``.
    actionable
        Must be ``False``.
    binding
        SPO catalogue and reactor-registry pins; must equal the
        embedded :data:`~scpn_z_pinch_core.observability.CATALOGUE_BINDING`.
    plan_identifier
        Identifier of the enveloped plan.
    plan_sha256
        SHA-256 of the inner plan's canonical bytes as lowercase hex.
    producer_revision
        Producer package revision that emitted the envelope; non-empty.
    non_claims
        Fixed explicit non-claims; must equal :data:`NON_CLAIMS`.

    Raises
    ------
    DiagnosticPlanError
        If any component violates the envelope contract.
    """

    schema: str
    schema_version: str
    project: str
    configurations: tuple[str, ...]
    capability: str
    evidence_maturity: str
    synthetic: bool
    authority: str
    actionable: bool
    binding: ObservabilityBinding
    plan_identifier: str
    plan_sha256: str
    producer_revision: str
    non_claims: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate the envelope contract.

        Raises
        ------
        DiagnosticPlanError
            If any component violates the envelope contract.
        """
        if self.schema != ENVELOPE_SCHEMA:
            raise DiagnosticPlanError(
                f"envelope.schema: must be {ENVELOPE_SCHEMA!r}, got {self.schema!r}"
            )
        if self.schema_version != ENVELOPE_SCHEMA_VERSION:
            raise DiagnosticPlanError(
                "envelope.schema_version: must be "
                f"{ENVELOPE_SCHEMA_VERSION!r}, got {self.schema_version!r}"
            )
        if self.project != PROJECT:
            raise DiagnosticPlanError(
                f"envelope.project: must be {PROJECT!r}, got {self.project!r}"
            )
        if self.configurations != OWNED_CONFIGURATIONS:
            raise DiagnosticPlanError(
                "envelope.configurations: must equal the owned set "
                f"{OWNED_CONFIGURATIONS!r}, got {self.configurations!r}"
            )
        if self.capability != CAPABILITY:
            raise DiagnosticPlanError(
                f"envelope.capability: must be {CAPABILITY!r}, got {self.capability!r}"
            )
        if self.evidence_maturity != EVIDENCE_MATURITY:
            raise DiagnosticPlanError(
                "envelope.evidence_maturity: must be "
                f"{EVIDENCE_MATURITY!r}, got {self.evidence_maturity!r}"
            )
        if self.synthetic is not True:
            raise DiagnosticPlanError(
                "envelope.synthetic: every enveloped plan is synthetic"
            )
        if self.authority != "review_only":
            raise DiagnosticPlanError(
                f"envelope.authority: must be 'review_only', got {self.authority!r}"
            )
        if self.actionable is not False:
            raise DiagnosticPlanError(
                "envelope.actionable: envelopes are never actionable"
            )
        if self.binding != CATALOGUE_BINDING:
            raise DiagnosticPlanError(
                "envelope.binding: must pin the embedded catalogue and "
                "reactor-registry releases"
            )
        if _IDENTIFIER.fullmatch(self.plan_identifier) is None:
            raise DiagnosticPlanError(
                "envelope.plan_identifier: malformed identifier "
                f"{self.plan_identifier!r}"
            )
        if _HEX_DIGEST.fullmatch(self.plan_sha256) is None:
            raise DiagnosticPlanError(
                "envelope.plan_sha256: must be 64 lowercase hexadecimal "
                f"characters, got {self.plan_sha256!r}"
            )
        if not self.producer_revision:
            raise DiagnosticPlanError("envelope.producer_revision: must be non-empty")
        if self.non_claims != NON_CLAIMS:
            raise DiagnosticPlanError(
                f"envelope.non_claims: must equal {NON_CLAIMS!r}, "
                f"got {self.non_claims!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the envelope to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Record with every declared envelope field.
        """
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "project": self.project,
            "configurations": list(self.configurations),
            "capability": self.capability,
            "evidence_maturity": self.evidence_maturity,
            "synthetic": self.synthetic,
            "authority": self.authority,
            "actionable": self.actionable,
            "binding": {
                "catalogue_version": self.binding.catalogue_version,
                "catalogue_digest_sha256": self.binding.catalogue_digest_sha256,
                "reactor_registry_version": self.binding.reactor_registry_version,
                "reactor_registry_digest_sha256": (
                    self.binding.reactor_registry_digest_sha256
                ),
            },
            "plan_identifier": self.plan_identifier,
            "plan_sha256": self.plan_sha256,
            "producer_revision": self.producer_revision,
            "non_claims": list(self.non_claims),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the envelope canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact envelope.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def envelope_for_plan(plan: DiagnosticPlan, producer_revision: str) -> PlanEnvelope:
    """Build the envelope for one validated diagnostic plan.

    Parameters
    ----------
    plan
        Validated plan to envelope.
    producer_revision
        Producer package revision emitting the envelope; non-empty.

    Returns
    -------
    PlanEnvelope
        Envelope carrying the plan's identifier and canonical digest.

    Raises
    ------
    DiagnosticPlanError
        If the producer revision is empty.
    """
    return PlanEnvelope(
        schema=ENVELOPE_SCHEMA,
        schema_version=ENVELOPE_SCHEMA_VERSION,
        project=PROJECT,
        configurations=OWNED_CONFIGURATIONS,
        capability=CAPABILITY,
        evidence_maturity=EVIDENCE_MATURITY,
        synthetic=True,
        authority="review_only",
        actionable=False,
        binding=CATALOGUE_BINDING,
        plan_identifier=plan.identifier,
        plan_sha256=plan.digest_sha256(),
        producer_revision=producer_revision,
        non_claims=NON_CLAIMS,
    )


def verify_envelope(envelope: PlanEnvelope, plan: DiagnosticPlan) -> None:
    """Verify one envelope against one plan, fail-closed.

    Parameters
    ----------
    envelope
        Envelope under verification.
    plan
        Plan the envelope claims to describe.

    Raises
    ------
    DiagnosticPlanError
        If the identifier or the canonical digest does not match.
    """
    if envelope.plan_identifier != plan.identifier:
        raise DiagnosticPlanError(
            "envelope.plan_identifier: envelope names "
            f"{envelope.plan_identifier!r} but the plan is "
            f"{plan.identifier!r}"
        )
    digest = plan.digest_sha256()
    if envelope.plan_sha256 != digest:
        raise DiagnosticPlanError(
            "envelope.plan_sha256: envelope pins "
            f"{envelope.plan_sha256} but the plan bytes hash to {digest}"
        )


def _string(record: dict[str, Any], field: str) -> str:
    """Return one required string field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a string.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DiagnosticPlanError(f"{field}: must be a string, got {value!r}")
    return value


def _boolean(record: dict[str, Any], field: str) -> bool:
    """Return one required boolean field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a boolean.

    Returns
    -------
    bool
        The boolean value.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing or not a boolean.
    """
    value = record.get(field)
    if not isinstance(value, bool):
        raise DiagnosticPlanError(f"{field}: must be a boolean, got {value!r}")
    return value


def _string_tuple(record: dict[str, Any], field: str) -> tuple[str, ...]:
    """Return one required string-array field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold an array of strings.

    Returns
    -------
    tuple of str
        The array entries.

    Raises
    ------
    DiagnosticPlanError
        If the field is missing, not an array, or holds non-strings.
    """
    value = record.get(field)
    if not isinstance(value, list):
        raise DiagnosticPlanError(f"{field}: must be an array, got {value!r}")
    for entry in value:
        if not isinstance(entry, str):
            raise DiagnosticPlanError(
                f"{field}: entries must be strings, got {entry!r}"
            )
    return tuple(value)


def envelope_from_record(record: Any) -> PlanEnvelope:
    """Build a validated envelope from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`PlanEnvelope.to_record`.

    Returns
    -------
    PlanEnvelope
        The fully validated envelope.

    Raises
    ------
    DiagnosticPlanError
        If the record shape or any value violates the contract.
    """
    if not isinstance(record, dict):
        raise DiagnosticPlanError("record: must be an object")
    known = {
        "schema",
        "schema_version",
        "project",
        "configurations",
        "capability",
        "evidence_maturity",
        "synthetic",
        "authority",
        "actionable",
        "binding",
        "plan_identifier",
        "plan_sha256",
        "producer_revision",
        "non_claims",
    }
    unknown = sorted(set(record) - known)
    if unknown:
        raise DiagnosticPlanError(f"record: unknown fields {unknown!r}")
    binding = record.get("binding")
    if not isinstance(binding, dict):
        raise DiagnosticPlanError("binding: must be an object")
    return PlanEnvelope(
        schema=_string(record, "schema"),
        schema_version=_string(record, "schema_version"),
        project=_string(record, "project"),
        configurations=_string_tuple(record, "configurations"),
        capability=_string(record, "capability"),
        evidence_maturity=_string(record, "evidence_maturity"),
        synthetic=_boolean(record, "synthetic"),
        authority=_string(record, "authority"),
        actionable=_boolean(record, "actionable"),
        binding=ObservabilityBinding(
            catalogue_version=_string(binding, "catalogue_version"),
            catalogue_digest_sha256=_string(binding, "catalogue_digest_sha256"),
            reactor_registry_version=_string(binding, "reactor_registry_version"),
            reactor_registry_digest_sha256=_string(
                binding, "reactor_registry_digest_sha256"
            ),
        ),
        plan_identifier=_string(record, "plan_identifier"),
        plan_sha256=_string(record, "plan_sha256"),
        producer_revision=_string(record, "producer_revision"),
        non_claims=_string_tuple(record, "non_claims"),
    )


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Assemble a JSON object while refusing duplicate members.

    Parameters
    ----------
    pairs
        Key-value pairs in document order.

    Returns
    -------
    dict[str, Any]
        The assembled object.

    Raises
    ------
    DiagnosticPlanError
        If any key occurs more than once.
    """
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise DiagnosticPlanError(f"record: duplicate member {key!r} is rejected")
        record[key] = value
    return record


def envelope_from_bytes(data: bytes) -> PlanEnvelope:
    """Build a validated envelope from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals and duplicate
        members are rejected.

    Returns
    -------
    PlanEnvelope
        The fully validated envelope.

    Raises
    ------
    DiagnosticPlanError
        If the document is not valid strict JSON or violates the
        contract.
    """

    def _reject_constant(literal: str) -> float:
        raise DiagnosticPlanError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicates,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticPlanError(f"record: invalid JSON document: {exc}") from exc
    return envelope_from_record(record)
