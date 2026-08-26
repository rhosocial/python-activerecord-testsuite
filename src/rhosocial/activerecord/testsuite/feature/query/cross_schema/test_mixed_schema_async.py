# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/test_mixed_schema_async.py
"""Async default-schema vs non-default-schema operations for identical tables."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("SchemaSupport", "supports_schema")
async def test_async_same_named_tables_coexist(async_mixed_schema_fixtures):
    """Identical table names in default and SCHEMA_A hold independent rows."""
    AsyncUser, AsyncOrder, AsyncMixedSchemaOrder = async_mixed_schema_fixtures

    user = AsyncUser(username="coexist", email="coexist@example.com", age=30)
    await user.save()
    await AsyncOrder(user_id=user.id, order_number="def-1", total_amount=10).save()
    await AsyncMixedSchemaOrder(
        user_id=user.id, order_number="sch-1", total_amount=100
    ).save()

    assert await AsyncOrder.query().count() == 1
    assert await AsyncMixedSchemaOrder.query().count() == 1


@requires_protocol("SchemaSupport", "supports_schema")
async def test_async_update_all_stays_scoped(async_mixed_schema_fixtures):
    """Bulk update on the schema-qualified namespace leaves defaults untouched."""
    AsyncUser, AsyncOrder, AsyncMixedSchemaOrder = async_mixed_schema_fixtures

    user = AsyncUser(username="scoped", email="scoped@example.com", age=30)
    await user.save()
    await AsyncOrder(user_id=user.id, order_number="d1").save()
    await AsyncMixedSchemaOrder(user_id=user.id, order_number="s1").save()
    await AsyncMixedSchemaOrder(user_id=user.id, order_number="s2").save()

    await AsyncMixedSchemaOrder.query().where(
        AsyncMixedSchemaOrder.c.user_id == user.id
    ).update_all({"status": "shipped"})
    assert await AsyncOrder.query().where(AsyncOrder.c.status == "pending").count() == 1
    assert (
        await AsyncMixedSchemaOrder.query()
        .where(AsyncMixedSchemaOrder.c.status == "shipped")
        .count()
        == 2
    )


@requires_protocol("SchemaSupport", "supports_schema")
async def test_async_join_default_user_with_schema_order(async_mixed_schema_fixtures):
    """Async JOIN from the default namespace to a schema-qualified table."""
    AsyncUser, AsyncOrder, AsyncMixedSchemaOrder = async_mixed_schema_fixtures

    alice = AsyncUser(username="alice", email="alice@example.com", age=30)
    bob = AsyncUser(username="bob", email="bob@example.com", age=30)
    await alice.save()
    await bob.save()
    await AsyncMixedSchemaOrder(user_id=alice.id, order_number="j1", total_amount=5).save()
    await AsyncMixedSchemaOrder(user_id=bob.id, order_number="j2", total_amount=7).save()

    rows = (
        await AsyncMixedSchemaOrder.query()
        .join(AsyncUser, on=AsyncMixedSchemaOrder.c.user_id == AsyncUser.c.id)
        .select(AsyncMixedSchemaOrder.c.order_number, AsyncUser.c.username.as_("owner"))
        .where(AsyncUser.c.username == "alice")
        .aggregate()
    )
    assert [(r["order_number"], r["owner"]) for r in rows] == [("j1", "alice")]
