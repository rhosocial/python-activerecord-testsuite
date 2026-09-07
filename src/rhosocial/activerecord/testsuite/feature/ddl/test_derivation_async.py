# src/rhosocial/activerecord/testsuite/feature/ddl/test_derivation_async.py
"""
feature.ddl: derivation round-trip (async) — async twin of test_derivation.
"""
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError


def _create_model_table_on(backend, model):
    """Derive *model*'s CREATE TABLE and execute it on a given backend."""
    expr = model.generate_create_table(backend.dialect)
    backend.execute(*expr.to_sql())
    return expr


def _create_model_table(model):
    """Idempotent derive-and-execute (drops leftovers first)."""
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


class TestZeroDeclarationDerivationAsync:
    async def test_derive_and_execute(self, async_bare_class):
        expr = _create_model_table(async_bare_class)
        sql, _ = expr.to_sql()
        assert "CREATE TABLE" in sql
        assert "PRIMARY KEY" in sql

    async def test_round_trip(self, async_bare_class):
        _create_model_table(async_bare_class)
        item = async_bare_class(name="a", quantity=2, price=1.5)
        await item.save()

        found = await async_bare_class.find_one({'id': item.id})
        assert found is not None
        assert found.name == "a"

        found.quantity = 5
        await found.save()
        again = await async_bare_class.find_one({'id': item.id})
        assert again.quantity == 5

    async def test_nullable_column_stays_nullable(self, async_bare_class):
        _create_model_table(async_bare_class)
        item = async_bare_class(name="n", quantity=1, price=1.0)
        await item.save()
        found = await async_bare_class.find_one({'id': item.id})
        assert found.note is None


class TestGenericSpecDerivationAsync:
    async def test_derive_and_execute(self, async_spec_order_class):
        expr = _create_model_table(async_spec_order_class)
        sql, _ = expr.to_sql()
        assert "UNIQUE" in sql
        assert "CHECK" in sql

    async def test_unique_constraint_enforced(self, async_spec_order_class):
        _create_model_table(async_spec_order_class)
        first = async_spec_order_class(code="A1", status="open")
        await first.save()
        dup = async_spec_order_class(code="A1", status="open")
        with pytest.raises(Exception):
            await dup.save()

    async def test_check_constraint_enforced(self, async_spec_order_class):
        _create_model_table(async_spec_order_class)
        bad = async_spec_order_class(code="A2", status="bogus")
        with pytest.raises(Exception):
            await bad.save()

    async def test_round_trip(self, async_spec_order_class):
        _create_model_table(async_spec_order_class)
        order = async_spec_order_class(code="B1", status="paid", quantity=3, total=9.9)
        await order.save()
        found = await async_spec_order_class.find_one({'id': order.id})
        assert found is not None
        assert found.code == "B1"


class TestCapabilitySpecDerivationAsync:
    async def test_derive_and_execute(self, async_capability_class):
        expr = _create_model_table(async_capability_class)
        sql, _ = expr.to_sql()
        assert "CREATE TABLE" in sql

    async def test_round_trip(self, async_capability_class):
        _create_model_table(async_capability_class)
        post = async_capability_class(title="hello", views=2)
        await post.save()
        found = await async_capability_class.find_one({"id": post.id})
        assert found is not None
        assert found.title == "hello"


class TestPKAndFKSpecDerivationAsync:
    async def test_derive_and_execute(self, async_spec_comment_class, async_spec_order_class):
        _create_model_table(async_spec_order_class)
        expr = _create_model_table(async_spec_comment_class)
        sql, _ = expr.to_sql()
        assert "FOREIGN KEY" in sql
        assert "REFERENCES" in sql

    async def test_round_trip_with_parent(self, async_spec_comment_with_parent):
        comment_class, order_class = async_spec_comment_with_parent
        _create_model_table(comment_class)  # order table already created

        order = order_class(code="C1", status="open")
        await order.save()
        comment = comment_class(comment_id=1, order_id=order.id, body="ok")
        await comment.save()
        found = await comment_class.find_one({"comment_id": 1})
        assert found is not None
        assert found.body == "ok"
