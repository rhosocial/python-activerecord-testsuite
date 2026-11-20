# src/rhosocial/activerecord/testsuite/feature/basic/validation/test_validation_variants_async.py
"""Validation variants: async declarations and value round-trips.

The async half shares the model declarations with its sync twin through one
mixin per variant (P4); it differs only in the configured model fixture and
the awaited save/read calls.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError
from rhosocial.activerecord.base.derivation import build_create_table_statement

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    operation_reason,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.validation_models import (
    VALIDATION_VARIANT_FIXTURES,
    AsyncPlainValidatedRow,
    AsyncValidatedRow,
    PlainValidatedRow,
    ValidatedRow,
)

BARE_FIXTURE = VALIDATION_VARIANT_FIXTURES[0]
ANNOTATED_FIXTURE = VALIDATION_VARIANT_FIXTURES[0]

_EXPECTED_COLUMNS = ("id", "code", "quantity", "price", "label")
_VALID_VALUES = {
    "code": "ABC-123",
    "quantity": 5,
    "price": Decimal("12.50"),
    "label": "  ALICE  ",
}
_INVALID_VALUES = {
    "code": "bad",
    "quantity": 0,
    "price": Decimal("-1"),
    "label": "",
}


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


class TestAsyncValidationVariants:
    """Async declaration and behavior contracts for the validation variants."""

    async def test_bare_model_has_no_validation_markers(self, async_plain_validated_row_class):
        """A bare model has no Pydantic constraints on its fields."""
        assert async_plain_validated_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in _EXPECTED_COLUMNS:
            assert async_plain_validated_row_class.model_fields[field].metadata == [], field
        row = async_plain_validated_row_class(**_INVALID_VALUES)
        assert row.code == "bad"
        assert row.quantity == 0

    async def test_annotated_model_declares_validation(self, async_validated_row_class):
        """The annotated model carries constraints and validators."""
        assert async_validated_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        assert async_validated_row_class.model_fields[
            "quantity"
        ].metadata, "quantity lost its Field constraints"
        assert async_validated_row_class.model_fields["code"].metadata, "code lost its pattern"
        row = async_validated_row_class(**_VALID_VALUES)
        assert row.label == "alice", "the field validator should normalize the label"
        with pytest.raises(ValidationError) as exc_info:
            async_validated_row_class(**_INVALID_VALUES)
        errors = str(exc_info.value)
        for field in ("code", "quantity", "price", "label"):
            assert field in errors, "invalid {} was accepted".format(field)

    async def test_variants_share_one_table(
        self, async_plain_validated_row_class, async_validated_row_class, database
    ):
        """Validation annotations do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(async_plain_validated_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(async_validated_row_class, dialect).to_sql()
        assert bare_ddl == annotated_ddl

    async def test_sync_async_twins_derive_identical_ddl(self, database):
        """A one-sided sync/async drift must fail (P4)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(PlainValidatedRow, dialect).to_sql() == (
            build_create_table_statement(AsyncPlainValidatedRow, dialect).to_sql()
        )
        assert build_create_table_statement(ValidatedRow, dialect).to_sql() == (
            build_create_table_statement(AsyncValidatedRow, dialect).to_sql()
        )

    async def test_both_variants_round_trip_values(
        self, async_plain_validated_row_class, async_validated_row_class, database
    ):
        """Both models write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = async_plain_validated_row_class(**_VALID_VALUES)
        assert await bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = await async_plain_validated_row_class.find_one(bare.id)
        for field, value in _VALID_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = async_validated_row_class(**_VALID_VALUES)
        assert await annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = await async_validated_row_class.find_one(annotated.id)
        assert found_annotated.label == "alice", "the normalized label must be persisted"
        for field in ("code", "quantity", "price"):
            assert getattr(found_annotated, field) == _VALID_VALUES[field], field
