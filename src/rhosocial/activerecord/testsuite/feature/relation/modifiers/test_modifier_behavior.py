# src/rhosocial/activerecord/testsuite/feature/relation/modifiers/test_modifier_behavior.py
"""
Tests for with_() method modifier behavior.

Tests modifier targeting (leaf-only, intermediate untouched),
modifier overwrite semantics (later overwrites earlier), and
documentation example parity. Both sync and async variants exist.
"""
import pytest


class TestModifierTargeting:
    """Tests that modifiers only apply to the target relation."""

    def test_modifier_only_on_target_not_intermediate(self, user_class):
        """Modifier should only apply to the target, not intermediate paths."""
        def my_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts.comments", my_modifier))

        configs = query.get_relation_configs()
        assert "posts" in configs, "Expected 'posts' in relation configs"
        assert "posts.comments" in configs, "Expected 'posts.comments' in relation configs"
        assert configs["posts"].query_modifier is None, "Expected intermediate modifier to be None"
        assert configs["posts.comments"].query_modifier is my_modifier, \
            "Expected target modifier to be set"

    def test_deep_nested_modifier_only_on_leaf(self, user_class):
        """Deep nested modifier should only apply to the leaf."""
        def leaf_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts.comments", leaf_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is None, "Expected intermediate modifier to be None"
        assert configs["posts.comments"].query_modifier is leaf_modifier, \
            "Expected leaf modifier to be set"

    def test_multiple_relations_each_with_own_modifier(self, user_class):
        """Each relation can have its own modifier (parent before child)."""
        def posts_modifier(q):
            return q

        def comments_modifier(q):
            return q

        query = user_class.query()
        # Note: posts_modifier must come AFTER comments_modifier to avoid overwrite
        # due to parameter expansion rule
        query.with_(("posts.comments", comments_modifier), ("posts", posts_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is posts_modifier, "Expected posts modifier to be set"
        assert configs["posts.comments"].query_modifier is comments_modifier, \
            "Expected comments modifier to be set"


class TestModifierOverwrite:
    """Tests for modifier overwrite behavior."""

    def test_simple_path_with_modifier(self, user_class):
        """Simple path with modifier should store the modifier."""
        def my_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts", my_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is my_modifier, "Expected modifier to be set"

    def test_later_modifier_overwrites_same_path(self, user_class):
        """Later modifier should overwrite same path."""
        def first_modifier(q):
            return q

        def second_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts", first_modifier))
        query.with_(("posts", second_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is second_modifier, "Expected later modifier to overwrite"

    def test_longer_path_overwrites_shorter_path(self, user_class):
        """Longer path should overwrite shorter path when adding new nested."""
        def short_modifier(q):
            return q

        def long_modifier(q):
            return q

        query = user_class.query()
        # ("posts", short_modifier) -> posts: short_modifier
        # ("posts.comments", long_modifier) -> posts: long_modifier (adding new nested), posts.comments: long_modifier
        query.with_(("posts", short_modifier), ("posts.comments", long_modifier))

        configs = query.get_relation_configs()
        # posts gets long_modifier because we're adding new nested "comments"
        assert configs["posts"].query_modifier is long_modifier, "Expected long modifier on posts"
        assert configs["posts.comments"].query_modifier is long_modifier, \
            "Expected long modifier on posts.comments"

    def test_correct_order_preserves_modifiers(self, user_class):
        """Correct order (child before parent) preserves modifiers."""
        def parent_modifier(q):
            return q

        def child_modifier(q):
            return q

        query = user_class.query()
        # Child first, then parent - parent modifier won't be overwritten
        query.with_(("posts.comments", child_modifier), ("posts", parent_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is parent_modifier, "Expected parent modifier to be set"
        assert configs["posts.comments"].query_modifier is child_modifier, \
            "Expected child modifier to be set"


class TestModifierDocumentationExamples:
    """Tests for documentation examples."""

    def test_documentation_example_expansion(self, user_class):
        """Test documentation example: expansion rule."""
        def modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts.comments", modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is None, "Expected intermediate modifier to be None"
        assert configs["posts.comments"].query_modifier is modifier, \
            "Expected target modifier to be set"

    def test_documentation_example_overwrite(self, user_class):
        """Test documentation example: overwrite rule."""
        def first(q):
            return q

        def second(q):
            return q

        query = user_class.query()
        query.with_(("posts", first))
        query.with_(("posts", second))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is second, "Expected later modifier to overwrite"

    def test_documentation_correct_order(self, user_class):
        """Test documentation example: correct order (child before parent)."""
        def posts_mod(q):
            return q

        def comments_mod(q):
            return q

        query = user_class.query()
        # Put child first, then parent to avoid overwrite
        query.with_(("posts.comments", comments_mod), ("posts", posts_mod))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is posts_mod, "Expected posts modifier to be set"
        assert configs["posts.comments"].query_modifier is comments_mod, \
            "Expected comments modifier to be set"
