# src/rhosocial/activerecord/testsuite/feature/relation/test_modifier_behavior_async.py
"""
Async tests for with_() method modifier behavior.
"""
import pytest


class TestAsyncModifierTargeting:
    """Async tests that modifiers only apply to the target relation."""

    @pytest.mark.asyncio
    async def test_modifier_only_on_target_not_intermediate(self, async_user_class):
        """Modifier should only apply to the target, not intermediate paths."""
        def my_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts.comments", my_modifier))

        configs = query.get_relation_configs()
        assert "posts" in configs
        assert "posts.comments" in configs
        assert configs["posts"].query_modifier is None
        assert configs["posts.comments"].query_modifier is my_modifier

    @pytest.mark.asyncio
    async def test_deep_nested_modifier_only_on_leaf(self, async_user_class):
        """Deep nested modifier should only apply to the leaf."""
        def leaf_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts.comments", leaf_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is None
        assert configs["posts.comments"].query_modifier is leaf_modifier

    @pytest.mark.asyncio
    async def test_multiple_relations_each_with_own_modifier(self, async_user_class):
        """Each relation can have its own modifier (parent before child)."""
        def posts_modifier(q):
            return q

        def comments_modifier(q):
            return q

        query = async_user_class.query()
        # Note: posts_modifier must come AFTER comments_modifier to avoid overwrite
        # due to parameter expansion rule
        query.with_(("posts.comments", comments_modifier), ("posts", posts_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is posts_modifier
        assert configs["posts.comments"].query_modifier is comments_modifier


class TestAsyncModifierOverwrite:
    """Async tests for modifier overwrite behavior."""

    @pytest.mark.asyncio
    async def test_simple_path_with_modifier(self, async_user_class):
        """Simple path with modifier should store the modifier."""
        def my_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", my_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is my_modifier

    @pytest.mark.asyncio
    async def test_later_modifier_overwrites_same_path(self, async_user_class):
        """Later modifier should overwrite same path."""
        def first_modifier(q):
            return q

        def second_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", first_modifier))
        query.with_(("posts", second_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is second_modifier

    @pytest.mark.asyncio
    async def test_correct_order_preserves_modifiers(self, async_user_class):
        """Correct order (child before parent) preserves modifiers."""
        def parent_modifier(q):
            return q

        def child_modifier(q):
            return q

        query = async_user_class.query()
        # Child first, then parent - parent modifier won't be overwritten
        query.with_(("posts.comments", child_modifier), ("posts", parent_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is parent_modifier
        assert configs["posts.comments"].query_modifier is child_modifier
