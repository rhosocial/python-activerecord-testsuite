# src/rhosocial/activerecord/testsuite/feature/ddl/test_derivation_async.py
"""Backend-independent asynchronous DDLSource declaration tests."""

from rhosocial.activerecord.backend.expression.statements.ddl_table import (
    ColumnConstraintType,
    ForeignKeyConstraint,
    TableConstraintType,
)
from rhosocial.activerecord.base import DDLSource, UseSqlType


def _constraint_types(model, field):
    return {constraint.constraint_type for constraint in model.column_constraints(field)}


class TestZeroDeclarationDerivationAsync:
    async def test_source_declaration(self, async_bare_class):
        assert isinstance(async_bare_class, DDLSource)
        assert async_bare_class.table_name() == "ddl_bare_items"
        assert async_bare_class.primary_key_columns() == ("id",)
        assert async_bare_class.ddl_field_names() == (
            "id",
            "name",
            "quantity",
            "price",
            "note",
        )

    async def test_primary_key_and_nullability_declarations(self, async_bare_class):
        assert ColumnConstraintType.PRIMARY_KEY in _constraint_types(
            async_bare_class, "id"
        )
        assert ColumnConstraintType.NOT_NULL in _constraint_types(
            async_bare_class, "name"
        )
        assert ColumnConstraintType.NOT_NULL not in _constraint_types(
            async_bare_class, "note"
        )


class TestGenericDeclarationDerivationAsync:
    async def test_type_and_constraint_declarations(self, async_spec_order_class):
        code_type = async_spec_order_class.column_type("code")
        assert isinstance(code_type, UseSqlType)
        assert code_type.data_type.name == "varchar"
        assert code_type.data_type.length == 32
        assert ColumnConstraintType.CHECK in _constraint_types(
            async_spec_order_class, "status"
        )

        unique = next(
            constraint
            for constraint in async_spec_order_class.table_constraints()
            if constraint.constraint_type == TableConstraintType.UNIQUE
        )
        assert unique.columns == ["code", "status"]

    async def test_table_index_declarations(self, async_spec_order_class):
        index = async_spec_order_class.table_indexes()[0]
        assert index.name == "ix_ddl_spec_orders_code"
        assert index.columns == ["code"]


class TestCapabilityDeclarationDerivationAsync:
    async def test_capability_declarations_remain_available(
        self, async_capability_class
    ):
        assert async_capability_class.table_indexes()[0].name == (
            "ix_ddl_capability_posts_title"
        )
        assert async_capability_class.generated_column("double_views") is not None


class TestForeignKeyDeclarationDerivationAsync:
    async def test_foreign_key_declaration(self, async_spec_comment_class):
        constraint = async_spec_comment_class.table_constraints()[0]
        assert isinstance(constraint, ForeignKeyConstraint)
        assert constraint.columns == ["order_id"]
        assert constraint.foreign_key_table == "ddl_spec_orders"
        assert constraint.foreign_key_columns == ["id"]
        assert constraint.on_delete.value == "CASCADE"
