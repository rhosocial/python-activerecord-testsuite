# src/rhosocial/activerecord/testsuite/feature/relation/validation/test_path_validation_async.py
"""
Async tests for relational query path validation and error handling.
"""
import pytest

from rhosocial.activerecord.query.relational import (
    InvalidRelationPathError,
    RelationNotFoundError,
)


class TestAsyncInvalidRelationPath:
    """Async tests for invalid relation path validation."""

    async def test_empty_relation_path(self, async_user_class):
        """Empty path should raise InvalidRelationPathError."""
        query = async_user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("")
        assert "cannot be empty" in str(exc_info.value), "Expected error to mention empty path"

    async def test_leading_dot(self, async_user_class):
        """Path with leading dot should raise InvalidRelationPathError."""
        query = async_user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_(".posts")
        assert "cannot start with a dot" in str(exc_info.value), "Expected error to mention leading dot"

    async def test_trailing_dot(self, async_user_class):
        """Path with trailing dot should raise InvalidRelationPathError."""
        query = async_user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("posts.")
        assert "cannot end with a dot" in str(exc_info.value), "Expected error to mention trailing dot"

    async def test_consecutive_dots(self, async_user_class):
        """Path with consecutive dots should raise InvalidRelationPathError."""
        query = async_user_class.query()
        with pytest.raises(InvalidRelationPathError) as exc_info:
            query.with_("posts..comments")
        assert "cannot contain consecutive dots" in str(exc_info.value), "Expected error to mention consecutive dots"

    async def test_multiple_invalid_paths(self, async_user_class):
        """Multiple invalid paths should raise on the first one."""
        query = async_user_class.query()
        with pytest.raises(InvalidRelationPathError):
            query.with_("posts", "")


class TestAsyncRelationPathAnalysis:
    """Async tests for relation path analysis."""

    async def test_analyze_relation_path_valid(self, async_user_class):
        """Valid path should return correct parts and configs."""
        query = async_user_class.query()
        parts, configs = query.analyze_relation_path("posts.comments")
        assert parts == ["posts", "comments"], "Expected two path parts"
        assert configs == ["posts", "posts.comments"], "Expected configs for posts and posts.comments"

    async def test_analyze_relation_path_single(self, async_user_class):
        """Single-level path should return single part."""
        query = async_user_class.query()
        parts, configs = query.analyze_relation_path("posts")
        assert parts == ["posts"], "Expected single path part"
        assert configs == ["posts"], "Expected single config"


class TestAsyncRelationNotFound:
    """Async tests for relation not found errors."""

    async def test_relation_not_found_on_model(self, async_user_class):
        """Non-existent relation should raise RelationNotFoundError."""
        query = async_user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("nonexistent")

    async def test_nested_relation_not_found(self, async_user_class):
        """Non-existent nested relation should raise RelationNotFoundError."""
        query = async_user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("posts.nonexistent")

    async def test_partial_path_valid_full_invalid(self, async_user_class):
        """Partially valid path should raise for invalid part."""
        query = async_user_class.query()
        with pytest.raises(RelationNotFoundError):
            query.with_("posts.comments.nonexistent")
