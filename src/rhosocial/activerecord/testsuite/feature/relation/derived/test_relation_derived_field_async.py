# src/rhosocial/activerecord/testsuite/feature/relation/derived/test_relation_derived_field_async.py
"""
Async tests for derived fields in relation models.
"""

from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
from rhosocial.activerecord.testsuite.utils import requires_functions, requires_protocol


class TestAsyncDerivedFieldBasic:
    """Async tests for basic derived fields."""

    async def test_derived_fields_registered(self, async_user_class):
        """Derived fields should be registered on the model."""
        assert "display_name" in async_user_class.__derived_fields__, \
            "Expected 'display_name' to be a derived field"
        assert "language" in async_user_class.__derived_fields__, \
            "Expected 'language' to be a derived field"
        assert "theme" in async_user_class.__derived_fields__, \
            "Expected 'theme' to be a derived field"

    async def test_post_derived_fields_registered(self, async_post_class):
        """Post derived fields should be registered."""
        assert "title_length" in async_post_class.__derived_fields__, \
            "Expected 'title_length' to be a derived field"
        assert "hotness" in async_post_class.__derived_fields__, \
            "Expected 'hotness' to be a derived field"

    async def test_comment_derived_fields_registered(self, async_comment_class):
        """Comment derived fields should be registered."""
        assert "body_length" in async_comment_class.__derived_fields__, \
            "Expected 'body_length' to be a derived field"
        assert "platform" in async_comment_class.__derived_fields__, \
            "Expected 'platform' to be a derived field"

    async def test_descriptor_class_access(self, async_user_class):
        """Class access should return DerivedField instance."""
        from rhosocial.activerecord.base import DerivedField
        assert isinstance(async_user_class.display_name, DerivedField), \
            "Expected display_name to be a DerivedField instance"

    async def test_descriptor_instance_default_none(self, async_user_class):
        """Instance should have None for derived fields by default."""
        user = async_user_class(name="Test", email="test@example.com")
        assert user.display_name is None, "Expected derived field to be None by default"
        assert user.language is None, "Expected derived field to be None by default"

    async def test_field_proxy_on_post(self, async_post_class):
        """Post should have FieldProxy that provides column access."""
        assert hasattr(async_post_class, 'c'), "Expected post_class to expose a 'c' field accessor"
        assert hasattr(async_post_class.c, 'title'), "Expected 'title' column access"
        assert hasattr(async_post_class.c, 'body'), "Expected 'body' column access"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    async def test_find_all_derived_true(self, async_user_class):
        """derived=True should return all derived fields."""
        user = async_user_class(name="Alice", email="alice@example.com")
        await user.save()

        results = await async_user_class.find_all(derived=True)
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].display_name is not None, "Expected display_name to be computed"

    async def test_find_all_derived_list(self, async_user_class):
        """derived=[field] should return only specified fields."""
        user = async_user_class(name="Bob", email="bob@example.com")
        await user.save()

        results = await async_user_class.find_all(derived=["display_name"])
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].display_name is not None, "Expected display_name to be computed"
        assert results[0].language is None, "Expected unspecified derived field to remain None"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    async def test_find_one_derived(self, async_user_class):
        """find_one with derived should return derived fields."""
        user = async_user_class(name="Charlie", email="charlie@example.com")
        await user.save()

        result = await async_user_class.find_one(user.id, derived=True)
        assert result is not None, "Expected the user record to be found"
        assert result.display_name is not None, "Expected display_name to be computed"

    async def test_find_all_derived_false_default(self, async_user_class):
        """Default (no derived) should not return derived fields."""
        user = async_user_class(name="Dave", email="dave@example.com")
        await user.save()

        results = await async_user_class.find_all()
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].display_name is None, "Expected derived field to be None by default"

    async def test_title_length_derived(self, async_user_post_comment_classes):
        """title_length should compute correctly."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Eve", email="eve@example.com")
        await user.save()

        post = post_class(title="Hello World", body="Content", user_id=user.id)
        await post.save()

        results = await post_class.find_all(derived=["title_length"])
        assert len(results) == 1, "Expected 1 post record to be found"
        assert results[0].title_length == 11, "Expected title_length to be 11"

    async def test_hotness_derived(self, async_user_post_comment_classes):
        """hotness should compute correctly."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Frank", email="frank@example.com")
        await user.save()

        post = post_class(title="Test", body="Content", user_id=user.id, view_count=42)
        await post.save()

        results = await post_class.find_all(derived=["hotness"])
        assert len(results) == 1, "Expected 1 post record to be found"
        assert results[0].hotness == 43, "Expected hotness to be 43"

    async def test_body_length_derived(self, async_user_post_comment_classes):
        """body_length should compute correctly."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Grace", email="grace@example.com")
        await user.save()

        post = post_class(title="Post", body="Content", user_id=user.id)
        await post.save()

        comment = comment_class(body="This is a comment", post_id=post.id)
        await comment.save()

        results = await comment_class.find_all(derived=["body_length"])
        assert len(results) == 1, "Expected 1 comment record to be found"
        assert results[0].body_length == 17, "Expected body_length to be 17"


class TestAsyncDerivedFieldWithProxy:
    """Async tests for derived fields using FieldProxy."""

    async def test_post_title_uses_proxy(self, async_user_post_comment_classes):
        """Post.title_length should use FieldProxy internally."""
        user_class, post_class, comment_class = async_user_post_comment_classes
        user = user_class(name="Hank", email="hank@example.com")
        await user.save()

        post = post_class(title="Proxy Test", body="Content", user_id=user.id)
        await post.save()

        results = await post_class.find_all(derived=["title_length"])
        assert results[0].title_length == 10, "Expected title_length to be 10"


