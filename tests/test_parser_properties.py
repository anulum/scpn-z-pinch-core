# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — public parser property tests

"""Property and fuzz cases for the four public JSON parsers.

Each parser takes untrusted bytes. The contract under test is the same for
all four: for any input the parser either raises the package's own error
type or returns an object whose canonical bytes are exactly the input. No
other exception may escape, and no second byte form may be accepted for
one object. Inputs are arbitrary bytes, single-byte mutations of a valid
document, leaf substitutions with arbitrary JSON values, and deep nesting.
Hypothesis runs derandomised so the hosted gate is reproducible.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from test_configuration import synthetic_configuration

from geometry_fixtures import reference_geometry
from observability_fixtures import synthetic_plan
from scpn_z_pinch_core.configuration import configuration_from_bytes
from scpn_z_pinch_core.errors import (
    DeviceConfigurationError,
    DeviceGeometryError,
    DiagnosticPlanError,
)
from scpn_z_pinch_core.geometry import geometry_from_bytes
from scpn_z_pinch_core.observability import plan_from_bytes
from scpn_z_pinch_core.plan_envelope import envelope_from_bytes, envelope_from_record

ENVELOPE_FIXTURE = Path(__file__).parent / "data" / "plan_envelope_fixture.json"

PROPERTY_SETTINGS = settings(
    max_examples=200,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


class Canonical(Protocol):
    """Any parsed object that serialises canonically."""

    def canonical_bytes(self) -> bytes:
        """Return the canonical serialisation."""
        ...


@dataclass(frozen=True)
class Parser:
    """One public parser, its error type and one valid document.

    Attributes
    ----------
    name
        Test identifier.
    parse
        The public bytes parser.
    error
        The only exception type the parser may raise.
    valid
        Canonical bytes of one valid document.
    """

    name: str
    parse: Callable[[bytes], Canonical]
    error: type[Exception]
    valid: bytes


def _envelope_bytes() -> bytes:
    """Return the canonical bytes of the committed envelope fixture."""
    document = json.loads(ENVELOPE_FIXTURE.read_bytes().decode("utf-8"))
    return envelope_from_record(document["envelope"]).canonical_bytes()


PARSERS = (
    Parser(
        "configuration",
        configuration_from_bytes,
        DeviceConfigurationError,
        synthetic_configuration().canonical_bytes(),
    ),
    Parser(
        "plan",
        plan_from_bytes,
        DiagnosticPlanError,
        synthetic_plan().canonical_bytes(),
    ),
    Parser(
        "geometry",
        geometry_from_bytes,
        DeviceGeometryError,
        reference_geometry().canonical_bytes(),
    ),
    Parser("envelope", envelope_from_bytes, DiagnosticPlanError, _envelope_bytes()),
)

JSON_VALUES = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=20),
    lambda children: (
        st.lists(children, max_size=4)
        | st.dictionaries(st.text(max_size=10), children, max_size=4)
    ),
    max_leaves=12,
)


def assert_contract(parser: Parser, data: bytes) -> None:
    """Check the parser contract on one input.

    Parameters
    ----------
    parser
        Parser under test.
    data
        Arbitrary input bytes.
    """
    try:
        parsed = parser.parse(data)
    except parser.error:
        return
    assert parsed.canonical_bytes() == data


def _leaf_paths(value: Any, prefix: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    """List the paths of every leaf in a JSON value."""
    if isinstance(value, dict):
        return [
            path
            for key, child in value.items()
            for path in _leaf_paths(child, (*prefix, key))
        ]
    if isinstance(value, list):
        return [
            path
            for index, child in enumerate(value)
            for path in _leaf_paths(child, (*prefix, index))
        ]
    return [prefix]


def _replace(value: Any, path: tuple[Any, ...], new: Any) -> Any:
    """Return a copy of a JSON value with one leaf replaced."""
    if not path:
        return new
    head, *rest = path
    if isinstance(value, dict):
        return {**value, head: _replace(value[head], tuple(rest), new)}
    copy = list(value)
    copy[head] = _replace(copy[head], tuple(rest), new)
    return copy


def _canonical(value: Any) -> bytes:
    """Serialise a JSON value in the packages' canonical spelling."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return (text + "\n").encode("utf-8")


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
def test_valid_document_round_trips(parser: Parser) -> None:
    """The valid seed document is accepted and reproduced byte for byte."""
    assert parser.parse(parser.valid).canonical_bytes() == parser.valid


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
@PROPERTY_SETTINGS
@given(data=st.binary(max_size=2048))
def test_arbitrary_bytes_meet_the_contract(parser: Parser, data: bytes) -> None:
    """Arbitrary bytes are refused with the package error or reproduced."""
    assert_contract(parser, data)


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
@PROPERTY_SETTINGS
@given(position=st.integers(min_value=0), byte=st.integers(0, 255))
def test_single_byte_mutation_meets_the_contract(
    parser: Parser, position: int, byte: int
) -> None:
    """Any single-byte change of a valid document keeps the contract."""
    data = bytearray(parser.valid)
    data[position % len(data)] = byte
    assert_contract(parser, bytes(data))


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
@PROPERTY_SETTINGS
@given(choice=st.integers(min_value=0), new=JSON_VALUES)
def test_leaf_substitution_meets_the_contract(
    parser: Parser, choice: int, new: Any
) -> None:
    """Replacing any field with any JSON value keeps the contract."""
    record = json.loads(parser.valid)
    paths = _leaf_paths(record)
    mutated = _replace(record, paths[choice % len(paths)], new)
    assert_contract(parser, _canonical(mutated))


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
@pytest.mark.parametrize("opening", [b"[", b'{"a":'], ids=["array", "object"])
def test_deep_nesting_is_refused_with_the_package_error(
    parser: Parser, opening: bytes
) -> None:
    """Nesting deeper than the interpreter recursion limit is a parser error."""
    with pytest.raises(parser.error):
        parser.parse(opening * 100_000)


@pytest.mark.parametrize("parser", PARSERS, ids=lambda parser: parser.name)
def test_out_of_range_number_is_refused(parser: Parser) -> None:
    """A finite-looking literal that overflows to infinity is refused."""
    record = json.loads(parser.valid)
    for path in _leaf_paths(record):
        text = _canonical(_replace(record, path, 0.5)).replace(b"0.5", b"1e999", 1)
        assert_contract(parser, text)
        with pytest.raises(parser.error):
            parser.parse(text)
