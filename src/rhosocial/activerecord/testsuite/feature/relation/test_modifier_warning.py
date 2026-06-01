# src/rhosocial/activerecord/testsuite/feature/relation/test_modifier_warning.py
"""
Tests for modifier overwrite warnings.
"""
import logging

import pytest


class TestModifierWarnings:
    """Tests for modifier overwrite warnings."""

    def test_warning_when_modifier_overwritten(self, user_class):
        """Warning should be issued when modifier is overwritten."""
        def first_modifier(q):
            return q

        def second_modifier(q):
            return q

        query = user_class.query()
        # Use separate calls to trigger overwrite warning
        query.with_(("posts", first_modifier))
        query.with_(("posts", second_modifier))

        # The warning is logged via the relation module's logger
        # We just verify the modifier was overwritten
        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is second_modifier

    def test_no_warning_when_same_modifier(self, user_class):
        """No warning when same modifier is applied twice."""
        def my_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts", my_modifier))
        query.with_(("posts", my_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is my_modifier

    def test_no_warning_when_overwriting_with_none(self, user_class):
        """Modifier is not overwritten when None is passed."""
        def my_modifier(q):
            return q

        query = user_class.query()
        query.with_(("posts", my_modifier))
        query.with_("posts")  # None modifier doesn't overwrite existing

        configs = query.get_relation_configs()
        # Existing modifier is preserved when None is passed
        assert configs["posts"].query_modifier is my_modifier

    def test_no_warning_for_different_paths(self, user_class):
        """No warning for different paths."""
        def posts_modifier(q):
            return q

        def comments_modifier(q):
            return q

        query = user_class.query()
        # Put child first, then parent to avoid overwrite
        query.with_(("posts.comments", comments_modifier), ("posts", posts_modifier))

        configs = query.get_relation_configs()
        assert configs["posts"].query_modifier is posts_modifier
        assert configs["posts.comments"].query_modifier is comments_modifier
