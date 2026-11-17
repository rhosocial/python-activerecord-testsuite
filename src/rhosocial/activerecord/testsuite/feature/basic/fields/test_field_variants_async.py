# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_field_variants_async.py
"""Field-mapping variants: async declarations and value round-trips.

The async half shares the model declarations with its sync twin through one
mixin per variant (P4); it differs only in the configured model fixture and
the awaited save/read calls.
"""

from decimal import Decimal

import pytest
from rhosocial.activerecord.base import DerivedField, UseAdapter, UseColumn
from rhosocial.activerecord.base.derivation import build_create_table_statement

from rhosocial.activerecord.testsuite.feature.basic.fixtures.field_models import (
    FIELD_VARIANT_FIXTURES,
    AsyncFieldRow,
    AsyncFieldRowAnnotated,
    FieldRow,
    FieldRowAnnotated,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    operation_reason,
    table_reason,
)

BARE_FIXTURE = FIELD_VARIANT_FIXTURES[0]
ANNOTATED_FIXTURE = FIELD_VARIANT_FIXTURES[0]

_BARE_VALUES = {"label": "alpha", "amount": Decimal("12.50"), "count": 7}
_ANNOTATED_VALUES = {"title": "alpha", "amount": Decimal("12.50"), "total": 7}
_EXPECTED_COLUMNS = ("id", "label", "amount", "count")


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


class TestAsyncFieldVariants:
    """Async declaration and value contracts for the field-mapping variants."""

    async def test_bare_model_has_no_declared_markers(self, async_field_row_class):
        """A bare field leaves mapping entirely to the framework."""
        assert async_field_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in async_field_row_class.ddl_field_names():
            assert async_field_row_class.column_data_type(field) is None, field
            assert async_field_row_class.get_column_name(field) == field, field

    async def test_annotated_model_declares_mapping_and_adapter(
        self, async_field_row_annotated_class
    ):
        """The annotated variant renames columns, adapts a value and derives a field."""
        annotated = async_field_row_annotated_class
        assert tuple(annotated.get_column_name(f) for f in annotated.ddl_field_names()) == (
            _EXPECTED_COLUMNS
        )
        assert annotated.get_column_name("title") == "label"
        assert annotated.get_column_name("total") == "count"

        annotations = {type(marker) for marker in annotated.column_annotations("total")}
        assert UseColumn in annotations, "total lost its UseColumn rename"
        assert UseAdapter in annotations, "total lost its UseAdapter"
        assert isinstance(
            getattr(annotated, "discounted", None), DerivedField
        ), "the derived field was dropped"

    async def test_variants_share_one_table(
        self, async_field_row_class, async_field_row_annotated_class, database
    ):
        """Renaming and adapting do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(async_field_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(
            async_field_row_annotated_class, dialect
        ).to_sql()
        assert bare_ddl == annotated_ddl

    async def test_sync_async_twins_derive_identical_ddl(self, database):
        """A one-sided sync/async drift must fail (P4)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(FieldRow, dialect).to_sql() == (
            build_create_table_statement(AsyncFieldRow, dialect).to_sql()
        )
        assert build_create_table_statement(FieldRowAnnotated, dialect).to_sql() == (
            build_create_table_statement(AsyncFieldRowAnnotated, dialect).to_sql()
        )

    async def test_both_variants_round_trip_values(
        self, async_field_row_class, async_field_row_annotated_class, database
    ):
        """Both mappings write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = async_field_row_class(**_BARE_VALUES)
        assert await bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = await async_field_row_class.find_one(bare.id)
        for field, value in _BARE_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = async_field_row_annotated_class(**_ANNOTATED_VALUES)
        assert await annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = await async_field_row_annotated_class.find_one(annotated.id)
        for field, value in _ANNOTATED_VALUES.items():
            assert getattr(found_annotated, field) == value, field
