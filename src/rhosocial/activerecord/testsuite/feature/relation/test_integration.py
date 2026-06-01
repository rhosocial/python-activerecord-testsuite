# src/rhosocial/activerecord/testsuite/feature/relation/test_integration.py
"""
Integration tests: relations + derived fields + field proxy + JSON.
"""
import pytest

from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol


class TestIntegration:
    """Integration tests for multiple features."""

    def test_relation_with_derived_fields(self, user_post_comment_classes):
        """Relations should work with derived fields."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Alice", email="alice@example.com")
        user.save()

        post = post_class(title="Hello World", body="Content", user_id=user.id, view_count=10)
        post.save()

        # Query posts with derived fields
        results = post_class.find_all(derived=["title_length", "hotness"])
        assert len(results) == 1
        assert results[0].title_length == 11
        assert results[0].hotness == 11

    def test_relation_with_field_proxy(self, user_post_comment_classes):
        """Relations should work with FieldProxy."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Bob", email="bob@example.com")
        user.save()

        post = post_class(title="Proxy Test", body="Content", user_id=user.id)
        post.save()

        # Query using FieldProxy
        results = post_class.find_all(post_class.c.user_id == user.id)
        assert len(results) == 1
        assert results[0].title == "Proxy Test"

    def test_derived_field_with_field_proxy(self, user_post_comment_classes):
        """Derived fields using FieldProxy should work."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Charlie", email="charlie@example.com")
        user.save()

        post = post_class(title="Derived Proxy", body="Content", user_id=user.id)
        post.save()

        # title_length uses Post.c.title (FieldProxy)
        results = post_class.find_all(derived=["title_length"])
        assert len(results) == 1
        assert results[0].title_length == 13  # len("Derived Proxy")

    def test_eager_load_with_derived(self, user_post_comment_classes):
        """Eager loading should work with derived fields."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Dave", email="dave@example.com")
        user.save()

        post1 = post_class(title="Post 1", body="Content 1", user_id=user.id, view_count=5)
        post1.save()
        post2 = post_class(title="Post 2", body="Content 2", user_id=user.id, view_count=10)
        post2.save()

        # Query with eager loading and derived fields
        results = user_class.find_all(derived=["display_name"])
        assert len(results) == 1
        assert results[0].display_name is not None

    @requires_protocol(JSONSupport, 'supports_json_type')
    def test_eager_load_with_json_derived(self, user_post_comment_classes):
        """Eager loading should work with JSON derived fields."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(
            name="Eve",
            email="eve@example.com",
            settings='{"language": "fr", "theme": "dark"}'
        )
        user.save()

        post = post_class(
            title="French Post",
            body="Content",
            user_id=user.id,
            metadata='{"tags": ["french"], "source": "import"}'
        )
        post.save()

        # Query with JSON derived fields
        results = user_class.find_all(derived=["language", "theme"])
        assert len(results) == 1
        assert results[0].language == "fr"
        assert results[0].theme == "dark"

    @requires_protocol(JSONSupport, 'supports_json_type')
    def test_full_integration(self, user_post_comment_classes):
        """Full integration: relations + derived + proxy + JSON."""
        user_class, post_class, comment_class = user_post_comment_classes
        # Create user with JSON settings
        user = user_class(
            name="Frank",
            email="frank@example.com",
            settings='{"language": "de", "theme": "auto"}'
        )
        user.save()

        # Create post with JSON metadata
        post = post_class(
            title="Full Integration Test",
            body="This is a comprehensive test",
            user_id=user.id,
            view_count=100,
            metadata='{"tags": ["integration", "test"], "source": "ci"}'
        )
        post.save()

        # Create comment with JSON meta
        comment = comment_class(
            body="Excellent integration test!",
            post_id=post.id,
            meta='{"platform": "github", "device": "desktop"}'
        )
        comment.save()

        # Query user with all derived fields
        users = user_class.find_all(derived="all")
        assert len(users) == 1
        assert users[0].display_name is not None
        assert users[0].language == "de"
        assert users[0].theme == "auto"

        # Query post with all derived fields
        posts = post_class.find_all(derived="all")
        assert len(posts) == 1
        assert posts[0].title_length == 21  # len("Full Integration Test")
        assert posts[0].hotness == 101  # 100 + 1
        assert posts[0].first_tag == "integration"
        assert posts[0].source == "ci"

        # Query comment with all derived fields
        comments = comment_class.find_all(derived="all")
        assert len(comments) == 1
        assert comments[0].body_length == 27  # len("Excellent integration test!")
        assert comments[0].platform == "github"
