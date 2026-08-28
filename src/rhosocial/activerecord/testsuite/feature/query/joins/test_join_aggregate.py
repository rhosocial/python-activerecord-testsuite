# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_aggregate.py
"""JOIN combined with aggregation: GROUP BY / HAVING over joined ranges."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol

from rhosocial.activerecord.backend.expression import functions


@requires_protocol("JoinSupport", "supports_inner_join")
def test_join_group_by_count(order_fixtures):
    """Count orders per user across the join."""
    User, Order, _ = order_fixtures
    dialect = User.__backend__.dialect

    alice = User(username="agg_alice", email="aa@example.com", age=30)
    bob = User(username="agg_bob", email="ab@example.com", age=31)
    alice.save()
    bob.save()
    Order(user_id=alice.id, order_number="g1").save()
    Order(user_id=alice.id, order_number="g2").save()
    Order(user_id=bob.id, order_number="g3").save()

    rows = (
        User.query()
        .join(Order, on=User.c.id == Order.c.user_id)
        .select(User.c.username, functions.count(dialect, Order.c.id).as_("n_orders"))
        .group_by(User.c.username)
        .aggregate()
    )
    counts = {r["username"]: r["n_orders"] for r in rows}
    assert counts == {"agg_alice": 2, "agg_bob": 1}


@requires_protocol("JoinSupport", "supports_inner_join")
def test_join_group_by_sum_having(order_fixtures):
    """HAVING filters aggregated groups after a join."""
    User, Order, _ = order_fixtures
    dialect = User.__backend__.dialect

    big = User(username="big_spender", email="bs@example.com", age=50)
    small = User(username="small_fry", email="sf@example.com", age=22)
    big.save()
    small.save()
    for i in range(3):
        Order(user_id=big.id, order_number=f"b{i}", total_amount=100 + i).save()
    Order(user_id=small.id, order_number="s1", total_amount=10).save()

    rows = (
        User.query()
        .join(Order, on=User.c.id == Order.c.user_id)
        .select(
            User.c.username,
            functions.sum_(dialect, Order.c.total_amount).as_("spent"),
            functions.count(dialect, Order.c.id).as_("n"),
        )
        .group_by(User.c.username)
        .having(functions.count(dialect, Order.c.id) > 1)
        .aggregate()
    )
    assert [(r["username"], r["spent"], r["n"]) for r in rows] == [("big_spender", 303, 3)]
