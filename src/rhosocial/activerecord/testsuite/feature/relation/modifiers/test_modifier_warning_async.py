# src/rhosocial/activerecord/testsuite/feature/relation/modifiers/test_modifier_warning_async.py
"""
Async tests for modifier overwrite warnings.
"""
import logging



class TestAsyncModifierWarnings:
    """Async tests for modifier overwrite warnings."""

    async def test_warning_when_modifier_overwritten(self, async_user_class):
        """Warning should be issued when modifier is overwritten."""
        def first_modifier(q):
            return q

        def second_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", first_modifier))
        query.with_(("posts", second_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is second_modifier, \
            "Expected the second modifier to overwrite the first"

    async def test_no_warning_when_same_modifier(self, async_user_class):
        """No warning when same modifier is applied twice."""
        def my_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", my_modifier))
        query.with_(("posts", my_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is my_modifier, \
            "Expected 'posts' relation to use the modifier"

    async def test_no_warning_when_overwriting_with_none(self, async_user_class):
        """Modifier is not overwritten when None is passed."""
        def my_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts", my_modifier))
        query.with_("posts")  # None modifier doesn't overwrite existing

        configs = query.get_relation_configs()
        # Existing modifier is preserved when None is passed
        assert configs["posts"].query_modifier is my_modifier, \
            "Expected the existing modifier to be preserved when None is passed"

    async def test_no_warning_for_different_paths(self, async_user_class):
        """No warning for different paths."""
        def posts_modifier(q):
            return q

        def comments_modifier(q):
            return q

        query = async_user_class.query()
        query.with_(("posts.comments", comments_modifier), ("posts", posts_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is posts_modifier, \
            "Expected 'posts' relation to use posts_modifier"
        assert configs["posts.comments"].query_modifier is comments_modifier, \
            "Expected 'posts.comments' relation to use comments_modifier"


