# src/rhosocial/activerecord/testsuite/feature/basic/type_adapter/test_type_adapter_variants_async.py
"""Type-adapter variants: async declarations and value round-trips.

The async half shares the model declarations with its sync twin through one
mixin per variant (P4); it differs only in the configured model fixture and
the awaited save/read calls.
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
    AdapterRow,
    AdapterRowAnnotated,
    AsyncAdapterRow,
    AsyncAdapterRowAnnotated,
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


class TestAsyncTypeAdapterVariants:
    """Async declaration and value contracts for the adapter variants."""

    async def test_bare_model_has_no_declared_markers(self, async_adapter_row_class):
        """A bare field leaves adaptation entirely to the framework."""
        assert async_adapter_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in async_adapter_row_class.ddl_field_names():
            assert async_adapter_row_class.column_data_type(field) is None, field
            assert async_adapter_row_class.get_column_name(field) == field, field

    async def test_annotated_model_declares_adapter_and_column_class(
        self, async_adapter_row_annotated_class
    ):
        """The annotated variant renames, adapts and pins the column class."""
        annotated = async_adapter_row_annotated_class
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

    async def test_variants_share_one_table(
        self, async_adapter_row_class, async_adapter_row_annotated_class, database
    ):
        """Renaming and adapting do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(async_adapter_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(
            async_adapter_row_annotated_class, dialect
        ).to_sql()
        assert bare_ddl == annotated_ddl

    async def test_sync_async_twins_derive_identical_ddl(self, database):
        """A one-sided sync/async drift must fail (P4)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(AdapterRow, dialect).to_sql() == (
            build_create_table_statement(AsyncAdapterRow, dialect).to_sql()
        )
        assert build_create_table_statement(AdapterRowAnnotated, dialect).to_sql() == (
            build_create_table_statement(AsyncAdapterRowAnnotated, dialect).to_sql()
        )

    async def test_both_variants_round_trip_values(
        self, async_adapter_row_class, async_adapter_row_annotated_class, database
    ):
        """Both mappings write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = async_adapter_row_class(**_BARE_VALUES)
        assert await bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = await async_adapter_row_class.find_one(bare.id)
        for field, value in _BARE_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = async_adapter_row_annotated_class(**_ANNOTATED_VALUES)
        assert await annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = await async_adapter_row_annotated_class.find_one(annotated.id)
        for field, value in _ANNOTATED_VALUES.items():
            assert getattr(found_annotated, field) == value, field
