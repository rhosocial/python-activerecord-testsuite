# src/rhosocial/activerecord/testsuite/feature/basic/ddl/test_materialized_view_contract.py
"""
Cross-backend materialized view contract (sync).

This is an *expression/dialect* contract: the provider hands over a dialect
instance and every assertion runs purely on SQL rendering, so no live database
connection is involved.

Two layers are covered:

**Invariants (never skipped).** A dialect that advertises materialized view
support must actually implement the CREATE rendering. Historically backends
declared ``supports_materialized_view() -> True`` while inheriting the generic
``ViewMixin`` formatter, which produced SQL no target database accepts
(PostgreSQL lost ``WITH (storage_parameter)``; ClickHouse emitted ``WITH DATA``,
a clause it does not have). The probe is the public promise, so probe and
formatter are asserted together.

CREATE is singled out because its syntax diverges on *every* backend
(PostgreSQL ``WITH (...)``/``TABLESPACE``/``WITH [NO] DATA``, Oracle
``BUILD IMMEDIATE``/``REFRESH``, Snowflake ``CLUSTER BY``/``COMMENT``,
ClickHouse ``ENGINE``/``TO``/``POPULATE``/``REFRESH``). A backend that genuinely
wants the generic form still satisfies the rule by overriding the formatter and
delegating to ``super()`` — one explicit method instead of a silent accident.
DROP is deliberately *not* constrained: ``DROP MATERIALIZED VIEW [IF EXISTS]
[CASCADE]`` is broadly valid, so inheriting it is legitimate.

REFRESH is constrained only when the backend advertises refresh support, since
most databases have no ``REFRESH MATERIALIZED VIEW`` statement at all.

**Capability-gated rendering.** Backends that do support materialized views must
render the expected statement shape; backends that do not are skipped
declaratively via ``@requires_protocol``.
"""

import pytest

from rhosocial.activerecord.backend.dialect.mixins import ViewMixin
from rhosocial.activerecord.backend.dialect.protocols import ViewSupport
from rhosocial.activerecord.backend.expression import Column, QueryExpression, TableExpression
from rhosocial.activerecord.backend.expression.statements.ddl_view import (
    CreateMaterializedViewExpression,
    DropMaterializedViewExpression,
    RefreshMaterializedViewExpression,
)
from rhosocial.activerecord.testsuite.utils import requires_protocol


#: Core ``ViewMixin`` implementations a backend must not resolve to once it
#: advertises the matching capability.
CORE_CREATE_FORMATTER = ViewMixin.format_create_materialized_view_statement
CORE_REFRESH_FORMATTER = ViewMixin.format_refresh_materialized_view_statement


def _source_query(dialect):
    """A minimal SELECT the MV expressions can embed."""
    return QueryExpression(
        dialect=dialect,
        select=[Column(dialect, "id")],
        from_=TableExpression(dialect, "source_table"),
    )


def _resolved_formatter(dialect, name):
    """Return the plain function object a dialect resolves ``name`` to."""
    bound = getattr(dialect, name, None)
    if bound is None:
        return None
    return getattr(bound, "__func__", bound)


class TestMaterializedViewCapabilityInvariants:
    """A declared capability must be backed by a real implementation."""

    def test_materialized_view_probe_is_callable(self, ddl_dialect):
        """Every backend must answer the probe (used for gating)."""
        probe = getattr(ddl_dialect, "supports_materialized_view", None)
        assert callable(probe), "dialect does not expose supports_materialized_view()"
        assert isinstance(probe(), bool)

    def test_declared_support_requires_own_create_formatter(self, ddl_dialect):
        """``supports_materialized_view() is True`` implies a backend-owned CREATE.

        Guards the failure mode where a backend flips the probe to ``True`` but
        leaves the generic ``ViewMixin`` implementation in place, so callers get
        SQL the target database cannot execute.
        """
        if ddl_dialect.supports_materialized_view() is not True:
            pytest.skip("backend does not advertise materialized view support")

        resolved = _resolved_formatter(
            ddl_dialect, "format_create_materialized_view_statement"
        )
        assert resolved is not None, (
            "dialect does not implement format_create_materialized_view_statement()"
        )
        assert resolved is not CORE_CREATE_FORMATTER, (
            f"{type(ddl_dialect).__name__} advertises materialized view support but "
            f"resolves format_create_materialized_view_statement() to the core "
            f"ViewMixin implementation; the backend must override it (and be listed "
            f"before ViewMixin in the dialect base list, otherwise the override is "
            f"dead code). CREATE MATERIALIZED VIEW syntax diverges on every backend, "
            f"so a backend that wants the generic form must say so explicitly by "
            f"overriding the formatter and delegating to super()."
        )

    def test_declared_refresh_support_requires_own_formatter(self, ddl_dialect):
        """The same invariant for the REFRESH path."""
        if ddl_dialect.supports_refresh_materialized_view() is not True:
            pytest.skip("backend does not advertise materialized view refresh")

        resolved = _resolved_formatter(
            ddl_dialect, "format_refresh_materialized_view_statement"
        )
        assert resolved is not None
        assert resolved is not CORE_REFRESH_FORMATTER, (
            f"{type(ddl_dialect).__name__} advertises REFRESH MATERIALIZED VIEW but "
            f"resolves the formatter to the core ViewMixin implementation"
        )

    def test_generic_expression_renders_when_supported(self, ddl_dialect):
        """The generic expressions must work on any backend that claims support.

        Catches formatters written against a private expression surface: those
        raise ``AttributeError`` when handed the generic expression.
        """
        if ddl_dialect.supports_materialized_view() is not True:
            pytest.skip("backend does not advertise materialized view support")

        create = CreateMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract", query=_source_query(ddl_dialect)
        )
        sql, _ = create.to_sql()
        assert sql.upper().startswith("CREATE MATERIALIZED VIEW"), (
            f"CREATE MATERIALIZED VIEW rendered as {sql!r}"
        )

        drop = DropMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract", if_exists=True
        )
        drop_sql, _ = drop.to_sql()
        assert drop_sql.upper().startswith("DROP MATERIALIZED VIEW"), (
            f"DROP MATERIALIZED VIEW rendered as {drop_sql!r}"
        )


class TestMaterializedViewRendering:
    """Statement shape for backends that advertise materialized views."""

    @requires_protocol(ViewSupport, "supports_materialized_view")
    def test_create_renders_query_and_data_clause(self, ddl_dialect):
        expression = CreateMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            query=_source_query(ddl_dialect),
        )
        sql, params = expression.to_sql()
        assert "mv_contract" in sql
        assert params == (), "materialized view DDL must not bind parameters"

    @requires_protocol(ViewSupport, "supports_materialized_view")
    def test_create_supports_column_aliases(self, ddl_dialect):
        expression = CreateMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            query=_source_query(ddl_dialect),
            column_aliases=["alias_id"],
        )
        sql, _ = expression.to_sql()
        assert "alias_id" in sql

    @requires_protocol(ViewSupport, "supports_materialized_view")
    def test_drop_supports_if_exists_and_cascade(self, ddl_dialect):
        expression = DropMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            if_exists=True,
            cascade=True,
        )
        sql, _ = expression.to_sql()
        assert "IF EXISTS" in sql
        assert "CASCADE" in sql

    @requires_protocol(ViewSupport, "supports_refresh_materialized_view")
    def test_refresh_renders_statement(self, ddl_dialect):
        expression = RefreshMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract"
        )
        sql, params = expression.to_sql()
        assert sql.upper().startswith("REFRESH MATERIALIZED VIEW")
        assert params == ()
