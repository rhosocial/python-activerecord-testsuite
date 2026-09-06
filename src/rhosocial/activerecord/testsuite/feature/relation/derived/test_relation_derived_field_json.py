# src/rhosocial/activerecord/testsuite/feature/relation/derived/test_relation_derived_field_json.py
"""
Tests for JSON derived fields in relation models.

These tests require JSON support from the backend dialect.
"""
import pytest

from rhosocial.activerecord.backend.dialect.protocols import JSONSupport
from rhosocial.activerecord.testsuite.utils import requires_functions, requires_protocol


class TestJsonDerivedField:
    """Tests for JSON derived fields (requires JSON support)."""

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_extract_user_language(self, user_class):
        """Should extract language from JSON settings."""
        user = user_class(
            name="Alice",
            email="alice@example.com",
            settings='{"language": "zh-CN", "theme": "dark"}'
        )
        user.save()

        results = user_class.find_all(derived=["language"])
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].language == "zh-CN", "Expected language to be 'zh-CN'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_extract_user_theme(self, user_class):
        """Should extract theme from JSON settings."""
        user = user_class(
            name="Bob",
            email="bob@example.com",
            settings='{"language": "en", "theme": "light"}'
        )
        user.save()

        results = user_class.find_all(derived=["theme"])
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].theme == "light", "Expected theme to be 'light'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_extract_post_first_tag(self, user_post_comment_classes):
        """Should extract first tag from JSON metadata."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Charlie", email="charlie@example.com")
        user.save()

        post = post_class(
            title="Test Post",
            body="Content",
            user_id=user.id,
            metadata='{"tags": ["python", "orm", "database"], "source": "blog"}'
        )
        post.save()

        results = post_class.find_all(derived=["first_tag"])
        assert len(results) == 1, "Expected 1 post record to be found"
        assert results[0].first_tag == "python", "Expected first_tag to be 'python'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_extract_post_source(self, user_post_comment_classes):
        """Should extract source from JSON metadata."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Dave", email="dave@example.com")
        user.save()

        post = post_class(
            title="Another Post",
            body="Content",
            user_id=user.id,
            metadata='{"tags": ["test"], "source": "newsletter"}'
        )
        post.save()

        results = post_class.find_all(derived=["source"])
        assert len(results) == 1, "Expected 1 post record to be found"
        assert results[0].source == "newsletter", "Expected source to be 'newsletter'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_extract_comment_platform(self, user_post_comment_classes):
        """Should extract platform from JSON meta."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Eve", email="eve@example.com")
        user.save()

        post = post_class(title="Post", body="Content", user_id=user.id)
        post.save()

        comment = comment_class(
            body="Great post!",
            post_id=post.id,
            meta='{"platform": "web", "device": "mobile"}'
        )
        comment.save()

        results = comment_class.find_all(derived=["platform"])
        assert len(results) == 1, "Expected 1 comment record to be found"
        assert results[0].platform == "web", "Expected platform to be 'web'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_derived_with_relation(self, user_class):
        """JSON derived fields should work with relation queries."""
        user = user_class(
            name="Frank",
            email="frank@example.com",
            settings='{"language": "ja", "theme": "dark"}'
        )
        user.save()

        # Query with derived fields
        results = user_class.find_all(derived=["language", "theme"])
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].language == "ja", "Expected language to be 'ja'"
        assert results[0].theme == "dark", "Expected theme to be 'dark'"

    @requires_protocol(JSONSupport, 'supports_json_type')
    @requires_functions('json_extract_text')
    def test_json_derived_all(self, user_class):
        """derived='all' should include JSON derived fields."""
        user = user_class(
            name="Grace",
            email="grace@example.com",
            settings='{"language": "ko", "theme": "auto"}'
        )
        user.save()

        results = user_class.find_all(derived="all")
        assert len(results) == 1, "Expected 1 user record to be found"
        assert results[0].language == "ko", "Expected language to be 'ko'"
        assert results[0].theme == "auto", "Expected theme to be 'auto'"
        assert results[0].display_name is not None, "Expected display_name to be computed"
