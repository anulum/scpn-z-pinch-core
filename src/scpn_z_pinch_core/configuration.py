# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device configuration container

"""Device configuration container bound to the SPO reactor registry.

A :class:`DeviceConfiguration` composes a validated pinch column and
discharge under exactly one of the two registry identifiers this
repository owns. The flow-shear class invariant is hard: sheared axial
flow defines the stabilised class (Shumlak & Hartman, PRL 75 (1995)
3285), and the static class declares exactly zero shear. The Bennett
temperature outside the documented plasma window is flagged.
Serialisation is canonical (sorted keys, no NaN or infinity accepted
anywhere) and the SHA-256 digest of those bytes identifies the exact
parameter set. The registry binding is a data pin only — this package
never imports SCPN Phase Orchestrator code.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Final

from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import Discharge, PinchColumn, require_finite

OWNED_CONFIGURATIONS: Final = ("sheared_flow_z_pinch", "z_pinch")
BENNETT_WINDOW_EV: Final = (1.0, 1.0e5)
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RegistryBinding:
    """Pin to one SPO reactor registry release.

    Parameters
    ----------
    version
        Registry release version; non-empty.
    digest_sha256
        Registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DeviceConfigurationError
        If either pin component is malformed.
    """

    version: str
    digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the registry pin.

        Raises
        ------
        DeviceConfigurationError
            If either pin component is malformed.
        """
        if not self.version:
            raise DeviceConfigurationError("registry.version: must be non-empty")
        if HEX_DIGEST.fullmatch(self.digest_sha256) is None:
            raise DeviceConfigurationError(
                "registry.digest_sha256: must be 64 lowercase hexadecimal "
                f"characters, got {self.digest_sha256!r}"
            )


@dataclass(frozen=True, slots=True)
class ConsistencyFinding:
    """One internal-consistency finding on a device configuration.

    Parameters
    ----------
    field
        Dotted field path the finding refers to.
    message
        Human-readable statement of the inconsistency.
    """

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class DeviceConfiguration:
    """Validated z-pinch device configuration.

    Parameters
    ----------
    identifier
        SPO registry configuration identifier; one of
        ``sheared_flow_z_pinch`` or ``z_pinch``.
    column
        Validated pinch-column geometry.
    discharge
        Validated discharge parameters.
    flow_shear_per_s
        Declared axial flow shear; strictly positive for the
        sheared-flow class and exactly zero for the static class.
    registry
        Pin to the SPO reactor registry release the identifier belongs
        to.

    Raises
    ------
    DeviceConfigurationError
        If the identifier is not owned by this repository or the shear
        declaration contradicts the class.
    """

    identifier: str
    column: PinchColumn
    discharge: Discharge
    flow_shear_per_s: float
    registry: RegistryBinding

    def __post_init__(self) -> None:
        """Validate identifier ownership and the shear class invariant.

        Raises
        ------
        DeviceConfigurationError
            If the identifier is not owned by this repository or the
            shear declaration contradicts the class.
        """
        if self.identifier not in OWNED_CONFIGURATIONS:
            raise DeviceConfigurationError(
                f"identifier: {self.identifier!r} is not owned by "
                f"SCPN-Z-PINCH-CORE; owned: {OWNED_CONFIGURATIONS!r}"
            )
        require_finite("flow_shear_per_s", self.flow_shear_per_s)
        if self.identifier == "sheared_flow_z_pinch" and self.flow_shear_per_s <= 0.0:
            raise DeviceConfigurationError(
                "flow_shear_per_s: sheared_flow_z_pinch requires strictly "
                f"positive flow shear, got {self.flow_shear_per_s!r}"
            )
        if self.identifier == "z_pinch" and self.flow_shear_per_s != 0.0:
            raise DeviceConfigurationError(
                "flow_shear_per_s: the static z_pinch class declares exactly "
                f"zero shear, got {self.flow_shear_per_s!r}"
            )

    def consistency_report(self) -> tuple[ConsistencyFinding, ...]:
        """Report physics-consistency findings without failing.

        Returns
        -------
        tuple of ConsistencyFinding
            Advisory findings from the documented estimates; empty when
            the Bennett temperature sits in the documented window.
            Findings are advisory instruments, not machine claims.
        """
        findings: list[ConsistencyFinding] = []
        temperature = self.discharge.bennett_temperature_ev()
        low, high = BENNETT_WINDOW_EV
        if not low <= temperature <= high:
            findings.append(
                ConsistencyFinding(
                    field="discharge.peak_current_ma",
                    message=(
                        f"Bennett temperature {temperature:.3g} eV is outside "
                        f"the documented pinch plasma window [{low:.0f} eV, "
                        f"{high:.0f} eV]"
                    ),
                )
            )
        return tuple(findings)

    def to_record(self) -> dict[str, Any]:
        """Project the configuration to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Nested record with every declared parameter.
        """
        return {
            "identifier": self.identifier,
            "column": {
                "column_radius_m": self.column.column_radius_m,
                "column_length_m": self.column.column_length_m,
            },
            "discharge": {
                "peak_current_ma": self.discharge.peak_current_ma,
                "ion_line_density_per_m": (self.discharge.ion_line_density_per_m),
            },
            "flow_shear_per_s": self.flow_shear_per_s,
            "registry": {
                "version": self.registry.version,
                "digest_sha256": self.registry.digest_sha256,
            },
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the configuration canonically.

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
        """Identify the exact parameter set.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _require_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """Return one required mapping field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a mapping.

    Returns
    -------
    dict[str, Any]
        The nested mapping.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a mapping.
    """
    value = record.get(field)
    if not isinstance(value, dict):
        raise DeviceConfigurationError(f"{field}: must be an object")
    return value


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number.

    Returns
    -------
    float
        The numeric value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a real number.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceConfigurationError(f"{field}: must be a number, got {value!r}")
    return float(value)


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
    DeviceConfigurationError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DeviceConfigurationError(f"{field}: must be a string, got {value!r}")
    return value


def configuration_from_record(record: Any) -> DeviceConfiguration:
    """Build a validated configuration from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceConfiguration.to_record`.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the record shape or any value violates the model.
    """
    if not isinstance(record, dict):
        raise DeviceConfigurationError("record: must be an object")
    known = {"identifier", "column", "discharge", "flow_shear_per_s", "registry"}
    unknown = sorted(set(record) - known)
    if unknown:
        raise DeviceConfigurationError(f"record: unknown fields {unknown!r}")
    column = _require_mapping(record, "column")
    discharge = _require_mapping(record, "discharge")
    registry = _require_mapping(record, "registry")
    return DeviceConfiguration(
        identifier=_string(record, "identifier"),
        column=PinchColumn(
            column_radius_m=_number(column, "column_radius_m"),
            column_length_m=_number(column, "column_length_m"),
        ),
        discharge=Discharge(
            peak_current_ma=_number(discharge, "peak_current_ma"),
            ion_line_density_per_m=_number(discharge, "ion_line_density_per_m"),
        ),
        flow_shear_per_s=_number(record, "flow_shear_per_s"),
        registry=RegistryBinding(
            version=_string(registry, "version"),
            digest_sha256=_string(registry, "digest_sha256"),
        ),
    )


def configuration_from_bytes(data: bytes) -> DeviceConfiguration:
    """Build a validated configuration from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceConfigurationError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceConfigurationError(f"record: invalid JSON document: {exc}") from exc
    return configuration_from_record(record)
