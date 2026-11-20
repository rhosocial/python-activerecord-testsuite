# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_field_variants.py
"""Field-mapping variants: bare declarations and non-storage-changing markers.

The two models bind to one table (``field_rows``) because ``UseColumn`` and
``UseAdapter`` change the Python-to-column mapping, not the stored columns.
The tests therefore assert three things:

* the bare model writes no marker at all;
* the annotated model declares the renames, the adapter and a derived field,
  yet derives the very same DDL;
* both models still round-trip their values on the configured backend.

The sync and async halves differ only in the configured model fixture; the
declarations are shared through one mixin per variant (P4).
"""

from decimal import Decimal

import pytest
from rhosocial.activerecord.base import DerivedField, UseAdapter, UseColumn
from rhosocial.activerecord.base.derivation import build_create_table_statement

from rhosocial.activerecord.testsuite.feature.basic.fixtures.field_models import (
    FIELD_VARIANT_FIXTURES,
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


class TestFieldVariants:
    """Declaration and value contracts for the two field-mapping variants."""

    def test_bare_model_has_no_declared_markers(self, field_row_class):
        """A bare field leaves mapping entirely to the framework."""
        assert field_row_class.ddl_field_names() == _EXPECTED_COLUMNS
        for field in field_row_class.ddl_field_names():
            assert field_row_class.column_data_type(field) is None, field
            assert field_row_class.get_column_name(field) == field, field

    def test_annotated_model_declares_mapping_and_adapter(self, field_row_annotated_class):
        """The annotated variant renames columns, adapts a value and derives a field."""
        annotated = field_row_annotated_class
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

    def test_variants_share_one_table(self, field_row_class, field_row_annotated_class, database):
        """Renaming and adapting do not change the derived DDL (P2)."""
        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        bare_ddl = build_create_table_statement(field_row_class, dialect).to_sql()
        annotated_ddl = build_create_table_statement(field_row_annotated_class, dialect).to_sql()
        assert bare_ddl == annotated_ddl

    def test_sync_async_twins_derive_identical_ddl(
        self, field_row_class, field_row_annotated_class, database
    ):
        """A one-sided sync/async drift must fail (P4)."""
        from rhosocial.activerecord.testsuite.feature.basic.fixtures.field_models import (
            AsyncFieldRow,
            AsyncFieldRowAnnotated,
        )

        dialect = database.dialect
        _skip_unless(dialect, BARE_FIXTURE, "create_table")
        assert build_create_table_statement(field_row_class, dialect).to_sql() == (
            build_create_table_statement(AsyncFieldRow, dialect).to_sql()
        )
        assert build_create_table_statement(field_row_annotated_class, dialect).to_sql() == (
            build_create_table_statement(AsyncFieldRowAnnotated, dialect).to_sql()
        )

    def test_both_variants_round_trip_values(
        self, field_row_class, field_row_annotated_class, database
    ):
        """Both mappings write and read their values on one table."""
        _skip_unless(database.dialect, BARE_FIXTURE, "insert")

        bare = field_row_class(**_BARE_VALUES)
        assert bare.save() == 1, "Expected the bare row to be inserted"
        found_bare = field_row_class.find_one(bare.id)
        for field, value in _BARE_VALUES.items():
            assert getattr(found_bare, field) == value, field

        annotated = field_row_annotated_class(**_ANNOTATED_VALUES)
        assert annotated.save() == 1, "Expected the annotated row to be inserted"
        found_annotated = field_row_annotated_class.find_one(annotated.id)
        for field, value in _ANNOTATED_VALUES.items():
            assert getattr(found_annotated, field) == value, field
