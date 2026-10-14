# src/rhosocial/activerecord/testsuite/feature/ddl/test_derivation.py
"""Backend-independent DDLSource declaration tests."""

from rhosocial.activerecord.backend.expression.statements.ddl_table import (
    ColumnCheckConstraint,
    ColumnNotNullConstraint,
    ColumnPrimaryKeyConstraint,
    ForeignKeyConstraint,
    TableUniqueConstraint,
)
from rhosocial.activerecord.base import DDLSource, UseSqlType


def _constraint_branches(model, field):
    """The branch classes the field's constraint clauses state.

    The kind is the branch node's class since the two-level split, so this
    reads what each clause states rather than a tag the node no longer
    carries.
    """
    return {type(constraint.branch) for constraint in model.column_constraints(field)}


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
        assert ColumnPrimaryKeyConstraint in _constraint_branches(
            bare_class, "id"
        )
        assert ColumnNotNullConstraint in _constraint_branches(bare_class, "name")
        assert ColumnNotNullConstraint not in _constraint_branches(
            bare_class, "note"
        )


class TestGenericDeclarationDerivation:
    def test_type_and_constraint_declarations(self, spec_order_class):
        code_type = spec_order_class.column_data_type("code")
        assert isinstance(code_type, UseSqlType)
        assert code_type.data_type.name == "varchar"
        assert code_type.data_type.length == 32
        assert ColumnCheckConstraint in _constraint_branches(
            spec_order_class, "status"
        )

        unique = next(
            constraint
            for constraint in spec_order_class.table_constraints()
            if isinstance(constraint.branch, TableUniqueConstraint)
        )
        assert unique.branch.columns == ["code", "status"]

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
        assert constraint.foreign_key_table.name == "ddl_spec_orders"
        assert constraint.foreign_key_columns == ["id"]
        assert constraint.on_delete.value == "CASCADE"
