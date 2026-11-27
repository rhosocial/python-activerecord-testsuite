# src/rhosocial/activerecord/testsuite/feature/rules/test_artifact_contract.py
"""Formal source: format-reference.md §4.11.3 (bare node) and §4.11.4
(untrusted input), with kind derivation from §4.11.1.

A written artifact is exactly ``{kind, params}``; the kind is computed from the
class and never stored on it; a nested expression is recognised by that shape
alone. A reader rejects leftover envelope fields, unknown or missing
parameters, and kinds its allowlist does not admit. No expression is probed
with ``getattr`` / ``hasattr``: class dictionaries, signatures and the public
serialize/deserialize functions answer every question here.
"""

import pytest

from rhosocial.activerecord.backend.expression.core import Literal
from rhosocial.activerecord.backend.expression.operators import ArithmeticOperation
from rhosocial.activerecord.backend.expression.registry import ExpressionRegistry
from rhosocial.activerecord.backend.expression.serialization import (
    ArtifactError,
    ExpressionDeserializationError,
    deserialize,
    serialize,
)
from rhosocial.activerecord.backend.expression.types import VarCharType
from rhosocial.activerecord.backend.expression.types.custom import CustomType

_READ_ERRORS = (ArtifactError, ExpressionDeserializationError)


def test_an_artifact_is_a_bare_node():
    artifact = serialize(VarCharType(length=255))
    assert set(artifact) == {"kind", "params"}
    assert artifact["kind"] == VarCharType.kind()
    assert artifact["params"] == {"length": 255, "spelling": "varchar"}


def test_kind_is_derived_from_the_class_and_never_stored():
    cls = type(VarCharType(length=10))
    assert "kind" not in vars(cls)
    assert serialize(VarCharType(length=10))["kind"] == serialize(VarCharType(length=20))["kind"]


def test_a_nested_node_is_recognised_by_shape_alone():
    artifact = serialize(ArithmeticOperation(None, "add", Literal(None, 1), Literal(None, 2)))
    for field in ("left", "right"):
        assert set(artifact["params"][field]) == {"kind", "params"}
    # §4.11.1's one exception: a literal's wire kind names its value.
    assert artifact["params"]["left"]["kind"] == serialize(Literal(None, 1))["kind"]
    assert artifact["params"]["left"]["kind"].startswith("integer_value")


def test_an_unknown_parameter_is_refused_by_name():
    with pytest.raises(ArtifactError, match="does not accept parameter"):
        deserialize({"kind": CustomType.kind(), "params": {"raw": "vector", "bogus": 1}})


def test_a_missing_required_parameter_is_refused_by_name():
    with pytest.raises(ArtifactError, match="missing required parameter"):
        deserialize({"kind": CustomType.kind(), "params": {}})


def test_a_leftover_envelope_field_is_refused():
    node = serialize(VarCharType(length=255))
    node["type"] = "rhosocial.activerecord.backend.expression.types.VarCharType"
    with pytest.raises(ArtifactError, match="unexpected field"):
        deserialize(node)


def test_an_unknown_kind_is_refused_without_an_import():
    with pytest.raises(_READ_ERRORS, match="not in the kind whitelist"):
        deserialize({"kind": "os.system", "params": {}})


def test_the_reader_allowlist_limits_what_it_may_produce():
    registry = ExpressionRegistry()
    registry.register_node(VarCharType)
    assert isinstance(deserialize(serialize(VarCharType(length=8)), registry=registry), VarCharType)
    with pytest.raises(_READ_ERRORS, match="not in the kind whitelist"):
        deserialize(serialize(Literal(None, 1)), registry=registry)
