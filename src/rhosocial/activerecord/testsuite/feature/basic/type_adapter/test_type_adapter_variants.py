# src/rhosocial/activerecord/testsuite/feature/basic/type_adapter/test_type_adapter_variants.py
"""Type-adapter variants: bare declarations and adapter annotations.

``UseColumn``, ``UseAdapter`` and ``UseColumnType`` change how a value is
mapped, not the stored columns, so both models bind to one ``adapter_rows``
table.  The tests assert that the bare model writes no marker, that the
annotated model declares the rename/adapter/column class yet derives the same
DDL, and that the adapted value still round-trips.

Sync and async halves share one mixin per variant (P4).
"""

import pytest
from rhosocial.activerecord.base import UseAdapter, UseColumn, UseColumnType
from rhosocial.activerecord.base.derivation import build_create_table_statement

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    operation_reason,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.type_adapter_models import (
    TYPE_ADAPTER_VARIANT_FIXTURES,
)

BARE_FIXTURE = TYPE_ADAPTER_VARIANT_FIXTURES[0]
ANNOTATED_FIXTURE = TYPE_ADAPTER_VARIANT_FIXTURES[0]

_BARE_VALUES = {"label": "alpha", "count": 7}
_ANNOTATED_VALUES = {"title": "alpha", "scaled": 7}
_EXPECTED_COLUMNS = ("id", "label", "count")


def _skip_unless(dialect, fixture, operation_name):
    """Skip with the registry's named reason, never with a made-up one."""
    reason = table_reason(dialect, fixture)
    if reason is not None:
        pytest.skip(reason)
    for operation in fixture.operations:
        if operation.name == operation_name:
            reason = operation_reason(dialect, operation)
            if reason is not None:
                pytest.skip(reason)


class TestTypeAdapterVariants:
    """Declaration and value contracts for the two adapter variants."""

    def test_bare_model_has_no_declared_markers(self, adapter_row_class):
        """A bare field leaves adaptation entirely to the framework."""
        assert adapter_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in adapter_row_class.ddl_field_names():
            assert adapter_row_class.column_data_type(field) is None, field
            assert adapter_row_class.get_column_name(field) == field, field

    def test_annotated_model_declares_adapter_and_column_class(self, adapter_row_annotated_class):
        """The annotated variant renames, adapts and pins the column class."""
        annotated = adapter_row_annotated_class
        assert tuple(annotated.get_column_name(f) for f in annotated.ddl_field_names()) == (
            _EXPECTED_COLUMNS
        )
        assert annotated.get_column_name("title") == "label"
        assert annotated.get_column_name("scaled") == "count"

        annotations = {type(marker) for marker in annotated.column_annotations("scaled")}
        assert UseColumn in annotations, "scaled lost its UseColumn rename"
        assert UseAdapter in annotations, "scaled lost its UseAdapter"
        assert UseColumnType in annotations, "scaled lost its UseColumnType"
        assert annotated.column_type("scaled") is not None

    def test_variants_share_one_table(
        self, adapter_row_class, adapter_row_annotated_class, database
    ):
        """Renaming and adapting do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(adapter_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(adapter_row_annotated_class, dialect).to_sql()
        assert bare_ddl == annotated_ddl

    def test_sync_async_twins_derive_identical_ddl(
        self, adapter_row_class, adapter_row_annotated_class, database
    ):
        """A one-sided sync/async drift must fail (P4)."""
        from rhosocial.activerecord.testsuite.feature.basic.fixtures.type_adapter_models import (
            AsyncAdapterRow,
            AsyncAdapterRowAnnotated,
        )

        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(adapter_row_class, dialect).to_sql() == (
            build_create_table_statement(AsyncAdapterRow, dialect).to_sql()
        )
        assert build_create_table_statement(adapter_row_annotated_class, dialect).to_sql() == (
            build_create_table_statement(AsyncAdapterRowAnnotated, dialect).to_sql()
        )

    def test_both_variants_round_trip_values(
        self, adapter_row_class, adapter_row_annotated_class, database
    ):
        """Both mappings write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = adapter_row_class(**_BARE_VALUES)
        assert bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = adapter_row_class.find_one(bare.id)
        for field, value in _BARE_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = adapter_row_annotated_class(**_ANNOTATED_VALUES)
        assert annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = adapter_row_annotated_class.find_one(annotated.id)
        for field, value in _ANNOTATED_VALUES.items():
            assert getattr(found_annotated, field) == value, field
