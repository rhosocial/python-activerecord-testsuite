# src/rhosocial/activerecord/testsuite/feature/basic/ddl/test_alter_table_if_exists.py
"""
Cross-backend ALTER TABLE IF [NOT] EXISTS tests (sync).

These tests exercise the optional ``if_not_exists`` / ``if_exists`` fields on
``AddColumn`` / ``DropColumn`` / ``DropTableConstraint``. They are a generic
*expression/dialect* contract: no live database connection is involved, the
provider hands over a dialect instance and the assertions run purely on SQL
rendering.

Backends that do not support a given modifier (their dialect both accepts and
rejects the qualifier) simply do not advertise the matching ``supports_*``
switch, so the corresponding test is skipped via ``@requires_protocol``.
Supported backends must render the qualifier; the plain (unqualified) forms
are rendered by every backend and asserted unconditionally.
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


# --- ADD COLUMN -------------------------------------------------

class TestDdlAddColumn:
    """ALTER TABLE ADD COLUMN rendering (plain & IF NOT EXISTS)."""

    @requires_protocol(AlterTableModifierSupport, "supports_add_column_if_not_exists")
    def test_add_column_if_not_exists(self, ddl_dialect):
        action = AddColumn(ddl_dialect, ColumnDefinition("content", TextType()), if_not_exists=True)
        sql, params = action.to_sql()
        assert "IF NOT EXISTS" in sql
        assert not params

    def test_add_column_plain_form(self, ddl_dialect):
        action = AddColumn(ddl_dialect, ColumnDefinition("content", TextType()))
        sql, params = action.to_sql()
        assert "IF NOT EXISTS" not in sql
        assert not params


# --- DROP COLUMN ------------------------------------------------

class TestDdlDropColumn:
    """ALTER TABLE ... DROP COLUMN rendering (plain & IF EXISTS)."""

    @requires_protocol(AlterTableModifierSupport, "supports_drop_column_if_exists")
    def test_drop_column_if_exists(self, ddl_dialect):
        action = DropColumn(ddl_dialect, column_name="content", if_exists=True)
        sql, params = action.to_sql()
        assert "IF EXISTS" in sql
        assert not params

    def test_drop_column_plain_form(self, ddl_dialect):
        action = DropColumn(ddl_dialect, column_name="content")
        sql, params = action.to_sql()
        assert "IF EXISTS" not in sql
        assert not params


# --- DROP CONSTRAINT ----------------------------------------------

class TestDdlDropConstraint:
    """ALTER TABLE ... DROP CONSTRAINT rendering (plain & IF EXISTS)."""

    @requires_protocol(AlterTableModifierSupport, "supports_drop_constraint_if_exists")
    def test_drop_constraint_if_exists(self, ddl_dialect):
        action = DropTableConstraint(
            ddl_dialect, constraint_name="uq_snapshot_content", if_exists=True
        )
        sql, params = action.to_sql()
        assert "IF EXISTS" in sql
        assert not params

    @requires_protocol(ConstraintSupport, "supports_drop_constraint")
    def test_drop_constraint_plain_form(self, ddl_dialect):
        action = DropTableConstraint(
            ddl_dialect, constraint_name="uq_snapshot_content"
        )
        sql, params = action.to_sql()
        assert "IF EXISTS" not in sql
        assert not params