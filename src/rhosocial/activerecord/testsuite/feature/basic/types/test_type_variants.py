# src/rhosocial/activerecord/testsuite/feature/basic/types/test_type_variants.py
"""Scalar type variants: bare declarations and fully annotated declarations.

Three questions, in that order:

* does a field write no DDL marker at all, or the full declaration from
  README section 4?
* can both variants create their table and give every Python value back
  unchanged?
* when a dialect refuses a storage concept, does the registry say which
  operation and which column it was?

The sync and async halves differ only in the configured model fixture; the
declarations under test are shared through one mixin per variant (P4).
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from rhosocial.activerecord.backend.expression.statements import (
    ColumnDefaultConstraint,
    ColumnUniqueConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    BooleanType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    TextType,
    TimestampType,
    TimeType,
    VarCharType,
)
from rhosocial.activerecord.base import UseSqlType

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    operation_reason,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_models import (
    MICROSECOND_FIXTURES,
    TYPED_FIELD_NAMES,
    TYPES_FIXTURES,
)
from rhosocial.activerecord.testsuite.utils import assert_datetime_equal

BARE_FIXTURE = TYPES_FIXTURES[0]
ANNOTATED_FIXTURE = TYPES_FIXTURES[1]
MICROSECOND_FIXTURE = MICROSECOND_FIXTURES[0]

_EXPECTED_TYPES = {
    "id": IntegerType,
    "flag": BooleanType,
    "count": IntegerType,
    "amount": DecimalType,
    "ratio": FloatType,
    "label": VarCharType,
    "born_on": DateType,
    "wakes_at": TimeType,
    "seen_at": TimestampType,
    "note": TextType,
}

# No microseconds: the bare variant does not ask for a precision, and a
# seconds-only TIMESTAMP is the one value every backend stores unchanged.
_VALUES = {
    "flag": True,
    "count": 7,
    "amount": Decimal("12.34"),
    "ratio": 0.5,
    "label": "alpha",
    "born_on": date(2000, 1, 2),
    "wakes_at": time(7, 30, 15),
    "seen_at": datetime(2024, 5, 6, 7, 8, 9),
    "note": "hello",
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


class TestScalarTypeVariants:
    """Declaration and value contracts for the two scalar-type variants."""

    def test_bare_model_has_no_declared_sql_types(self, typed_user_class):
        """A bare field leaves storage entirely to the dialect."""
        fields = typed_user_class.ddl_field_names()
        assert fields == TYPED_FIELD_NAMES, "The bare variant's field set changed"
        for field in fields:
            assert typed_user_class.column_data_type(field) is None, field

    def test_annotated_model_declares_sql_types(self, typed_user_annotated_class):
        """Every annotated field carries the type section 4 asks for."""
        fields = typed_user_annotated_class.ddl_field_names()
        assert fields == TYPED_FIELD_NAMES, "The two variants must declare one field set"
        for field in fields:
            marker = typed_user_annotated_class.column_data_type(field)
            assert isinstance(marker, UseSqlType), field
            assert isinstance(marker.data_type, _EXPECTED_TYPES[field]), field

        assert typed_user_annotated_class.column_data_type("amount").data_type.precision == 12
        assert typed_user_annotated_class.column_data_type("amount").data_type.scale == 2
        assert typed_user_annotated_class.column_data_type("label").data_type.length == 64
        assert typed_user_annotated_class.column_data_type("seen_at").data_type.precision == 3

        flag_rules = {
            type(constraint.branch)
            for constraint in typed_user_annotated_class.column_constraints("flag")
        }
        assert ColumnDefaultConstraint in flag_rules, "flag lost its DEFAULT declaration"
        label_rules = {
            type(constraint.branch)
            for constraint in typed_user_annotated_class.column_constraints("label")
        }
        assert ColumnUniqueConstraint in label_rules, "label lost its UNIQUE declaration"
        indexes = typed_user_annotated_class.column_indexes("label")
        assert [index.name for index in indexes] == ["ix_typed_users_annotated_label"]
        assert (
            typed_user_annotated_class.column_comment("count")
            == "Occurrences recorded for this row"
        )

    def test_bare_model_value_round_trip(self, typed_user_class, database, schema):
        """Inferred storage still gives every Python value back unchanged."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")
        instance = typed_user_class(**_VALUES)
        assert instance.save() == 1, "Expected the bare row to be inserted"
        assert instance.id is not None, "Expected a database-assigned primary key"
        found = typed_user_class.find_one(instance.id)
        assert found is not None, "Expected to read the bare row back"
        for field, value in _VALUES.items():
            actual = getattr(found, field)
            if isinstance(value, datetime):
                # Some drivers qualify a zoneless column with UTC on read; the
                # shared helper compares the instants on a common naive clock.
                assert_datetime_equal(actual, value)
            else:
                assert actual == value, field

    def test_annotated_model_value_round_trip(self, typed_user_annotated_class, database, schema):
        """Declared storage gives every Python value back unchanged."""
        _skip_unless(database.dialect, ANNOTATED_FIXTURE, "insert")
        instance = typed_user_annotated_class(**_VALUES)
        assert instance.save() == 1, "Expected the annotated row to be inserted"
        assert instance.id is not None, "Expected a database-assigned primary key"
        found = typed_user_annotated_class.find_one(instance.id)
        assert found is not None, "Expected to read the annotated row back"
        for field, value in _VALUES.items():
            actual = getattr(found, field)
            if isinstance(value, datetime):
                # Some drivers qualify a zoneless column with UTC on read; the
                # shared helper compares the instants on a common naive clock.
                assert_datetime_equal(actual, value)
            else:
                assert actual == value, field

    def test_microsecond_round_trip(self, microsecond_row_class, database, schema):
        """A precision=6 TIMESTAMP keeps all six fractional digits where supported."""
        _skip_unless(database.dialect, MICROSECOND_FIXTURE, "insert")
        precise_at = datetime(2024, 5, 6, 7, 8, 9, 123456)
        instance = microsecond_row_class(precise_at=precise_at)
        assert instance.save() == 1, "Expected the microsecond row to be inserted"
        assert instance.id is not None, "Expected a database-assigned primary key"
        found = microsecond_row_class.find_one(instance.id)
        assert found is not None, "Expected to read the microsecond row back"
        assert_datetime_equal(found.precise_at, precise_at, tolerance=timedelta(0))
