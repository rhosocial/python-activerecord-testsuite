# src/rhosocial/activerecord/testsuite/feature/ddl/test_derivation.py
"""
feature.ddl: derivation round-trip (sync).

Every test derives DDL from the fixture model declarations via
``generate_create_table``, executes it through the backend under test, and
verifies the live structure round-trips (insert / query / defaults). The
declared constants are the single source of truth — no hand-written schema.
"""
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError


def _create_model_table_on(backend, model):
    """Derive *model*'s CREATE TABLE and execute it on a given backend."""
    expr = model.generate_create_table(backend.dialect)
    backend.execute(*expr.to_sql())
    return expr


def _create_model_table(model):
    """Derive DDL from the model and execute it (table only).

    Idempotent: drops the leftover table first so a test may derive and
    execute repeatedly on the same scenario connection.
    """
    from rhosocial.activerecord.backend.expression import (
        DropTableExpression, TableExpression,
    )

    drop = DropTableExpression(
        dialect=model.__backend__.dialect,
        table=TableExpression(model.__backend__.dialect, model.__table_name__),
        if_exists=True,
    )
    model.__backend__.execute(*drop.to_sql())

    expr = model.generate_create_table()
    model.__backend__.execute(*expr.to_sql())
    return expr


def _create_model_indexes(model, expr):
    """Derive and execute each index product."""
    for ix in expr.indexes:
        index_expr = ix.to_create_index_expression(
            model.__backend__.dialect, expr.table
        )
        model.__backend__.execute(*index_expr.to_sql())


class TestZeroDeclarationDerivation:
    """BareItem: no Specs at all — default derivation rules."""

    def test_derive_and_execute(self, bare_class):
        expr = _create_model_table(bare_class)
        sql, _ = expr.to_sql()
        # Default rules visible in the derived DDL
        assert "CREATE TABLE" in sql
        assert "PRIMARY KEY" in sql

    def test_round_trip(self, bare_class):
        _create_model_table(bare_class)
        item = bare_class(name="a", quantity=2, price=1.5)
        item.save()

        found = bare_class.find_one({'id': item.id})
        assert found is not None
        assert found.name == "a"
        assert found.quantity == 2

        found.quantity = 5
        found.save()
        again = bare_class.find_one({'id': item.id})
        assert again.quantity == 5

    def test_nullable_column_stays_nullable(self, bare_class):
        """Optional fields (with defaults) derive as nullable: omitting note
        must not violate the derived schema."""
        _create_model_table(bare_class)
        item = bare_class(name="n", quantity=1, price=1.0)
        item.save()
        assert bare_class.find_one({'id': item.id}).note is None


class TestGenericSpecDerivation:
    """SpecOrder: generic Specs (UUID PK, CHECK, UNIQUE, DEFAULT, INDEX)."""

    def test_derive_and_execute(self, spec_order_class):
        expr = _create_model_table(spec_order_class)
        sql, _ = expr.to_sql()
        assert "UNIQUE" in sql
        assert "CHECK" in sql

    def test_unique_constraint_enforced(self, spec_order_class):
        _create_model_table(spec_order_class)
        first = spec_order_class(code="A1", status="open")
        first.save()
        dup = spec_order_class(code="A1", status="open")
        with pytest.raises(Exception):
            dup.save()

    def test_check_constraint_enforced(self, spec_order_class):
        _create_model_table(spec_order_class)
        bad = spec_order_class(code="A2", status="bogus")
        with pytest.raises(Exception):
            bad.save()

    def test_round_trip(self, spec_order_class):
        _create_model_table(spec_order_class)
        order = spec_order_class(code="B1", status="paid", quantity=3, total=9.9)
        order.save()
        found = spec_order_class.find_one({'id': order.id})
        assert found is not None
        assert found.code == "B1"
        assert found.status == "paid"


class TestCapabilitySpecDerivation:
    """CapabilityPost: capability-gated Specs claim-or-ignore per backend."""

    def test_derive_and_execute(self, capability_class):
        expr = _create_model_table(capability_class)
        # Whatever the backend claims (partial index, JSON type, generated
        # column), derivation and execution succeed.
        assert "CREATE TABLE" in sql_text(expr)

    def test_round_trip(self, capability_class):
        _create_model_table(capability_class)
        post = capability_class(title="hello", views=2)
        post.save()
        found = capability_class.find_one({"id": post.id})
        assert found is not None
        assert found.title == "hello"


class TestPKAndFKSpecDerivation:
    """SpecComment: explicit integer PK + ForeignKeySpec + NotNullSpec."""

    def test_derive_and_execute(self, spec_comment_class):
        expr = _create_model_table(spec_comment_class)
        sql, _ = expr.to_sql()
        assert "FOREIGN KEY" in sql
        assert "REFERENCES" in sql

    def test_round_trip_with_parent(self, spec_comment_with_parent):
        comment_class, order_class = spec_comment_with_parent
        _create_model_table(comment_class)  # order table already created

        order = order_class(code="C1", status="open")
        order.save()
        comment = comment_class(comment_id=1, order_id=order.id, body="ok")
        comment.save()
        found = comment_class.find_one({"comment_id": 1})
        assert found is not None
        assert found.body == "ok"


def sql_text(expr):
    sql, _ = expr.to_sql()
    return sql
