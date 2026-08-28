# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_subquery.py
"""JOIN combined with subqueries: IN-filters over joined ranges and
aggregate-subquery comparisons."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("JoinSupport", "supports_inner_join")
def test_join_filtered_by_in_subquery(order_fixtures):
    """Only users having a 'big' order survive an IN-subquery filter."""
    User, Order, _ = order_fixtures

    rich = User(username="sub_rich", email="sr@example.com", age=60)
    poor = User(username="sub_poor", email="sp@example.com", age=61)
    rich.save()
    poor.save()
    Order(user_id=rich.id, order_number="r1", total_amount=999).save()
    Order(user_id=poor.id, order_number="p1", total_amount=1).save()

    big_orders = Order.query().select(Order.c.user_id).where(Order.c.total_amount > 100)
    rows = (
        User.query()
        .join(Order, on=User.c.id == Order.c.user_id)
        .where(User.c.id.in_(big_orders))
        .select(User.c.username)
        .aggregate()
    )
    assert [r["username"] for r in rows] == ["sub_rich"]


@requires_protocol("JoinSupport", "supports_inner_join")
def test_three_table_join_with_in_subquery(order_fixtures):
    """Chained joins remain composable with a subquery predicate."""
    User, Order, OrderItem = order_fixtures

    user = User(username="chain_sub", email="cs@example.com", age=35)
    user.save()
    order = Order(user_id=user.id, order_number="c1")
    order.save()
    OrderItem(order_id=order.id, product_name="widget", quantity=5, unit_price=20).save()

    target_items = OrderItem.query().select(OrderItem.c.order_id).where(OrderItem.c.quantity >= 5)
    rows = (
        User.query()
        .join(Order, on=User.c.id == Order.c.user_id)
        .inner_join(OrderItem, on=Order.c.id == OrderItem.c.order_id)
        .where(Order.c.id.in_(target_items))
        .select(User.c.username, Order.c.order_number)
        .aggregate()
    )
    assert [(r["username"], r["order_number"]) for r in rows] == [("chain_sub", "c1")]
