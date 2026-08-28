# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_using_async.py
"""Async USING-clause join coverage."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("JoinSupport", "supports_inner_join")
async def test_inner_join_with_using_column(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures

    user = AsyncUser(username="using_user", email="using@example.com", age=33)
    await user.save()
    await AsyncOrder(user_id=user.id, order_number="u1", total_amount=11).save()

    rows = (
        await AsyncUser.query()
        .inner_join(AsyncOrder, using=["id"])
        .select(AsyncUser.c.username, AsyncOrder.c.order_number)
        .aggregate()
    )
    assert [r["order_number"] for r in rows] == ["u1"]


@requires_protocol("JoinSupport", "supports_left_join")
async def test_left_join_with_using(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures

    lonely = AsyncUser(username="lonely_using", email="lu@example.com", age=44)
    await lonely.save()
    buyer = AsyncUser(username="buyer_using", email="bu@example.com", age=45)
    await buyer.save()
    # Advance the orders sequence so this order's id lands on buyer.id,
    # letting USING ("id") pair them while lonely keeps no match.
    await AsyncOrder(user_id=lonely.id, order_number="tmp").save()
    await AsyncOrder.query().where(AsyncOrder.c.order_number == "tmp").delete_all()
    await AsyncOrder(user_id=buyer.id, order_number="u2", total_amount=12).save()

    rows = (
        await AsyncUser.query()
        .left_join(AsyncOrder, using=["id"])
        .select(AsyncUser.c.username, AsyncOrder.c.id.as_("order_id"))
        .aggregate()
    )
    by_name = {r["username"]: r["order_id"] for r in rows}
    assert by_name["lonely_using"] is None
    assert by_name["buyer_using"] is not None


async def test_on_and_using_are_mutually_exclusive(async_order_fixtures):
    AsyncUser, AsyncOrder, _ = async_order_fixtures

    with pytest.raises(ValueError):
        AsyncUser.query().join(
            AsyncOrder, on=AsyncUser.c.id == AsyncOrder.c.user_id, using=["user_id"]
        )
