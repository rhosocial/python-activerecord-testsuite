# src/rhosocial/activerecord/testsuite/feature/basic/types_complex/test_complex_variants.py
"""Sync contracts for the complex-type bare / annotated fixture pair.

Three questions are answered here:

1. do the two variants declare different storage while keeping the same
   Python types (README section 5, P2/P4);
2. can both tables be built and do their values round-trip;
3. does the section 8.1 capability metadata produce a skip reason that names
   the exact column and switch.
"""

import uuid

import pytest
from rhosocial.activerecord.backend.adapters import MacAddress, Point
from rhosocial.activerecord.backend.expression import BinaryColumn
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    CustomType,
    EnumType,
    IntegerType,
    IntervalType,
    XmlType,
)
from rhosocial.activerecord.base.derivation import build_create_table_statement
from rhosocial.activerecord.base.fields import UseAdapter, UseColumnType, UseSqlType

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
    """Canonical values for the nine common columns (elapsed stays NULL)."""
    return {
        "token": uuid.uuid4(),
        "payload": {"k": "value"},
        "tags": ["alpha", "beta"],
        "kind": ComplexKind.ALPHA,
        "raw": b"\x00\x01\x02",
        "nic": MacAddress.parse("01:23:45:67:89:ab"),
        "location": Point(1.5, 2.5),
    }


def test_common_python_types_are_identical():
    """Bare and annotated must describe the same Python value types (P2)."""
    for field in COMMON_FIELDS:
        assert ComplexRow.field_python_type(field) == ComplexRowAnnotated.field_python_type(field)
        assert ComplexRow.field_python_type(field) == AsyncComplexRow.field_python_type(field)
        assert ComplexRowAnnotated.field_python_type(
            field
        ) == AsyncComplexRowAnnotated.field_python_type(field)


def test_bare_declares_no_storage():
    """A bare field writes only its Python type: no DDL annotation at all."""
    for field in COMMON_FIELDS:
        assert ComplexRow.column_data_type(field) is None, field
        assert ComplexRow.column_comment(field) is None, field
        assert not ComplexRow.column_indexes(field), field


def test_annotated_declares_section5_annotations():
    """Every annotation named in README section 5 is present on its column."""
    annotated = ComplexRowAnnotated

    declared = annotated.column_data_type("id")
    assert isinstance(declared, UseSqlType)
    assert declared.data_types == (IntegerType(),)

    assert [index.name for index in annotated.column_indexes("token")] == [
        "ix_complex_rows_annotated_token"
    ]
    assert "payload" in annotated.column_comment("payload")

    tags = annotated.column_data_type("tags")
    assert isinstance(tags, UseSqlType)
    assert isinstance(tags.data_types[0], ArrayType)

    elapsed = annotated.column_data_type("elapsed")
    assert isinstance(elapsed, UseSqlType)
    assert isinstance(elapsed.data_types[0], IntervalType)

    kind = annotated.column_data_type("kind")
    assert isinstance(kind, UseSqlType)
    assert isinstance(kind.data_types[0], EnumType)

    raw_type = annotated.column_type("raw")
    assert isinstance(raw_type, UseColumnType)
    assert BinaryColumn in raw_type.column_classes

    assert any(isinstance(marker, UseAdapter) for marker in annotated.column_annotations("nic"))

    location = annotated.column_data_type("location")
    assert isinstance(location, UseSqlType)
    assert isinstance(location.data_types[0], CustomType)

    # Dimensional families and XML exist only on the annotated table.
    assert "heading" not in ComplexRow.ddl_field_names()
    assert "markup" not in ComplexRow.ddl_field_names()
    assert "heading" in annotated.ddl_field_names()
    assert isinstance(annotated.column_data_type("markup").data_types[0], XmlType)


def test_sync_async_twins_derive_identical_ddl(database, schema):
    """A one-sided sync/async drift must fail (P4)."""
    dialect = database.dialect
    assert build_create_table_statement(ComplexRow, dialect).to_sql() == (
        build_create_table_statement(AsyncComplexRow, dialect).to_sql()
    )
    assert build_create_table_statement(ComplexRowAnnotated, dialect).to_sql() == (
        build_create_table_statement(AsyncComplexRowAnnotated, dialect).to_sql()
    )


def test_both_variants_round_trip_values(complex_bare_class, complex_annotated_class):
    """The declared tables can be written and read on the configured backend."""
    for model in (complex_bare_class, complex_annotated_class):
        values = _row_values()
        saved = model(**values)
        assert saved.save() == 1

        loaded = model.find_one(saved.id)
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
        # The duration is left NULL: no portable DML converter exists for a
        # bare timedelta on every backend's driver.
        assert loaded.elapsed is None


def test_operation_reason_names_column_and_switch():
    """A refused switch is reported against the column that requires it."""
    operation = Operation("insert", requires_on=("json",), column="payload")
    assert operation_reason(_AnsweringDialect(json=True), operation) is None
    reason = operation_reason(_AnsweringDialect(json=False), operation)
    assert "insert on column payload" in reason
    assert "json" in reason


def test_table_reason_picks_the_first_refused_column():
    """The registry points at one column, not at the whole table."""
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
        )
    }
    assert table_reason(_AnsweringDialect(**all_on), COMPLEX_FIXTURES[0]) is None

    refused = dict(all_on, mac=False)
    reason = table_reason(_AnsweringDialect(**refused), COMPLEX_FIXTURES[0])
    assert "nic" in reason
    assert "mac" in reason
    assert "payload" not in reason


def test_requires_off_switch():
    """``requires_off`` refuses a dialect that *does* answer the switch."""
    operation = Operation("create_table", requires_off=("xml",), column="markup")
    assert operation_reason(_AnsweringDialect(xml=False), operation) is None
    assert "markup" in operation_reason(_AnsweringDialect(xml=True), operation)


def test_unanswered_switch_is_a_failure():
    """A switch nobody answered is a dialect gap, never a silent skip."""
    operation = Operation("insert", requires_on=("never_answered",), column="token")
    with pytest.raises(MissingRequirementError):
        operation_reason(_AnsweringDialect(), operation)
