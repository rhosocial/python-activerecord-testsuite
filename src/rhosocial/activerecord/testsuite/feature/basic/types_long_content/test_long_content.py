# src/rhosocial/activerecord/testsuite/feature/basic/types_long_content/test_long_content.py
"""Synchronous long-content contract: round-trip, capacity, capability skip.

The four content columns are declared with ``length=16000`` (text/blob) or kept
small enough for Oracle's 4 000-byte JSON/XML carrier. This file also checks the
capability metadata that lets a backend skip the group with a named reason, and
the sync/async DDL parity required by P4.
"""

from rhosocial.activerecord.backend.impl.dummy.dialect import DummyDialect
from rhosocial.activerecord.base.derivation import (
    build_create_table_statement,
    build_drop_table_statement,
)

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    operation_reason,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_long_content_models import (
    DOCUMENT_VALUE,
    LONG_BYTES,
    LONG_CONTENT_FIXTURES,
    LONG_TEXT,
    MARKUP_VALUE,
    AsyncLongRow,
    LongRow,
)

_FIXTURE = LONG_CONTENT_FIXTURES[0]


class _Refuses(DummyDialect):
    """A dummy dialect that answers ``False`` for one storage concept."""

    name = "Refuses"

    def __init__(self, concept):
        super().__init__()
        self._concept = concept

    def supports_data_types(self):
        table = super().supports_data_types()
        table[self._concept] = False
        return table


def _operation_for(column):
    for operation in _FIXTURE.operations:
        if operation.column == column:
            return operation
    raise AssertionError("no operation registered for column {!r}".format(column))


class TestLongContent:
    """Round-trip and capacity assertions against a configured backend."""

    def test_long_values_round_trip(self, schema, long_row_class):
        """A value at each declared minimum survives write and read-back."""
        row = long_row_class(
            body=LONG_TEXT,
            raw=LONG_BYTES,
            document=DOCUMENT_VALUE,
            markup=MARKUP_VALUE,
        )
        assert row.save() == 1
        assert row.id is not None

        found = long_row_class.find_one(row.id)
        assert found is not None
        assert found.body == LONG_TEXT
        assert len(found.body) == 16000
        assert found.raw == LONG_BYTES
        assert len(found.raw) == 16000
        assert found.document == DOCUMENT_VALUE
        assert found.markup == MARKUP_VALUE

    def test_length_is_a_minimum_not_a_width(self, schema, long_row_class):
        """``length=16000`` is a floor: one more unit still round-trips."""
        assert LongRow.column_data_type("body").data_type.length == 16000
        assert LongRow.column_data_type("raw").data_type.length == 16000
        # json/xml carry no length yet; their content is designed to fit.
        assert LongRow.column_data_type("document").data_type.length is None
        assert LongRow.column_data_type("markup").data_type.length is None

        row = long_row_class(
            body=LONG_TEXT + "X",
            raw=LONG_BYTES + b"\x00",
            document=DOCUMENT_VALUE,
            markup=MARKUP_VALUE,
        )
        assert row.save() == 1
        found = long_row_class.find_one(row.id)
        assert len(found.body) == 16001
        assert len(found.raw) == 16001
        assert found.body.endswith("X")
        assert found.raw.endswith(b"\x00")


def test_a_fully_supporting_dialect_has_no_skip_reason():
    """The dummy dialect renders all four concepts, so nothing is skipped."""
    assert table_reason(DummyDialect(), _FIXTURE) is None


def test_a_refused_concept_names_its_column_and_switch():
    """Per-column registration makes the skip reason actionable."""
    why = table_reason(_Refuses("json"), _FIXTURE)
    assert why is not None
    assert "document" in why
    assert "json" in why
    assert operation_reason(_Refuses("json"), _operation_for("document")) == why

    why_xml = table_reason(_Refuses("xml"), _FIXTURE)
    assert why_xml is not None
    assert "markup" in why_xml
    assert "xml" in why_xml

    # The other columns are unaffected by that same answer.
    assert operation_reason(_Refuses("json"), _operation_for("body")) is None
    assert operation_reason(_Refuses("xml"), _operation_for("raw")) is None


def test_sync_async_twins_derive_identical_ddl():
    """P4: the two twins must not drift on either DDL statement."""
    dialect = DummyDialect()
    for builder in (build_create_table_statement, build_drop_table_statement):
        assert builder(LongRow, dialect).to_sql() == builder(AsyncLongRow, dialect).to_sql()
