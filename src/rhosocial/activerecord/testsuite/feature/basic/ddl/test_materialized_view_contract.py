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

from rhosocial.activerecord.backend.dialect.exceptions import DialectNotAdaptedException
from rhosocial.activerecord.backend.dialect.mixins import ViewMixin
from rhosocial.activerecord.backend.dialect.protocols import ViewSupport
from rhosocial.activerecord.backend.expression import Column, QueryExpression, TableExpression
from rhosocial.activerecord.backend.expression.statements.ddl_view import (
    CreateMaterializedViewExpression,
    DropMaterializedViewExpression,
    RefreshMaterializedViewExpression,
)


#: Core ``ViewMixin`` implementations a backend must not resolve to once it
#: advertises the matching capability.
CORE_CREATE_FORMATTER = ViewMixin.format_create_materialized_view_statement
CORE_REFRESH_FORMATTER = ViewMixin.format_refresh_materialized_view_statement


def _probe(dialect, method_name, *, required: bool):
    """Call a capability probe, skipping when the dialect cannot answer it.

    Version-aware probes raise ``DialectNotAdaptedException`` until the backend
    has connected, and version-gated formatters legitimately cannot render
    without a resolved version (Oracle gates ``CREATE MATERIALIZED VIEW`` on 9i
    and ``IF NOT EXISTS`` on 23ai). Such dialects are skipped rather than
    failed: the point of this contract is to catch *lying* probes, not to
    require every backend to render DDL without a connection.
    """
    probe = getattr(dialect, method_name, None)
    if probe is None:
        if required:
            pytest.fail(f"dialect does not expose {method_name}()")
        return False
    try:
        return bool(probe())
    except DialectNotAdaptedException:
        pytest.skip(f"dialect is not adapted; {method_name}() needs a server version")


def _mv_supported(dialect):
    """Whether the dialect advertises materialized views (skip if unknowable)."""
    return _probe(dialect, "supports_materialized_view", required=True)


def _mv_refresh_supported(dialect):
    """Whether the dialect advertises materialized view refresh."""
    return _probe(dialect, "supports_refresh_materialized_view", required=False)


def _render(expression):
    """Render an expression, skipping dialects that need a resolved version.

    Version-gated formatters cannot produce SQL before the backend has
    connected (Oracle gates ``CREATE MATERIALIZED VIEW`` on 9i and
    ``IF NOT EXISTS`` on 23ai), so an unadapted dialect is skipped rather than
    failed — the ownership invariants above still run for it.
    """
    try:
        return expression.to_sql()
    except DialectNotAdaptedException:
        pytest.skip("dialect is not adapted; version-gated DDL cannot be rendered")


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

    def test_declared_support_requires_own_create_formatter(self, ddl_dialect):
        """``supports_materialized_view() is True`` implies a backend-owned CREATE.

        Guards the failure mode where a backend flips the probe to ``True`` but
        leaves the generic ``ViewMixin`` implementation in place, so callers get
        SQL the target database cannot execute.
        """
        if not _mv_supported(ddl_dialect):
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
        if not _mv_refresh_supported(ddl_dialect):
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
        if not _mv_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view support")

        create = CreateMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract", query=_source_query(ddl_dialect)
        )
        sql, _ = _render(create)
        assert sql.upper().startswith("CREATE MATERIALIZED VIEW"), (
            f"CREATE MATERIALIZED VIEW rendered as {sql!r}"
        )

        drop = DropMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract", if_exists=True
        )
        drop_sql, _ = _render(drop)
        assert drop_sql.upper().startswith("DROP MATERIALIZED VIEW"), (
            f"DROP MATERIALIZED VIEW rendered as {drop_sql!r}"
        )


class TestMaterializedViewRendering:
    """Statement shape for backends that advertise materialized views."""

    def test_create_renders_query_and_data_clause(self, ddl_dialect):
        if not _mv_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view support")
        expression = CreateMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            query=_source_query(ddl_dialect),
        )
        sql, params = _render(expression)
        assert "mv_contract" in sql
        assert params == (), "materialized view DDL must not bind parameters"

    def test_create_supports_column_aliases(self, ddl_dialect):
        if not _mv_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view support")
        expression = CreateMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            query=_source_query(ddl_dialect),
            column_aliases=["alias_id"],
        )
        sql, _ = _render(expression)
        assert "alias_id" in sql

    def test_drop_supports_if_exists_and_cascade(self, ddl_dialect):
        if not _mv_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view support")
        expression = DropMaterializedViewExpression(
            dialect=ddl_dialect,
            view_name="mv_contract",
            if_exists=True,
            cascade=True,
        )
        sql, _ = _render(expression)
        assert "IF EXISTS" in sql
        assert "CASCADE" in sql

    def test_refresh_renders_statement(self, ddl_dialect):
        """A refreshing backend must render *something* that refreshes the view.

        The leading keyword is deliberately not asserted: not every database
        exposes a ``REFRESH MATERIALIZED VIEW`` statement. Oracle refreshes via a
        ``DBMS_MVIEW.REFRESH`` PL/SQL block. The contract is that the request
        renders and refers to the view; the concrete statement shape is asserted
        per backend.
        """
        if not _mv_refresh_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view refresh")
        expression = RefreshMaterializedViewExpression(
            dialect=ddl_dialect, view_name="mv_contract"
        )
        sql, params = _render(expression)
        assert sql.strip(), "REFRESH rendered an empty statement"
        # Backends that fold unquoted identifiers may emit the name in upper
        # case (Oracle passes a string name to DBMS_MVIEW), so compare case
        # insensitively.
        assert "MV_CONTRACT" in sql.upper()
        assert params == ()


class TestMaterializedViewProtocolDeclaration:
    """The capability must be reachable through the declared protocol."""

    def test_probe_is_declared_by_view_support(self, ddl_dialect):
        if not _mv_supported(ddl_dialect):
            pytest.skip("backend does not advertise materialized view support")
        assert isinstance(ddl_dialect, ViewSupport)
