# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/test_cross_schema_join_async.py
"""Async variant of the cross-schema ActiveRecord / ActiveQuery tests."""

import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@pytest.mark.requires_protocol("SchemaSupport", "supports_schema")
async def test_async_cross_schema_join(async_schema_fixtures):
    """JOIN across two schemas with WHERE + ORDER BY (async)."""
    AsyncCustomer, AsyncOrder = async_schema_fixtures

    alice = AsyncCustomer(name="async_alice")
    await alice.save()
    bob = AsyncCustomer(name="async_bob")
    await bob.save()

    for cust, amount in ((alice, 100), (bob, 200), (alice, 300)):
        await AsyncOrder(customer_id=cust.id, amount=amount).save()

    rows = await (
        AsyncOrder.query()
        .join(AsyncCustomer, on=AsyncOrder.c.customer_id == AsyncCustomer.c.id)
        .select(AsyncOrder.c.amount, AsyncCustomer.c.name.as_("customer"))
        .where(AsyncCustomer.c.name == "async_alice")
        .order_by(AsyncOrder.c.amount)
        .aggregate()
    )
    assert [(r["amount"], r["customer"]) for r in rows] == [
        (100, "async_alice"),
        (300, "async_alice"),
    ]


@pytest.mark.requires_protocol("SchemaSupport", "supports_schema")
async def test_async_cross_schema_writes_are_scoped(async_schema_fixtures):
    """Writes land in the owning schema and stay scoped by qualifiers (async)."""
    AsyncCustomer, AsyncOrder = async_schema_fixtures

    cust = AsyncCustomer(name="async_writer")
    await cust.save()
    order = AsyncOrder(customer_id=cust.id, amount=42)
    await order.save()

    assert await AsyncOrder.query().where(AsyncOrder.c.id == order.id).count() == 1
    assert await AsyncCustomer.query().where(AsyncCustomer.c.id == cust.id).count() == 1

    await AsyncOrder.query().where(AsyncOrder.c.id == order.id).update_all({"amount": 43})
    refreshed = await AsyncOrder.query().where(AsyncOrder.c.id == order.id).one()
    assert refreshed.amount == 43

    await AsyncOrder.query().where(AsyncOrder.c.id == order.id).delete_all()
    assert await AsyncOrder.query().where(AsyncOrder.c.id == order.id).count() == 0
    assert await AsyncCustomer.query().where(AsyncCustomer.c.id == cust.id).count() == 1
