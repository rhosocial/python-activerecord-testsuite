# src/rhosocial/activerecord/testsuite/feature/relation/validation/test_path_validation.py
"""
Tests for relational query path validation and error handling.
"""
import pytest

from rhosocial.activerecord.query.relational import (
    InvalidRelationPathError,
    RelationNotFoundError,
)


class TestInvalidRelationPath:
    """Tests for invalid relation path validation."""

    def test_empty_relation_path(self, user_class):
        """Empty path should raise InvalidRelationPathError."""
        query = user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("")
        assert "cannot be empty" in str(exc_info.value)

    def test_leading_dot(self, user_class):
        """Path with leading dot should raise InvalidRelationPathError."""
        query = user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_(".posts")
        assert "cannot start with a dot" in str(exc_info.value)

    def test_trailing_dot(self, user_class):
        """Path with trailing dot should raise InvalidRelationPathError."""
        query = user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("posts.")
        assert "cannot end with a dot" in str(exc_info.value)

    def test_consecutive_dots(self, user_class):
        """Path with consecutive dots should raise InvalidRelationPathError."""
        query = user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("posts..comments")
        assert "cannot contain consecutive dots" in str(exc_info.value)

    def test_multiple_invalid_paths(self, user_class):
        """Multiple invalid paths should raise on the first one."""
        query = user_class.query()
        with pytest.raises(InvalidRelationPathError):
            query.with_("posts", "")


class TestRelationPathAnalysis:
    """Tests for relation path analysis."""

    def test_analyze_relation_path_valid(self, user_class):
        """Valid path should return correct parts and configs."""
        query = user_class.query()
        parts, configs = query.analyze_relation_path("posts.comments")
        assert parts == ["posts", "comments"]
        assert configs == ["posts", "posts.comments"]

    def test_analyze_relation_path_single(self, user_class):
        """Single-level path should return single part."""
        query = user_class.query()
        parts, configs = query.analyze_relation_path("posts")
        assert parts == ["posts"]
        assert configs == ["posts"]


class TestRelationNotFound:
    """Tests for relation not found errors."""

    def test_relation_not_found_on_model(self, user_class):
        """Non-existent relation should raise RelationNotFoundError."""
        query = user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("nonexistent")

    def test_nested_relation_not_found(self, user_class):
        """Non-existent nested relation should raise RelationNotFoundError."""
        query = user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("posts.nonexistent")

    def test_partial_path_valid_full_invalid(self, user_class):
        """Partially valid path should raise for invalid part."""
        query = user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("posts.comments.nonexistent")
