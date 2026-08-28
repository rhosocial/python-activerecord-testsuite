# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_types.py
"""Outer, cross and mixed-type join coverage for ActiveQuery.

Verifies the row-preservation semantics of each JOIN type (the most common
regression area) rather than only the happy-path matched rows.
"""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


def _user_without_orders(users):
    """Create a user that places no orders; returns the model instance."""
    lonely = users[0](username="lonely", email="lonely@example.com", age=40)
    lonely.save()
    return lonely


@requires_protocol("JoinSupport", "supports_left_join")
def test_left_join_preserves_unmatched_left_rows(order_fixtures):
    """Rows without a match still appear, right-side columns being NULL."""
    User, Order, _ = order_fixtures
    _user_without_orders([User])

    rows = (
        User.query()
        .left_join(Order, on=User.c.id == Order.c.user_id)
        .select(User.c.username, Order.c.id.as_("order_id"))
        .aggregate()
    )
    lonely_rows = [r for r in rows if r["username"] == "lonely"]
    assert len(lonely_rows) == 1
    assert lonely_rows[0]["order_id"] is None


@requires_protocol("JoinSupport", "supports_right_join")
def test_right_join_preserves_right_side(order_fixtures):
    """RIGHT JOIN keeps every right-hand row even when left side has gaps."""
    User, Order, _ = order_fixtures
    _user_without_orders([User])

    total_orders = Order.query().count()
    joined = (
        Order.query()
        .right_join(User, on=Order.c.user_id == User.c.id)
        .select(Order.c.id.as_("order_id"))
        .aggregate()
    )
    assert len(joined) == total_orders


@requires_protocol("JoinSupport", "supports_full_join")
def test_full_outer_join_covers_both_sides(order_fixtures):
    """FULL OUTER JOIN yields unmatched rows of both sides exactly once."""
    User, Order, _ = order_fixtures
    lonely = _user_without_orders([User])

    orders_total = Order.query().count()
    users_total = User.query().count()
    users_with_orders = (
        User.query().join(Order, on=User.c.id == Order.c.user_id).aggregate()
    )

    rows = (
        User.query()
        .full_join(Order, on=User.c.id == Order.c.user_id)
        .select(User.c.username, Order.c.id.as_("order_id"))
        .aggregate()
    )
    # Every order appears; every user without orders adds one NULL-extended row.
    matched_users = len({r["username"] for r in rows if r["order_id"] is not None})
    null_extended = [r for r in rows if r["order_id"] is None]
    assert len(rows) == orders_total + (users_total - matched_users)
    assert [r["username"] for r in null_extended] == ["lonely"]


@requires_protocol("JoinSupport", "supports_cross_join")
def test_cross_join_is_cartesian(order_fixtures):
    """CROSS JOIN produces |left| x |right| rows without an ON clause."""
    User, Order, _ = order_fixtures

    users_total = User.query().count()
    orders_total = Order.query().count()

    rows = User.query().cross_join(Order).select(User.c.username).aggregate()
    assert len(rows) == users_total * orders_total


@requires_protocol("JoinSupport", "supports_straight_join")
def test_straight_join_returns_inner_equivalent(order_fixtures):
    """STRAIGHT_JOIN is result-equivalent to INNER JOIN (MySQL optimizer hint)."""
    User, Order, _ = order_fixtures

    inner = User.query().join(Order, on=User.c.id == Order.c.user_id).aggregate()
    straight = (
        User.query()
        .straight_join(Order, on=User.c.id == Order.c.user_id)
        .aggregate()
    )
    assert len(straight) == len(inner)


def test_mixed_type_join_chain(order_fixtures):
    """LEFT and INNER joins can be chained with preserved per-hop semantics."""
    User, Order, OrderItem = order_fixtures

    lonely = _user_without_orders([User])
    buyer = User(username="buyer", email="buyer@example.com", age=31)
    buyer.save()
    order = Order(user_id=buyer.id, order_number="mix-1", total_amount=50)
    order.save()

    rows = (
        User.query()
        .left_join(Order, on=User.c.id == Order.c.user_id)
        .inner_join(OrderItem, on=Order.c.id == OrderItem.c.order_id)
        .select(User.c.username, OrderItem.c.id.as_("item_id"))
        .aggregate()
    )
    # Only users whose orders have items survive the trailing INNER hop;
    # the lonely user's NULL-extended row cannot satisfy it.
    assert all(r["username"] != "lonely" for r in rows)
