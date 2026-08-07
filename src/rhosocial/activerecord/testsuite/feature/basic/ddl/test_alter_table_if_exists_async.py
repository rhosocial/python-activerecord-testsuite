# src/rhosocial/activerecord/testsuite/feature/basic/ddl/test_alter_table_if_exists_async.py
"""
Cross-backend ALTER TABLE IF [NOT] EXISTS tests (async).

Async mirror of ``test_alter_table_if_exists.py``. The ddl group is a
dialect/expression contract, so the async variant only swaps the fixture
provider (``async_ddl_dialect``); no RPC-style concurrency is exercised.
"""
from typing import TYPE_CHECKING

import pytest

from rhosocial.activerecord.backend.dialect.protocols import (
    AlterTableModifierSupport,
    ConstraintSupport,
)
from rhosocial.activerecord.backend.expression.statements import ColumnDefinition
from rhosocial.activerecord.backend.expression.statements.ddl_alter import (
    AddColumn,
    DropColumn,
    DropTableConstraint,
)
from rhosocial.activerecord.backend.expression.types import TextType
from rhosocial.activerecord.testsuite.utils import requires_protocol

if TYPE_CHECKING:  # pragma: no cover
    pass


class TestAsyncDdlAddColumn:
    """ALTER TABLE ADD COLUMN rendering (plain & IF NOT EXISTS)."""

    @requires_protocol(AlterTableModifierSupport, "supports_add_column_if_not_exists")
    async def test_add_column_if_not_exists(self, async_ddl_dialect):
        action = AddColumn(
            async_ddl_dialect, ColumnDefinition("content", TextType()), if_not_exists=True
        )
        sql, params = action.to_sql()
        assert "IF NOT EXISTS" in sql
        assert not params

    async def test_add_column_plain_form(self, async_ddl_dialect):
        action = AddColumn(async_ddl_dialect, ColumnDefinition("content", TextType()))
        sql, params = action.to_sql()
        assert "IF NOT EXISTS" not in sql
        assert not params


class TestAsyncDdlDropColumn:
    """ALTER TABLE ... DROP COLUMN IF EXISTS rendering."""

    @requires_protocol(AlterTableModifierSupport, "supports_drop_column_if_exists")
    async def test_drop_column_if_exists(self, async_ddl_dialect):
        action = DropColumn(async_ddl_dialect, column_name="content", if_exists=True)
        sql, params = action.to_sql()
        assert "IF EXISTS" in sql
        assert not params

    async def test_drop_column_plain_form(self, async_ddl_dialect):
        action = DropColumn(async_ddl_dialect, column_name="content")
        sql, params = action.to_sql()
        assert "IF EXISTS" not in sql
        assert not params


class TestAsyncDdlDropConstraint:
    """ALTER TABLE ... DROP CONSTRAINT IF EXISTS (plain & qualified)."""

    @requires_protocol(AlterTableModifierSupport, "supports_drop_constraint_if_exists")
    async def test_drop_constraint_if_exists(self, async_ddl_dialect):
        action = DropTableConstraint(
            async_ddl_dialect, constraint_name="uq_snapshot_content", if_exists=True
        )
        sql, params = action.to_sql()
        assert "IF EXISTS" in sql
        assert not params

    @requires_protocol(ConstraintSupport, "supports_drop_constraint")
    async def test_drop_constraint_plain_form(self, async_ddl_dialect):
        action = DropTableConstraint(
            async_ddl_dialect, constraint_name="uq_snapshot_content"
        )
        sql, params = action.to_sql()
        assert "IF EXISTS" not in sql
        assert not params