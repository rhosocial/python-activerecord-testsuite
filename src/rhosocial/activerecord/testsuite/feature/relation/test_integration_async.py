# src/rhosocial/activerecord/testsuite/feature/relation/test_integration_async.py
"""
Async integration tests: relations + derived fields + field proxy + JSON.
"""
import pytest

from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol


class TestAsyncIntegration:
    """Async integration tests for multiple features."""

    @pytest.mark.asyncio
    async def test_relation_with_derived_fields(self, async_user_post_comment_classes):
        """Relations should work with derived fields."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Alice", email="alice@example.com")
        await user.save()

        post = post_class(title="Hello World", body="Content", user_id=user.id, view_count=10)
        await post.save()

        results = await post_class.find_all(derived=["title_length", "hotness"])
        assert len(results) == 1
        assert results[0].title_length == 11
        assert results[0].hotness == 11

    @pytest.mark.asyncio
    async def test_relation_with_field_proxy(self, async_user_post_comment_classes):
        """Relations should work with FieldProxy."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Bob", email="bob@example.com")
        await user.save()

        post = post_class(title="Proxy Test", body="Content", user_id=user.id)
        await post.save()

        results = await post_class.find_all(post_class.c.user_id == user.id)
        assert len(results) == 1
        assert results[0].title == "Proxy Test"

    @pytest.mark.asyncio
    async def test_derived_field_with_field_proxy(self, async_user_post_comment_classes):
        """Derived fields using FieldProxy should work."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Charlie", email="charlie@example.com")
        await user.save()

        post = post_class(title="Derived Proxy", body="Content", user_id=user.id)
        await post.save()

        results = await post_class.find_all(derived=["title_length"])
        assert len(results) == 1
        assert results[0].title_length == 13

    @requires_protocol(JSONSupport, 'supports_json_type')
    @pytest.mark.asyncio
    async def test_eager_load_with_json_derived(self, async_user_post_comment_classes):
        """Eager loading should work with JSON derived fields."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(
            name="Eve",
            email="eve@example.com",
            settings='{"language": "fr", "theme": "dark"}'
        )
        await user.save()

        results = await user_class.find_all(derived=["language", "theme"])
        assert len(results) == 1
        assert results[0].language == "fr"
        assert results[0].theme == "dark"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @pytest.mark.asyncio
    async def test_full_integration(self, async_user_post_comment_classes):
        """Full integration: relations + derived + proxy + JSON."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(
            name="Frank",
            email="frank@example.com",
            settings='{"language": "de", "theme": "auto"}'
        )
        await user.save()

        post = post_class(
            title="Full Integration Test",
            body="This is a comprehensive test",
            user_id=user.id,
            view_count=100,
            metadata='{"tags": ["integration", "test"], "source": "ci"}'
        )
        await post.save()

        comment = comment_class(
            body="Excellent integration test!",
            post_id=post.id,
            meta='{"platform": "github", "device": "desktop"}'
        )
        await comment.save()

        users = await user_class.find_all(derived="all")
        assert len(users) == 1
        assert users[0].display_name is not None
        assert users[0].language == "de"
        assert users[0].theme == "auto"

        posts = await post_class.find_all(derived="all")
        assert len(posts) == 1
        assert posts[0].title_length == 21  # len("Full Integration Test")
        assert posts[0].hotness == 101
        assert posts[0].first_tag == "integration"
        assert posts[0].source == "ci"

        comments = await comment_class.find_all(derived="all")
        assert len(comments) == 1
        assert comments[0].body_length == 27  # len("Excellent integration test!")
        assert comments[0].platform == "github"
