# src/rhosocial/activerecord/testsuite/feature/ddl/test_statement_derivation.py
"""Backend contract for ModelDDLDeclaration -> statement derivation."""

try:  # Python 3.8 has no typing.Annotated
    from typing import Annotated, Optional
except ImportError:  # pragma: no cover - only on 3.8
    from typing import Optional

    from typing_extensions import Annotated

import pytest
from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
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
    __primary_key__ = "id"
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
    __primary_key__ = "id"
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


def _supports(dialect, capability):
    """Read a capability switch the dialect must be able to answer.

    These switches are inherited from the dialect mixins with real defaults,
    so a missing probe is a backend defect, not a reason to skip: a contract
    that cannot ask the question cannot honestly pick a branch either.
    """
    probe = getattr(dialect, capability, None)
    if not callable(probe):
        pytest.fail(
            f"{type(dialect).__name__} does not expose {capability}(); the declaration "
            f"contract cannot branch on a capability the dialect does not answer"
        )
    return bool(probe())


def _assert_refuses_by_name(statements, feature_name):
    """A capability a dialect lacks must be refused at render time, by name.

    The statements are built first on purpose: a declaration that derives
    nothing has *dropped* the statement rather than refused it, and a silent
    drop is the failure this contract exists to catch. Rendering must then
    raise ``UnsupportedFeatureError`` naming the statement, so the caller sees
    the limitation instead of SQL the backend cannot accept.
    """
    assert statements, (
        f"a declared statement derived no {feature_name} statement; a silent drop "
        f"is not a refusal"
    )
    with pytest.raises(UnsupportedFeatureError, match=feature_name) as excinfo:
        for statement in statements:
            statement.to_sql()
    assert excinfo.value.feature_name == feature_name


def test_create_table_statement_has_no_inline_extras_by_default(ddl_dialect):
    sql = _create_sql(DerivationItem, ddl_dialect)
    assert "CREATE TABLE" in sql.upper()
    assert "ddl_derivation_items" in sql.lower()
    assert "name" in sql.lower()
    assert "CREATE INDEX" not in sql.upper()


def test_column_order_is_owned_by_the_caller(ddl_dialect):
    sql = _create_sql(DerivationItem, ddl_dialect, column_order=["name", "id"]).lower()
    assert sql.index("name") < sql.index("id")


def test_column_order_must_cover_every_column(ddl_dialect):
    with pytest.raises(ValueError, match="missing column"):
        build_create_table_statement(DerivationItem, ddl_dialect, column_order=["id"])


def test_indexes_are_separate_statements_by_default(ddl_dialect):
    """One declared index derives one CREATE INDEX and one DROP INDEX.

    A dialect that cannot render the plain index statement must refuse it by
    name; rendering nothing would be a silent drop, which the derivation must
    never do.
    """
    indexes = build_create_index_statements(DerivationItem, ddl_dialect)
    assert len(indexes) == 1
    drops = build_drop_index_statements(DerivationItem, ddl_dialect)
    assert len(drops) == 1

    if _supports(ddl_dialect, "supports_create_index"):
        sql = indexes[0].to_sql()[0]
        assert "CREATE INDEX" in sql.upper()
        assert "ix_derivation_items_name" in sql.lower()
    else:
        _assert_refuses_by_name(indexes, "CREATE INDEX")

    if _supports(ddl_dialect, "supports_drop_index"):
        assert "ix_derivation_items_name" in drops[0].to_sql()[0].lower()
    else:
        _assert_refuses_by_name(drops, "DROP INDEX")


def test_drop_table_statement_names_the_table(ddl_dialect):
    sql = build_drop_table_statement(DerivationItem, ddl_dialect).to_sql()[0]
    assert "DROP TABLE" in sql.upper()
    assert "ddl_derivation_items" in sql.lower()


def test_async_model_derives_the_same_statements(ddl_dialect):
    # A dialect is not sync/async; only the backend is.  The async model derives
    # its statements with the same dialect instance, and branches on the same
    # index capabilities the sync twin does.
    sql = _create_sql(AsyncDerivationItem, ddl_dialect)
    assert "ddl_derivation_items" in sql.lower()
    indexes = build_create_index_statements(AsyncDerivationItem, ddl_dialect)
    assert len(indexes) == 1
    drops = build_drop_index_statements(AsyncDerivationItem, ddl_dialect)
    assert len(drops) == 1

    if _supports(ddl_dialect, "supports_create_index"):
        assert "ix_derivation_items_name" in indexes[0].to_sql()[0].lower()
    else:
        _assert_refuses_by_name(indexes, "CREATE INDEX")

    if _supports(ddl_dialect, "supports_drop_index"):
        assert "ix_derivation_items_name" in drops[0].to_sql()[0].lower()
    else:
        _assert_refuses_by_name(drops, "DROP INDEX")
