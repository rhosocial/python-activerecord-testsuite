# src/rhosocial/activerecord/testsuite/feature/basic/types_complex/test_complex_variants_async.py
"""Async twins of the ``types_complex`` contracts.

The async models share their field declarations with the sync ones (P4), so
these tests check that the same declarations build the same tables and carry
the same values through the async backend.  The capability-metadata contract
is repeated against the async model list so both halves of the pair register
the same per-column switches.
"""

import uuid

import pytest
from rhosocial.activerecord.backend.adapters import MacAddress, Point
from rhosocial.activerecord.backend.expression import BinaryColumn, XMLColumn
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    CustomType,
    EnumType,
    IntervalType,
    XmlType,
)
from rhosocial.activerecord.base.derivation import build_create_table_statement
from rhosocial.activerecord.base.fields import UseAdapter, UseSqlType

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    Operation,
    operation_reason,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_complex_models import (
    COMPLEX_FIXTURES,
    AsyncComplexRow,
    AsyncComplexRowAnnotated,
    ComplexKind,
    ComplexRow,
    ComplexRowAnnotated,
)
from rhosocial.activerecord.testsuite.pytest_plugin.requirements import (
    MissingRequirementError,
)

COMMON_FIELDS = (
    "id",
    "token",
    "payload",
    "tags",
    "elapsed",
    "kind",
    "raw",
    "nic",
    "location",
)


class _AnsweringDialect:
    """A dialect stub whose only answers are the given concept switches."""

    name = "stub"

    def __init__(self, **answers):
        self._answers = answers

    def __getattr__(self, name):
        # A declared concept answers through a zero-argument switch of the
        # same name (the capability-protocol channel): True = renders, False =
        # explicitly does not render. Unknown names raise (unanswered).
        if name in self._answers:
            value = self._answers[name]
            return lambda: bool(value)
        raise AttributeError(name)


def _row_values():
    return {
        "token": uuid.uuid4(),
        "payload": {"k": "value"},
        "tags": ["alpha", "beta"],
        "kind": ComplexKind.ALPHA,
        "raw": b"\x00\x01\x02",
        "nic": MacAddress.parse("01:23:45:67:89:ab"),
        "location": Point(1.5, 2.5),
    }


def test_async_python_types_match_both_sync_variants():
    for field in COMMON_FIELDS:
        assert AsyncComplexRow.field_python_type(field) == ComplexRow.field_python_type(field)
        assert AsyncComplexRowAnnotated.field_python_type(
            field
        ) == ComplexRowAnnotated.field_python_type(field)


def test_async_annotated_declarations_match_sync():
    for field in COMMON_FIELDS:
        assert AsyncComplexRowAnnotated.column_data_type(field) == (
            ComplexRowAnnotated.column_data_type(field)
        )
        assert AsyncComplexRowAnnotated.column_type(field) == (
            ComplexRowAnnotated.column_type(field)
        )

    declared = AsyncComplexRowAnnotated.column_data_type("id")
    assert isinstance(declared, UseSqlType)
    assert isinstance(AsyncComplexRowAnnotated.column_data_type("tags").data_types[0], ArrayType)
    assert isinstance(
        AsyncComplexRowAnnotated.column_data_type("elapsed").data_types[0], IntervalType
    )
    assert isinstance(AsyncComplexRowAnnotated.column_data_type("kind").data_types[0], EnumType)
    assert isinstance(
        AsyncComplexRowAnnotated.column_data_type("location").data_types[0], CustomType
    )
    assert BinaryColumn in AsyncComplexRowAnnotated.column_type("raw").column_classes
    assert XMLColumn in AsyncComplexRowAnnotated.column_type("markup").column_classes
    assert any(
        isinstance(marker, UseAdapter)
        for marker in AsyncComplexRowAnnotated.column_annotations("nic")
    )
    assert isinstance(AsyncComplexRowAnnotated.column_data_type("markup").data_types[0], XmlType)
    assert [index.name for index in AsyncComplexRowAnnotated.column_indexes("token")] == [
        "ix_complex_rows_annotated_token"
    ]


def test_async_twins_derive_identical_ddl(database, schema):
    dialect = database.dialect
    assert build_create_table_statement(AsyncComplexRow, dialect).to_sql() == (
        build_create_table_statement(ComplexRow, dialect).to_sql()
    )
    assert build_create_table_statement(AsyncComplexRowAnnotated, dialect).to_sql() == (
        build_create_table_statement(ComplexRowAnnotated, dialect).to_sql()
    )


async def test_async_both_variants_round_trip_values(
    async_complex_bare_class, async_complex_annotated_class
):
    for model in (async_complex_bare_class, async_complex_annotated_class):
        values = _row_values()
        saved = model(**values)
        assert await saved.save() == 1

        loaded = await model.find_one(saved.id)
        assert loaded.token == values["token"]
        assert loaded.payload == values["payload"]
        assert loaded.tags == values["tags"]
        assert loaded.kind == values["kind"]
        assert loaded.raw == values["raw"]
        assert loaded.nic == values["nic"]
        assert (loaded.location.x, loaded.location.y) == (
            values["location"].x,
            values["location"].y,
        )
        assert loaded.elapsed is None


def test_async_capability_reasons():
    """The same per-column registry is used from the async test module."""
    operation = Operation("insert", requires_on=("array",), column="tags")
    assert operation_reason(_AnsweringDialect(array=True), operation) is None
    assert "tags" in operation_reason(_AnsweringDialect(array=False), operation)

    all_on = {
        switch: True
        for switch in (
            "integer",
            "uuid",
            "json",
            "array",
            "interval",
            "enum",
            "blob",
            "mac",
            "geometry",
            "vector",
            "xml",
        )
    }
    assert table_reason(_AnsweringDialect(**all_on), COMPLEX_FIXTURES[1]) is None

    refused = dict(all_on, geometry=False)
    reason = table_reason(_AnsweringDialect(**refused), COMPLEX_FIXTURES[1])
    assert "location" in reason
    assert "geometry" in reason

    with pytest.raises(MissingRequirementError):
        operation_reason(
            _AnsweringDialect(), Operation("insert", requires_on=("vector",), column="heading")
        )
