# src/rhosocial/activerecord/testsuite/feature/query/joins/test_join_qualifiers.py
"""Column-qualifier resolution contract under JOINs.

Locks the generated SQL *forms* (after quote/case normalisation) so dialect
regressions surface locally instead of as live-server errors:

- JOIN ranges keep schema qualifiers; column references stay two-part.
- Aliased self-join ranges are referenced by alias only.
"""
import re

import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


def _norm(sql: str) -> str:
    """Normalise rendered SQL: strip identifier quotes, fold case/space."""
    cleaned = sql.replace('"', "").replace("`", "").replace("[", "").replace("]", "")
    return re.sub(r"\s+", " ", cleaned).lower()


@requires_protocol("JoinSupport", "supports_inner_join")
def test_join_columns_are_table_qualified(order_fixtures):
    """ON predicates and select lists qualify columns with their table."""
    User, Order, _ = order_fixtures

    user = User(username="qual_user", email="qu@example.com", age=30)
    user.save()
    Order(user_id=user.id, order_number="q1").save()

    query = (
        User.query()
        .join(Order, on=User.c.id == Order.c.user_id)
        .select(User.c.username, Order.c.order_number)
        .where(User.c.username == "qual_user")
    )
    sql, params = query.to_sql()
    normed = _norm(sql)
    assert "users.id = orders.user_id" in normed
    assert "orders.user_id" in normed.split(" where ")[0]
    assert "users.username" in normed
    assert params == ("qual_user",) or params == ["qual_user"]

    rows = query.aggregate()
    assert [r["order_number"] for r in rows] == ["q1"]


@requires_protocol("JoinSupport", "supports_inner_join")
async def test_aliased_self_join_references_alias_only(tree_fixtures):
    """Self-join columns address the runtime alias, not the base table."""
    NodeModel = tree_fixtures[0]

    root = NodeModel(name="alias_root", value=1)
    root.save()
    kid = NodeModel(name="alias_kid", value=2)
    kid.parent_id = root.id
    kid.save()

    child = NodeModel.c.with_table_alias("child")
    query = NodeModel.query().join(
        NodeModel, on=child.parent_id == NodeModel.c.id, alias="child"
    ).select(child.name.as_("child_name"), NodeModel.c.name.as_("parent_name"))
    sql, _ = query.to_sql()
    normed = _norm(sql)

    assert "nodes as child" in normed or "nodes child" in normed
    assert "child.parent_id = nodes.id" in normed
    assert "child.name" in normed

    rows = query.aggregate()
    assert [(r["child_name"], r["parent_name"]) for r in rows] == [("alias_kid", "alias_root")]
