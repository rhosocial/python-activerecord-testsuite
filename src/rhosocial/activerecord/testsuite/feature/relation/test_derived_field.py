# src/rhosocial/activerecord/testsuite/feature/relation/test_derived_field.py
"""
Tests for derived fields in relation models.
"""
import pytest


class TestDerivedFieldBasic:
    """Tests for basic derived fields (no JSON dependency)."""

    def test_derived_fields_registered(self, user_class):
        """Derived fields should be registered on the model."""
        assert "display_name" in user_class.__derived_fields__
        assert "language" in user_class.__derived_fields__
        assert "theme" in user_class.__derived_fields__

    def test_post_derived_fields_registered(self, post_class):
        """Post derived fields should be registered."""
        assert "title_length" in post_class.__derived_fields__
        assert "hotness" in post_class.__derived_fields__
        assert "first_tag" in post_class.__derived_fields__
        assert "source" in post_class.__derived_fields__

    def test_comment_derived_fields_registered(self, comment_class):
        """Comment derived fields should be registered."""
        assert "body_length" in comment_class.__derived_fields__
        assert "platform" in comment_class.__derived_fields__

    def test_descriptor_class_access(self, user_class):
        """Class access should return DerivedField instance."""
        from rhosocial.activerecord.base import DerivedField
        assert isinstance(user_class.display_name, DerivedField)

    def test_descriptor_instance_default_none(self, user_class):
        """Instance should have None for derived fields by default."""
        user = user_class(name="Test", email="test@example.com")
        assert user.display_name is None
        assert user.language is None

    def test_field_proxy_on_post(self, post_class):
        """Post should have FieldProxy that provides column access."""
        # Post.c returns a _FieldAccessor that provides type-safe column access
        assert hasattr(post_class, 'c')
        assert hasattr(post_class.c, 'title')
        assert hasattr(post_class.c, 'body')

    def test_find_all_derived_true(self, user_class):
        """derived=True should return all derived fields."""
        user = user_class(name="Alice", email="alice@example.com")
        user.save()

        results = user_class.find_all(derived=True)
        assert len(results) == 1
        # display_name should be computed
        assert results[0].display_name is not None

    def test_find_all_derived_list(self, user_class):
        """derived=[field] should return only specified fields."""
        user = user_class(name="Bob", email="bob@example.com")
        user.save()

        results = user_class.find_all(derived=["display_name"])
        assert len(results) == 1
        assert results[0].display_name is not None
        assert results[0].language is None

    def test_find_one_derived(self, user_class):
        """find_one with derived should return derived fields."""
        user = user_class(name="Charlie", email="charlie@example.com")
        user.save()

        result = user_class.find_one(user.id, derived=True)
        assert result is not None
        assert result.display_name is not None

    def test_find_all_derived_false_default(self, user_class):
        """Default (no derived) should not return derived fields."""
        user = user_class(name="Dave", email="dave@example.com")
        user.save()

        results = user_class.find_all()
        assert len(results) == 1
        assert results[0].display_name is None

    def test_title_length_derived(self, user_post_comment_classes):
        """title_length should compute correctly."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Eve", email="eve@example.com")
        user.save()

        post = post_class(title="Hello World", body="Content", user_id=user.id)
        post.save()

        results = post_class.find_all(derived=["title_length"])
        assert len(results) == 1
        assert results[0].title_length == 11  # len("Hello World")

    def test_hotness_derived(self, user_post_comment_classes):
        """hotness should compute correctly."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Frank", email="frank@example.com")
        user.save()

        post = post_class(title="Test", body="Content", user_id=user.id, view_count=42)
        post.save()

        results = post_class.find_all(derived=["hotness"])
        assert len(results) == 1
        assert results[0].hotness == 43  # 42 + 1

    def test_body_length_derived(self, user_post_comment_classes):
        """body_length should compute correctly."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Grace", email="grace@example.com")
        user.save()

        post = post_class(title="Post", body="Content", user_id=user.id)
        post.save()

        comment = comment_class(body="This is a comment", post_id=post.id)
        comment.save()

        results = comment_class.find_all(derived=["body_length"])
        assert len(results) == 1
        assert results[0].body_length == 17  # len("This is a comment")


class TestDerivedFieldWithProxy:
    """Tests for derived fields using FieldProxy."""

    def test_post_title_uses_proxy(self, user_post_comment_classes):
        """Post.title_length should use FieldProxy internally."""
        user_class, post_class, comment_class = user_post_comment_classes
        user = user_class(name="Hank", email="hank@example.com")
        user.save()

        post = post_class(title="Proxy Test", body="Content", user_id=user.id)
        post.save()

        results = post_class.find_all(derived=["title_length"])
        assert results[0].title_length == 10  # len("Proxy Test")
