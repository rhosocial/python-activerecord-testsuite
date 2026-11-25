# tests/rhosocial/activerecord/testsuite/feature/query/typed_column/test_supported_concepts.py
"""Capability concepts are read off declared attribute names, not patterns.

A dialect declares a data-type capability by defining
``format_data_type_<concept>``; that is the only place a contract can learn
what it renders. The reading is deliberately strict -- a name outside the shape
is not a capability -- so a contract test cannot be satisfied by an attribute
that only resembles one.
"""

from rhosocial.activerecord.testsuite.feature.query.typed_column.column_helpers import (
    supported_concepts,
)


class _Dialect:
    """A dialect stand-in whose capability family is exactly what it declares."""

    format_data_type_text = object()
    format_data_type_uuid = object()
    format_data_type_enum_variant = object()
    format_data_type_json_b2 = object()
    # Shape violations: not capabilities, so never reported.
    format_data_type_ = object()
    format_data_type_1uuid = object()
    format_data_type_UUID = object()
    format_data_typeuuid = object()
    format_other_type_text = object()


def test_only_declared_concepts_are_reported():
    assert supported_concepts(_Dialect()) == {
        "text",
        "uuid",
        "enum_variant",
        "json_b2",
    }


def test_a_name_outside_the_family_is_ignored():
    """``format_other_type_text`` shares a prefix but is not this family."""
    assert "other_type_text" not in supported_concepts(_Dialect())


def test_a_dialect_without_the_family_declares_nothing():
    class _Bare:
        pass

    assert supported_concepts(_Bare()) == set()
