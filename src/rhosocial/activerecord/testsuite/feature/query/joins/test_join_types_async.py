# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_types_async.py
"""Async variants for outer, cross and mixed-type join coverage."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


async def _user_without_orders(users):
    lonely = users[0](username="lonely", email="lonely@example.com", age=40)
    await lonely.save()
    return lonely


@requires_protocol("JoinSupport", "supports_left_join")
async def test_left_join_preserves_unmatched_left_rows(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures
    await _user_without_orders([AsyncUser])

    rows = (
        await AsyncUser.query()
        .left_join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .select(AsyncUser.c.username, AsyncOrder.c.id.as_("order_id"))
        .aggregate()
    )
    lonely_rows = [r for r in rows if r["username"] == "lonely"]
    assert len(lonely_rows) == 1
    assert lonely_rows[0]["order_id"] is None


@requires_protocol("JoinSupport", "supports_right_join")
async def test_right_join_preserves_right_side(async_order_fixtures):
    AsyncOrder, AsyncUser = async_order_fixtures[1], async_order_fixtures[0]
    await _user_without_orders([async_order_fixtures[0]])

    total_orders = await AsyncOrder.query().count()
    joined = (
        await AsyncOrder.query()
        .right_join(AsyncUser, on=AsyncOrder.c.user_id == AsyncUser.c.id)
        .select(AsyncOrder.c.id.as_("order_id"))
        .aggregate()
    )
    assert len(joined) == total_orders


@requires_protocol("JoinSupport", "supports_full_join")
async def test_full_outer_join_covers_both_sides(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures
    await _user_without_orders([AsyncUser])

    orders_total = await AsyncOrder.query().count()
    users_total = await AsyncUser.query().count()

    rows = (
        await AsyncUser.query()
        .full_join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .select(AsyncUser.c.username, AsyncOrder.c.id.as_("order_id"))
        .aggregate()
    )
    matched_users = len({r["username"] for r in rows if r["order_id"] is not None})
    assert len(rows) == orders_total + (users_total - matched_users)


@requires_protocol("JoinSupport", "supports_cross_join")
async def test_cross_join_is_cartesian(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures

    users_total = await AsyncUser.query().count()
    orders_total = await AsyncOrder.query().count()

    rows = await (AsyncUser.query().cross_join(AsyncOrder).select(AsyncUser.c.username)).aggregate()
    assert len(rows) == users_total * orders_total


@requires_protocol("JoinSupport", "supports_straight_join")
async def test_straight_join_returns_inner_equivalent(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures

    inner = await (AsyncUser.query().join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)).aggregate()
    straight = (
        await AsyncUser.query()
        .straight_join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .aggregate()
    )
    assert len(straight) == len(inner)


async def test_mixed_type_join_chain(async_order_fixtures):
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    buyer = AsyncUser(username="buyer", email="buyer@example.com", age=31)
    await buyer.save()
    order = AsyncOrder(user_id=buyer.id, order_number="mix-1", total_amount=50)
    await order.save()

    rows = (
        await AsyncUser.query()
        .left_join(AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id)
        .inner_join(AsyncOrderItem, on=AsyncOrder.c.id == AsyncOrderItem.c.order_id)
        .select(AsyncUser.c.username, AsyncOrderItem.c.id.as_("item_id"))
        .aggregate()
    )
    assert all(r["username"] != "lonely" for r in rows)
