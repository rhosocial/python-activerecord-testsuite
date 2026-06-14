# src/rhosocial/activerecord/testsuite/feature/relation/test_derived_field_json_async.py
"""
Async tests for JSON derived fields in relation models.

These tests require JSON support from the backend dialect.
"""
import pytest

from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
from rhosocial.activerecord.testsuite.utils import requires_functions, requires_protocol


class TestAsyncJsonDerivedField:
    """Async tests for JSON derived fields (requires JSON support)."""

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_extract_user_language(self, async_user_class):
        """Should extract language from JSON settings."""
        user = async_user_class(
            name="Alice",
            email="alice@example.com",
            settings='{"language": "zh-CN", "theme": "dark"}'
        )
        await user.save()

        results = await async_user_class.find_all(derived=["language"])
        assert len(results) == 1
        assert results[0].language == "zh-CN"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_extract_user_theme(self, async_user_class):
        """Should extract theme from JSON settings."""
        user = async_user_class(
            name="Bob",
            email="bob@example.com",
            settings='{"language": "en", "theme": "light"}'
        )
        await user.save()

        results = await async_user_class.find_all(derived=["theme"])
        assert len(results) == 1
        assert results[0].theme == "light"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_extract_post_first_tag(self, async_post_class, async_user_class):
        """Should extract first tag from JSON metadata."""
        user = async_user_class(name="Charlie", email="charlie@example.com")
        await user.save()

        post = async_post_class(
            title="Test Post",
            body="Content",
            user_id=user.id,
            metadata='{"tags": ["python", "orm", "database"], "source": "blog"}'
        )
        await post.save()

        results = await async_post_class.find_all(derived=["first_tag"])
        assert len(results) == 1
        assert results[0].first_tag == "python"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_extract_post_source(self, async_post_class, async_user_class):
        """Should extract source from JSON metadata."""
        user = async_user_class(name="Dave", email="dave@example.com")
        await user.save()

        post = async_post_class(
            title="Another Post",
            body="Content",
            user_id=user.id,
            metadata='{"tags": ["test"], "source": "newsletter"}'
        )
        await post.save()

        results = await async_post_class.find_all(derived=["source"])
        assert len(results) == 1
        assert results[0].source == "newsletter"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_extract_comment_platform(self, async_comment_class, async_post_class, async_user_class):
        """Should extract platform from JSON meta."""
        user = async_user_class(name="Eve", email="eve@example.com")
        await user.save()

        post = async_post_class(title="Post", body="Content", user_id=user.id)
        await post.save()

        comment = async_comment_class(
            body="Great post!",
            post_id=post.id,
            meta='{"platform": "web", "device": "mobile"}'
        )
        await comment.save()

        results = await async_comment_class.find_all(derived=["platform"])
        assert len(results) == 1
        assert results[0].platform == "web"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_derived_with_relation(self, async_user_class):
        """JSON derived fields should work with relation queries."""
        user = async_user_class(
            name="Frank",
            email="frank@example.com",
            settings='{"language": "ja", "theme": "dark"}'
        )
        await user.save()

        results = await async_user_class.find_all(derived=["language", "theme"])
        assert len(results) == 1
        assert results[0].language == "ja"
        assert results[0].theme == "dark"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    @pytest.mark.asyncio
    async def test_json_derived_all(self, async_user_class):
        """derived='all' should include JSON derived fields."""
        user = async_user_class(
            name="Grace",
            email="grace@example.com",
            settings='{"language": "ko", "theme": "auto"}'
        )
        await user.save()

        results = await async_user_class.find_all(derived="all")
        assert len(results) == 1
        assert results[0].language == "ko"
        assert results[0].theme == "auto"
        assert results[0].display_name is not None
