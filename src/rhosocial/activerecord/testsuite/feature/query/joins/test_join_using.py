# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_using.py
"""USING-clause join coverage.

``JoinExpression`` renders ``... JOIN ... USING ("col")`` when ``using``
columns are given instead of an ON predicate; the ActiveQuery convenience
methods forward the ``using`` keyword.
"""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("JoinSupport", "supports_inner_join")
def test_inner_join_with_using_column(order_fixtures):
    """JOIN ... USING ("id") pairs the tables' identical surrogate keys.

    Fresh per-test tables make autoincrement ids deterministic (both start
    at 1), giving an artificial but fully valid USING pairing.
    """
    User, Order, _ = order_fixtures

    user = User(username="using_user", email="using@example.com", age=33)
    user.save()
    Order(user_id=user.id, order_number="u1", total_amount=11).save()

    rows = (
        User.query()
        .inner_join(Order, using=["id"])
        .select(User.c.username, Order.c.order_number)
        .aggregate()
    )
    assert [r["order_number"] for r in rows] == ["u1"]


@requires_protocol("JoinSupport", "supports_left_join")
def test_left_join_with_using(order_fixtures):
    """LEFT JOIN ... USING keeps unmatched left rows like its ON counterpart."""
    User, Order, _ = order_fixtures

    lonely = User(username="lonely_using", email="lu@example.com", age=44)
    lonely.save()
    buyer = User(username="buyer_using", email="bu@example.com", age=45)
    buyer.save()
    # Advance the orders sequence so this order's id lands on buyer.id,
    # letting USING ("id") pair them while lonely keeps no match.
    Order(user_id=lonely.id, order_number="tmp").save()
    Order.query().where(Order.c.order_number == "tmp").delete_all()
    Order(user_id=buyer.id, order_number="u2", total_amount=12).save()

    rows = (
        User.query()
        .left_join(Order, using=["id"])
        .select(User.c.username, Order.c.id.as_("order_id"))
        .aggregate()
    )
    by_name = {r["username"]: r["order_id"] for r in rows}
    assert by_name["lonely_using"] is None
    assert by_name["buyer_using"] is not None


def test_on_and_using_are_mutually_exclusive(order_fixtures):
    """Passing both raises instead of generating ambiguous SQL."""
    User, Order, _ = order_fixtures

    with pytest.raises(ValueError):
        User.query().join(Order, on=User.c.id == Order.c.user_id, using=["user_id"])
