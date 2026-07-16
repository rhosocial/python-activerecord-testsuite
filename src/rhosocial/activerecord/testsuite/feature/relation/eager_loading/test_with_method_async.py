# src/rhosocial/activerecord/testsuite/feature/relation/eager_loading/test_with_method_async.py
"""
Async tests for with_() method and RelationConfig.
"""

from rhosocial.activerecord.query.relational import RelationConfig


class TestAsyncWithMethod:
    """Async tests for with_() method behavior."""

    async def test_with_no_relations(self, async_user_class):
        """with_() with no arguments should not add any relations."""
        query = async_user_class.query()
        configs = query.get_relation_configs()
        assert len(configs) == 0

    async def test_with_single_string_relation(self, async_user_class):
        """with_() with single string should add the relation."""
        query = async_user_class.query()
        query.with_("posts")

        configs = query.get_relation_configs()
        assert "posts" in configs
        assert configs["posts"].query_modifier is None

    async def test_with_single_tuple_relation(self, async_user_class):
        """with_() with tuple (path, modifier) should add the relation with modifier."""
        def my_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", my_modifier))

        configs = query.get_relation_configs()
        assert "posts" in configs
        assert configs["posts"].query_modifier is my_modifier

    async def test_with_none_modifier(self, async_user_class):
        """with_() with None modifier should add the relation without modifier."""
        query = async_user_class.query()
        query.with_(("posts", None))

        configs = query.get_relation_configs()
        assert "posts" in configs
        assert configs["posts"].query_modifier is None

    async def test_multiple_relations_with_validation(self, async_user_class):
        """with_() with multiple relations should validate all."""
        query = async_user_class.query()
        query.with_("posts", "posts.comments")

        configs = query.get_relation_configs()
        assert "posts" in configs
        assert "posts.comments" in configs


class TestAsyncRelationConfig:
    """Async tests for RelationConfig dataclass."""

    async def test_relation_config_defaults(self, async_user_class):
        """RelationConfig should have correct defaults."""
        config = RelationConfig(name="test", nested=False, query_modifier=None)
        assert config.name == "test"
        assert config.nested is False
        assert config.query_modifier is None

    async def test_relation_config_with_modifier(self, async_user_class):
        """RelationConfig should store modifier."""
        def my_modifier(q):
            return q

        config = RelationConfig(name="test", nested=False, query_modifier=my_modifier)
        assert config.query_modifier is my_modifier

    async def test_get_relation_configs_empty(self, async_user_class):
        """get_relation_configs should return empty dict initially."""
        query = async_user_class.query()
        configs = query.get_relation_configs()
        assert len(configs) == 0

    async def test_get_relation_configs_returns_copy(self, async_user_class):
        """get_relation_configs should return a copy."""
        query = async_user_class.query()
        query.with_("posts")

        configs1 = query.get_relation_configs()
        configs2 = query.get_relation_configs()
        assert configs1 == configs2
        assert configs1 is not configs2
