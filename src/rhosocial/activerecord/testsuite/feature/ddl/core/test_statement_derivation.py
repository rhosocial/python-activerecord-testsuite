# src/rhosocial/activerecord/testsuite/feature/ddl/test_statement_derivation.py
"""Backend contract for DDLSource -> statement derivation."""

try:  # Python 3.8 has no typing.Annotated
    from typing import Annotated, Optional
except ImportError:  # pragma: no cover - only on 3.8
    from typing import Optional

    from typing_extensions import Annotated

import pytest
from rhosocial.activerecord.backend.expression.types import IntegerType, VarCharType
from rhosocial.activerecord.base import (
    IdentityAttribute,
    UseColumnAttributes,
    UseIndex,
    UseSqlType,
)
from rhosocial.activerecord.base.derivation import (
    build_create_index_statements,
    build_create_table_statement,
    build_drop_index_statements,
    build_drop_table_statement,
)
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class DerivationItem(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "ddl_derivation_items"

    id: Annotated[
        Optional[int],
        UseSqlType(IntegerType()),
        UseColumnAttributes(IdentityAttribute()),
    ] = None
    name: Annotated[
        str,
        UseSqlType(VarCharType(length=64)),
        UseIndex("ix_derivation_items_name"),
    ]


class AsyncDerivationItem(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "ddl_derivation_items"

    id: Annotated[
        Optional[int],
        UseSqlType(IntegerType()),
        UseColumnAttributes(IdentityAttribute()),
    ] = None
    name: Annotated[
        str,
        UseSqlType(VarCharType(length=64)),
        UseIndex("ix_derivation_items_name"),
    ]


def _create_sql(model, dialect, **kwargs):
    statement = build_create_table_statement(model, dialect, **kwargs)
    return statement.to_sql()[0]


def test_create_table_statement_has_no_inline_extras_by_default(ddl_dialect):
    sql = _create_sql(DerivationItem, ddl_dialect)
    assert "CREATE TABLE" in sql.upper()
    assert "ddl_derivation_items" in sql
    assert "name" in sql
    assert "CREATE INDEX" not in sql.upper()


def test_column_order_is_owned_by_the_caller(ddl_dialect):
    sql = _create_sql(DerivationItem, ddl_dialect, column_order=["name", "id"])
    assert sql.index("name") < sql.index("id")


def test_column_order_must_cover_every_column(ddl_dialect):
    with pytest.raises(ValueError, match="missing column"):
        build_create_table_statement(DerivationItem, ddl_dialect, column_order=["id"])


def test_indexes_are_separate_statements_by_default(ddl_dialect):
    indexes = build_create_index_statements(DerivationItem, ddl_dialect)
    assert len(indexes) == 1
    sql = indexes[0].to_sql()[0]
    assert "CREATE INDEX" in sql.upper()
    assert "ix_derivation_items_name" in sql

    drops = build_drop_index_statements(DerivationItem, ddl_dialect)
    assert len(drops) == 1
    assert "ix_derivation_items_name" in drops[0].to_sql()[0]


def test_drop_table_statement_names_the_table(ddl_dialect):
    sql = build_drop_table_statement(DerivationItem, ddl_dialect).to_sql()[0]
    assert "DROP TABLE" in sql.upper()
    assert "ddl_derivation_items" in sql


def test_async_model_derives_the_same_statements(ddl_dialect):
    # A dialect is not sync/async; only the backend is.  The async model derives
    # its statements with the same dialect instance.
    sql = _create_sql(AsyncDerivationItem, ddl_dialect)
    assert "ddl_derivation_items" in sql
    indexes = build_create_index_statements(AsyncDerivationItem, ddl_dialect)
    assert len(indexes) == 1
