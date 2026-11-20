# src/rhosocial/activerecord/testsuite/feature/basic/validation/test_validation_variants.py
"""Validation variants: bare fields and Pydantic-annotated fields.

Pydantic constraints and validators are validation semantics, not storage
declarations (README section 2 P2), so both models bind to one
``validated_rows`` table.  The tests answer three questions:

* does the bare model accept any value of the right Python type?
* does the annotated model declare the constraints and refuse invalid values?
* do both variants still round-trip their values through the same table?

Sync and async halves share one mixin per variant (P4).
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


class TestValidationVariants:
    """Declaration and behavior contracts for the two validation variants."""

    def test_bare_model_has_no_validation_markers(self, plain_validated_row_class):
        """A bare model has no Pydantic constraints on its fields."""
        assert plain_validated_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in _EXPECTED_COLUMNS:
            assert plain_validated_row_class.model_fields[field].metadata == [], field
        # No validation: every value of the right Python type is accepted.
        row = plain_validated_row_class(**_INVALID_VALUES)
        assert row.code == "bad"
        assert row.quantity == 0

    def test_annotated_model_declares_validation(self, validated_row_class):
        """The annotated model carries constraints and validators."""
        assert validated_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        assert validated_row_class.model_fields[
            "quantity"
        ].metadata, "quantity lost its Field constraints"
        assert validated_row_class.model_fields["code"].metadata, "code lost its pattern"
        row = validated_row_class(**_VALID_VALUES)
        assert row.label == "alice", "the field validator should normalize the label"
        with pytest.raises(ValidationError) as exc_info:
            validated_row_class(**_INVALID_VALUES)
        errors = str(exc_info.value)
        for field in ("code", "quantity", "price", "label"):
            assert field in errors, "invalid {} was accepted".format(field)

    def test_variants_share_one_table(
        self, plain_validated_row_class, validated_row_class, database
    ):
        """Validation annotations do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(plain_validated_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(validated_row_class, dialect).to_sql()
        assert bare_ddl == annotated_ddl

    def test_sync_async_twins_derive_identical_ddl(
        self, plain_validated_row_class, validated_row_class, database
    ):
        """A one-sided sync/async drift must fail (P4)."""
        from rhosocial.activerecord.testsuite.feature.basic.fixtures.validation_models import (
            AsyncPlainValidatedRow,
            AsyncValidatedRow,
        )

        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(plain_validated_row_class, dialect).to_sql() == (
            build_create_table_statement(AsyncPlainValidatedRow, dialect).to_sql()
        )
        assert build_create_table_statement(validated_row_class, dialect).to_sql() == (
            build_create_table_statement(AsyncValidatedRow, dialect).to_sql()
        )

    def test_both_variants_round_trip_values(
        self, plain_validated_row_class, validated_row_class, database
    ):
        """Both models write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = plain_validated_row_class(**_VALID_VALUES)
        assert bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = plain_validated_row_class.find_one(bare.id)
        for field, value in _VALID_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = validated_row_class(**_VALID_VALUES)
        assert annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = validated_row_class.find_one(annotated.id)
        assert found_annotated.label == "alice", "the normalized label must be persisted"
        for field in ("code", "quantity", "price"):
            assert getattr(found_annotated, field) == _VALID_VALUES[field], field
