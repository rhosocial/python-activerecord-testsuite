# src/rhosocial/activerecord/testsuite/feature/query/joins/test_self_join.py
"""True self-join coverage: one table joined to itself under two aliases.

The ActiveRecord-level mechanism is a runtime-derived second proxy:
``Node.c.with_table_alias(alias)`` yields a static ``alias.column``
accessor that pairs with ``join(Node, on=..., alias=alias)``.
"""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol

from rhosocial.activerecord.backend.expression import functions

from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node


def _seed_tree(tree_fixtures):
    """root -> (a, b); a -> a1. Returns nodes keyed by name."""
    NodeModel = tree_fixtures[0]
    named = {}
    for name, parent, value in (
        ("root", None, 1),
        ("a", "root", 10),
        ("b", "root", 20),
        ("a1", "a", 100),
    ):
        node = NodeModel(name=name, value=value)
        if parent is not None:
            node.parent_id = named[parent].id
        node.save()
        named[name] = node
    return named


@requires_protocol("JoinSupport", "supports_inner_join")
def test_self_join_child_to_parent(tree_fixtures):
    _seed_tree(tree_fixtures)

    child = Node.c.with_table_alias("child")
    rows = (
        Node.query()
        .join(Node, on=child.parent_id == Node.c.id, alias="child")
        .select(child.name.as_("child_name"), Node.c.name.as_("parent_name"))
        .where(Node.c.name == "root")
        .order_by(child.name)
        .aggregate()
    )
    assert [(r["child_name"], r["parent_name"]) for r in rows] == [("a", "root"), ("b", "root")]


@requires_protocol("JoinSupport", "supports_left_join")
def test_self_join_left_keeps_roots(tree_fixtures):
    """LEFT self-join keeps parents without parents of their own."""
    _seed_tree(tree_fixtures)

    child = Node.c.with_table_alias("kid")
    rows = (
        Node.query()
        .left_join(Node, on=child.parent_id == Node.c.id, alias="kid")
        .select(Node.c.name.as_("node"), child.name.as_("child_name"))
        .where(Node.c.parent_id.is_null())
        .aggregate()
    )
    assert [(r["node"], r["child_name"]) for r in rows] == [("root", "a"), ("root", "b")]


@requires_protocol("JoinSupport", "supports_inner_join")
def test_self_join_aggregates_children_per_parent(tree_fixtures):
    _seed_tree(tree_fixtures)

    child = Node.c.with_table_alias("kid")
    dialect = Node.__backend__.dialect
    rows = (
        Node.query()
        .join(Node, on=child.parent_id == Node.c.id, alias="kid")
        .select(
            Node.c.name.as_("parent"),
            functions.count(dialect, child.value).as_("n_children"),
            functions.sum_(dialect, child.value).as_("value_sum"),
        )
        .group_by(Node.c.name)
        .having(functions.count(dialect, child.value) > 1)
        .aggregate()
    )
    assert [(r["parent"], r["n_children"], r["value_sum"]) for r in rows] == [("root", 2, 30)]
