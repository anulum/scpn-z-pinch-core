# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device configuration container tests

"""Every branch of the device configuration container and its parsers.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import pytest

from scpn_z_pinch_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_z_pinch_core.errors import DeviceConfigurationError
from scpn_z_pinch_core.parameters import Discharge, PinchColumn

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)


def synthetic_configuration(
    identifier: str = "sheared_flow_z_pinch",
    flow_shear_per_s: float = 1.0e6,
    peak_current_ma: float = 0.1,
) -> DeviceConfiguration:
    """Build a valid synthetic configuration with optional overrides."""
    return DeviceConfiguration(
        identifier=identifier,
        column=PinchColumn(column_radius_m=0.005, column_length_m=0.5),
        discharge=Discharge(
            peak_current_ma=peak_current_ma,
            ion_line_density_per_m=1.0e18,
        ),
        flow_shear_per_s=flow_shear_per_s,
        registry=REGISTRY,
    )


def test_registry_binding_rejects_bad_pins() -> None:
    """Malformed registry pins are rejected."""
    with pytest.raises(DeviceConfigurationError, match=r"registry\.version"):
        RegistryBinding(version="", digest_sha256="0" * 64)
    with pytest.raises(DeviceConfigurationError, match=r"registry\.digest_sha256"):
        RegistryBinding(version="1.0.0", digest_sha256="ZZ")


def test_both_owned_identifiers_construct() -> None:
    """Each owned identifier constructs with its class-consistent shear."""
    sheared = synthetic_configuration()
    static = synthetic_configuration("z_pinch", flow_shear_per_s=0.0)
    assert sheared.identifier == "sheared_flow_z_pinch"
    assert static.flow_shear_per_s == 0.0


def test_unowned_identifier_is_rejected() -> None:
    """Identifiers outside this repository's ownership are rejected."""
    with pytest.raises(DeviceConfigurationError, match="not owned"):
        synthetic_configuration("theta_pinch")


def test_shear_class_invariants() -> None:
    """Shear declarations must match the configuration class exactly."""
    with pytest.raises(DeviceConfigurationError, match="strictly"):
        synthetic_configuration(flow_shear_per_s=0.0)
    with pytest.raises(DeviceConfigurationError, match="exactly"):
        synthetic_configuration("z_pinch", flow_shear_per_s=1.0)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        synthetic_configuration(flow_shear_per_s=math.nan)


def test_consistency_report_clean_and_finding() -> None:
    """The report is empty in-window and precise outside it."""
    assert synthetic_configuration().consistency_report() == ()
    hot = synthetic_configuration(peak_current_ma=100.0)
    findings = hot.consistency_report()
    assert len(findings) == 1
    assert "Bennett temperature" in findings[0].message


def test_canonical_round_trip_and_digest() -> None:
    """Canonical bytes round-trip losslessly and digest deterministically."""
    configuration = synthetic_configuration()
    data = configuration.canonical_bytes()
    assert data.endswith(b"\n")
    restored = configuration_from_bytes(data)
    assert restored == configuration
    expected = hashlib.sha256(data).hexdigest()
    assert configuration.digest_sha256() == expected


def test_from_record_round_trip_both_classes() -> None:
    """Both owned configuration classes round-trip through records."""
    for configuration in (
        synthetic_configuration(),
        synthetic_configuration("z_pinch", flow_shear_per_s=0.0),
    ):
        assert configuration_from_record(configuration.to_record()) == configuration


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda _: "not-a-dict", "record: must be an object"),
        (lambda r: {**r, "extra": 1}, "unknown fields"),
        (lambda r: {**r, "column": None}, "column: must be an object"),
        (lambda r: {**r, "discharge": []}, "discharge: must be an object"),
        (lambda r: {**r, "registry": 7}, "registry: must be an object"),
        (lambda r: {**r, "identifier": 3}, "identifier: must be a string"),
        (
            lambda r: {**r, "flow_shear_per_s": "fast"},
            "flow_shear_per_s: must be a number",
        ),
    ],
)
def test_from_record_shape_violations(mutate: Any, fragment: str) -> None:
    """Each record-shape violation is rejected with a precise message."""
    record = synthetic_configuration().to_record()
    with pytest.raises(DeviceConfigurationError, match=fragment):
        configuration_from_record(mutate(record))


def test_from_record_field_type_violations() -> None:
    """Nested field-type violations name the offending field."""
    record = synthetic_configuration().to_record()
    record["column"]["column_radius_m"] = "big"
    with pytest.raises(DeviceConfigurationError, match="column_radius_m: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["discharge"]["peak_current_ma"] = True
    with pytest.raises(DeviceConfigurationError, match="peak_current_ma: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["registry"]["version"] = None
    with pytest.raises(DeviceConfigurationError, match="version: must be a string"):
        configuration_from_record(record)


def test_from_bytes_rejects_invalid_documents() -> None:
    """Invalid UTF-8, invalid JSON, and non-finite literals are rejected."""
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"\xff\xfe")
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"{not json")
    record = synthetic_configuration().to_record()
    text = json.dumps(record).replace("0.005", "NaN", 1)
    with pytest.raises(DeviceConfigurationError, match="non-finite JSON literal"):
        configuration_from_bytes(text.encode("utf-8"))


def test_integer_accepted_where_number_expected() -> None:
    """Integral JSON numbers are accepted for real-valued fields."""
    record = synthetic_configuration().to_record()
    record["flow_shear_per_s"] = 1000000
    restored = configuration_from_record(record)
    assert restored.flow_shear_per_s == 1.0e6
