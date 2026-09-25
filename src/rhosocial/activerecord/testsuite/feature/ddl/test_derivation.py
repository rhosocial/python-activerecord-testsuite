# src/rhosocial/activerecord/testsuite/feature/ddl/test_derivation.py
"""Backend-independent DDLSource declaration tests."""

from rhosocial.activerecord.backend.expression.statements.ddl_table import (
    ColumnConstraintType,
    ForeignKeyConstraint,
    TableConstraintType,
)
from rhosocial.activerecord.base import DDLSource, UseSqlType


def _constraint_types(model, field):
    return {constraint.constraint_type for constraint in model.column_constraints(field)}


class TestZeroDeclarationDerivation:
    def test_source_declaration(self, bare_class):
        assert isinstance(bare_class, DDLSource)
        assert bare_class.table_name() == "ddl_bare_items"
        assert bare_class.primary_key_columns() == ("id",)
        assert bare_class.ddl_field_names() == (
            "id",
            "name",
            "quantity",
            "price",
            "note",
        )

    def test_primary_key_and_nullability_declarations(self, bare_class):
        assert ColumnConstraintType.PRIMARY_KEY in _constraint_types(
            bare_class, "id"
        )
        assert ColumnConstraintType.NOT_NULL in _constraint_types(bare_class, "name")
        assert ColumnConstraintType.NOT_NULL not in _constraint_types(
            bare_class, "note"
        )


class TestGenericDeclarationDerivation:
    def test_type_and_constraint_declarations(self, spec_order_class):
        code_type = spec_order_class.column_type("code")
        assert isinstance(code_type, UseSqlType)
        assert code_type.data_type.name == "varchar"
        assert code_type.data_type.length == 32
        assert ColumnConstraintType.CHECK in _constraint_types(
            spec_order_class, "status"
        )

        unique = next(
            constraint
            for constraint in spec_order_class.table_constraints()
            if constraint.constraint_type == TableConstraintType.UNIQUE
        )
        assert unique.columns == ["code", "status"]

    def test_table_index_declarations(self, spec_order_class):
        index = spec_order_class.table_indexes()[0]
        assert index.name == "ix_ddl_spec_orders_code"
        assert index.columns == ["code"]


class TestCapabilityDeclarationDerivation:
    def test_capability_declarations_remain_available(self, capability_class):
        assert capability_class.table_indexes()[0].name == (
            "ix_ddl_capability_posts_title"
        )
        assert capability_class.generated_column("double_views") is not None
        assert capability_class.column_indexes("title") == []


class TestForeignKeyDeclarationDerivation:
    def test_foreign_key_declaration(self, spec_comment_class):
        constraint = spec_comment_class.table_constraints()[0]
        assert isinstance(constraint, ForeignKeyConstraint)
        assert constraint.columns == ["order_id"]
        assert constraint.foreign_key_table == "ddl_spec_orders"
        assert constraint.foreign_key_columns == ["id"]
        assert constraint.on_delete.value == "CASCADE"
