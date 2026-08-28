# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_aggregate_async.py
"""Async JOIN + aggregation coverage."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol

from rhosocial.activerecord.backend.expression import functions


@requires_protocol("JoinSupport", "supports_inner_join")
async def test_join_group_by_count(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures
    dialect = AsyncUser.__backend__.dialect

    alice = AsyncUser(username="agg_alice", email="aa@example.com", age=30)
    bob = AsyncUser(username="agg_bob", email="ab@example.com", age=31)
    await alice.save()
    await bob.save()
    await AsyncOrder(user_id=alice.id, order_number="g1").save()
    await AsyncOrder(user_id=alice.id, order_number="g2").save()
    await AsyncOrder(user_id=bob.id, order_number="g3").save()

    rows = (
        await AsyncUser.query()
        .join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .select(AsyncUser.c.username, functions.count(dialect, AsyncOrder.c.id).as_("n_orders"))
        .group_by(AsyncUser.c.username)
        .aggregate()
    )
    counts = {r["username"]: r["n_orders"] for r in rows}
    assert counts == {"agg_alice": 2, "agg_bob": 1}


@requires_protocol("JoinSupport", "supports_inner_join")
async def test_join_group_by_sum_having(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures
    dialect = AsyncUser.__backend__.dialect

    big = AsyncUser(username="big_spender", email="bs@example.com", age=50)
    small = AsyncUser(username="small_fry", email="sf@example.com", age=22)
    await big.save()
    await small.save()
    for i in range(3):
        await AsyncOrder(user_id=big.id, order_number=f"b{i}", total_amount=100 + i).save()
    await AsyncOrder(user_id=small.id, order_number="s1", total_amount=10).save()

    rows = (
        await AsyncUser.query()
        .join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .select(
            AsyncUser.c.username,
            functions.sum_(dialect, AsyncOrder.c.total_amount).as_("spent"),
            functions.count(dialect, AsyncOrder.c.id).as_("n"),
        )
        .group_by(AsyncUser.c.username)
        .having(functions.count(dialect, AsyncOrder.c.id) > 1)
        .aggregate()
    )
    assert [(r["username"], r["spent"], r["n"]) for r in rows] == [("big_spender", 303, 3)]
