# src/rhosocial/activerecord/testsuite/feature/query/joins/test_self_join_async.py
"""Async self-join coverage via runtime-derived aliased proxies."""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol

from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode


async def _seed_tree(async_tree_fixtures):
    NodeModel = async_tree_fixtures[0]
    named = {}
    for name, parent, value in (
        ("root", None, 1),
        ("a", "root", 10),
        ("b", "root", 20),
    ):
        node = NodeModel(name=name, value=value)
        if parent is not None:
            node.parent_id = named[parent].id
        await node.save()
        named[name] = node
    return named


@requires_protocol("JoinSupport", "supports_inner_join")
async def test_async_self_join_child_to_parent(async_tree_fixtures):
    await _seed_tree(async_tree_fixtures)

    child = AsyncNode.c.with_table_alias("child")
    rows = (
        await AsyncNode.query()
        .join(AsyncNode, on=child.parent_id == AsyncNode.c.id, alias="child")
        .select(child.name.as_("child_name"), AsyncNode.c.name.as_("parent_name"))
        .where(AsyncNode.c.name == "root")
        .order_by(child.name)
        .aggregate()
    )
    assert [(r["child_name"], r["parent_name"]) for r in rows] == [("a", "root"), ("b", "root")]


@requires_protocol("JoinSupport", "supports_left_join")
async def test_async_self_join_left_keeps_roots(async_tree_fixtures):
    await _seed_tree(async_tree_fixtures)

    child = AsyncNode.c.with_table_alias("kid")
    rows = (
        await AsyncNode.query()
        .left_join(AsyncNode, on=child.parent_id == AsyncNode.c.id, alias="kid")
        .select(AsyncNode.c.name.as_("node"), child.name.as_("child_name"))
        .where(AsyncNode.c.parent_id.is_null())
        .aggregate()
    )
    assert [(r["node"], r["child_name"]) for r in rows] == [("root", "a"), ("root", "b")]
