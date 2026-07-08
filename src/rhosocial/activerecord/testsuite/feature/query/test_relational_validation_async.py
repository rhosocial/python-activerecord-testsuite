# src/rhosocial/activerecord/testsuite/feature/query/test_relational_validation_async.py
"""
Detailed RelationalQueryMixin implementation tests to increase coverage of src/rhosocial/activerecord/query/relational.py

This file contains specific tests for the RelationalQueryMixin class,
testing validation methods and functionality directly to improve code coverage.
"""

import pytest
from unittest.mock import Mock, MagicMock
from rhosocial.activerecord.query.relational import RelationalQueryMixin, InvalidRelationPathError, RelationNotFoundError
from rhosocial.activerecord.interface import IQuery
from rhosocial.activerecord.backend.impl.dummy.backend import DummyBackend


class MockQuery(RelationalQueryMixin):
    """Mock query class to test RelationalQueryMixin methods."""

    def __init__(self, model_class=None):
        # Use dummy backend for testing
        backend = DummyBackend()
        # Call the mixin's init method with the backend
        RelationalQueryMixin.__init__(self, backend=backend)
        self.model_class = model_class
        self._logger = Mock()

    def _log(self, level, message):
        """Mock logging method."""
        self._logger.log(level, message)

    def to_sql(self):
        """Mock to_sql method to satisfy IQuery interface."""
        return ("SELECT * FROM mock", ())

    def where(self, condition):
        """Mock where method to satisfy IQuery interface."""
        return self

    def all(self):
        """Mock all method to satisfy IQuery interface."""
        return []


def create_mock_model_with_relations(relations):
    """Create a mock model with specified relations."""
    mock_model = Mock()
    mock_model.__name__ = "MockModel"

    def get_relation(name):
        if name in relations:
            mock_relation = Mock()
            mock_relation.get_related_model = Mock(return_value=Mock(__name__="RelatedModel"))
            return mock_relation
        return None

    mock_model.get_relation = get_relation
    return mock_model


class TestAsyncRelationalValidation:
    """Synchronous tests for relational validation functionality."""

    @pytest.mark.asyncio

    async def test_validate_relation_path_empty_string(self):
        """Test _validate_relation_path with empty string."""
        query = MockQuery()

        with pytest.raises(InvalidRelationPathError, match="Relation path cannot be empty"):
            query._validate_relation_path("")

    @pytest.mark.asyncio

    async def test_validate_relation_path_leading_dot(self):
        """Test _validate_relation_path with leading dot."""
        query = MockQuery()

        with pytest.raises(InvalidRelationPathError, match="cannot start with a dot"):
            query._validate_relation_path(".posts")

    @pytest.mark.asyncio

    async def test_validate_relation_path_trailing_dot(self):
        """Test _validate_relation_path with trailing dot."""
        query = MockQuery()

        with pytest.raises(InvalidRelationPathError, match="cannot end with a dot"):
            query._validate_relation_path("posts.")

    @pytest.mark.asyncio

    async def test_validate_relation_path_consecutive_dots(self):
        """Test _validate_relation_path with consecutive dots."""
        query = MockQuery()

        with pytest.raises(InvalidRelationPathError, match="cannot contain consecutive dots"):
            query._validate_relation_path("posts..comments")

    @pytest.mark.asyncio

    async def test_validate_relation_path_valid_cases(self):
        """Test _validate_relation_path with valid cases."""
        query = MockQuery()

        # These should not raise any exceptions
        query._validate_relation_path("posts")
        query._validate_relation_path("posts.comments")
        query._validate_relation_path("user.posts.comments")
        query._validate_relation_path("a")
        query._validate_relation_path("valid.path.with.multiple.parts")

    @pytest.mark.asyncio

    async def test_validate_relation_exists_relation_not_found(self):
        """Test _validate_relation_exists when relation does not exist."""
        mock_model = create_mock_model_with_relations(['existing_relation'])
        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'nonexistent_relation' not found on MockModel"):
            query._validate_relation_exists('nonexistent_relation')

    @pytest.mark.asyncio

    async def test_validate_relation_exists_relation_found(self):
        """Test _validate_relation_exists when relation exists."""
        mock_model = create_mock_model_with_relations(['existing_relation'])
        query = MockQuery(mock_model)

        # This should not raise any exception
        query._validate_relation_exists('existing_relation')

    @pytest.mark.asyncio

    async def test_validate_relation_exists_with_custom_model_class(self):
        """Test _validate_relation_exists with custom model class."""
        custom_model = create_mock_model_with_relations(['custom_relation'])
        query = MockQuery()  # Initially no model_class

        # This should not raise any exception
        query._validate_relation_exists('custom_relation', custom_model)

    @pytest.mark.asyncio

    async def test_validate_relation_exists_with_custom_model_class_not_found(self):
        """Test _validate_relation_exists with custom model class when relation not found."""
        custom_model = create_mock_model_with_relations(['some_relation'])
        query = MockQuery()  # Initially no model_class

        with pytest.raises(RelationNotFoundError, match="Relation 'missing_relation' not found on MockModel"):
            query._validate_relation_exists('missing_relation', custom_model)

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_empty_path(self):
        """Test _validate_complete_relation_path with empty path."""
        mock_model = create_mock_model_with_relations([])
        query = MockQuery(mock_model)

        # Empty path should split to [''] which will try to find '' relation
        with pytest.raises(RelationNotFoundError):
            query._validate_complete_relation_path("")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_single_invalid(self):
        """Test _validate_complete_relation_path with single invalid relation."""
        mock_model = create_mock_model_with_relations([])
        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'invalid' not found on MockModel"):
            query._validate_complete_relation_path("invalid")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_single_valid(self):
        """Test _validate_complete_relation_path with single valid relation."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        mock_relation = Mock()
        # Return a mock model instead of None to avoid the error
        mock_relation.get_related_model = Mock(return_value=Mock(__name__="RelatedModel"))
        mock_model.get_relation = Mock(return_value=mock_relation)

        query = MockQuery(mock_model)

        # This should not raise any exception for a valid relation
        query._validate_complete_relation_path("valid_relation")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_nested_invalid_first(self):
        """Test _validate_complete_relation_path with invalid first relation in nested path."""
        mock_model = create_mock_model_with_relations([])  # No relations available
        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'invalid' not found on MockModel"):
            query._validate_complete_relation_path("invalid.valid2")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_nested_invalid_second(self):
        """Test _validate_complete_relation_path with invalid second relation in nested path."""
        # Create a model that has the first relation but not the second
        mock_model = create_mock_model_with_relations(['first_relation'])
        first_relation = Mock()
        first_relation.get_related_model = Mock(return_value=Mock(__name__="SecondModel"))
        mock_model.get_relation = Mock(side_effect=lambda name: first_relation if name == 'first_relation' else None)

        # Create a second model that doesn't have the second relation
        second_model = create_mock_model_with_relations([])  # No relations on second model

        # Override get_relation to return the second model for first relation
        def get_relation_side_effect(name):
            if name == 'first_relation':
                first_relation.get_related_model.return_value = second_model
                return first_relation
            return None

        mock_model.get_relation = Mock(side_effect=get_relation_side_effect)

        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'second_relation' not found on MockModel"):
            query._validate_complete_relation_path("first_relation.second_relation")

    @pytest.mark.asyncio

    async def test_with_method_invalid_paths(self):
        """Test with_ method with various invalid paths that should trigger _validate_relation_path errors."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        # Test with empty string
        with pytest.raises(InvalidRelationPathError, match="Relation path cannot be empty"):
            query.with_("")

    @pytest.mark.asyncio

    async def test_with_method_invalid_paths_leading_dot(self):
        """Test with_ method with leading dot path."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        with pytest.raises(InvalidRelationPathError, match="cannot start with a dot"):
            query.with_(".invalid")

    @pytest.mark.asyncio

    async def test_with_method_invalid_paths_trailing_dot(self):
        """Test with_ method with trailing dot path."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        with pytest.raises(InvalidRelationPathError, match="cannot end with a dot"):
            query.with_("invalid.")

    @pytest.mark.asyncio

    async def test_with_method_invalid_paths_consecutive_dots(self):
        """Test with_ method with consecutive dots path."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        with pytest.raises(InvalidRelationPathError, match="cannot contain consecutive dots"):
            query.with_("invalid..path")

    @pytest.mark.asyncio

    async def test_with_method_relation_not_found(self):
        """Test with_ method with non-existent relation."""
        mock_model = create_mock_model_with_relations([])  # No relations
        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'nonexistent' not found on MockModel"):
            query.with_("nonexistent")

    @pytest.mark.asyncio

    async def test_process_relation_path_validation(self):
        """Test _process_relation_path calls validation methods."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        valid_relation = Mock()
        valid_relation.get_related_model = Mock(return_value=None)
        mock_model.get_relation = Mock(return_value=valid_relation)

        query = MockQuery(mock_model)

        # This should work without errors for a valid path
        query._process_relation_path("valid_relation")

        # Check that the relation was added to eager loads
        assert "valid_relation" in query._eager_loads

    @pytest.mark.asyncio

    async def test_process_relation_path_invalid_format(self):
        """Test _process_relation_path with invalid format."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        with pytest.raises(InvalidRelationPathError, match="cannot start with a dot"):
            query._process_relation_path(".invalid")

    @pytest.mark.asyncio

    async def test_update_existing_relation_config(self):
        """Test _update_existing_relation_config method."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        # First add a relation config
        query._add_relation_config('test_relation', ['nested'], lambda q: q.where(True))

        # Then update it with a different modifier
        query._update_existing_relation_config('test_relation', ['nested', 'more_nested'],
                                              lambda q: q, True)

        # Check that the config was updated
        config = query._eager_loads['test_relation']
        assert 'more_nested' in config.nested
        assert config.query_modifier is not None

    @pytest.mark.asyncio

    async def test_update_existing_relation_config_with_lambda(self):
        """Test _update_existing_relation_config with lambda modifier overwrite warning."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        # First add a relation config with a lambda
        first_lambda = lambda x: x.where(True)
        query._add_relation_config('test_relation', ['nested'], first_lambda)

        # Then update it with another lambda - this should trigger the warning
        second_lambda = lambda q: q
        query._update_existing_relation_config('test_relation', ['nested', 'more_nested'],
                                              second_lambda, True)

        # Check that the config was updated
        config = query._eager_loads['test_relation']
        assert 'more_nested' in config.nested

    @pytest.mark.asyncio

    async def test_add_relation_config(self):
        """Test _add_relation_config method."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        query = MockQuery(mock_model)

        query._add_relation_config('new_relation', ['nested'], lambda q: q)

        assert 'new_relation' in query._eager_loads
        config = query._eager_loads['new_relation']
        assert config.name == 'new_relation'
        assert 'nested' in config.nested
        assert config.query_modifier is not None

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_get_related_model_returns_none(self):
        """Test _validate_complete_relation_path when get_related_model returns None."""
        mock_model = create_mock_model_with_relations(['first'])
        first_relation = Mock()
        first_relation.get_related_model = Mock(return_value=None)  # Returns None
        mock_model.get_relation = Mock(return_value=first_relation)

        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Could not determine related model for relation 'first'"):
            query._validate_complete_relation_path("first.second")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_get_relation_returns_none_middle_of_path(self):
        """Test _validate_complete_relation_path when get_relation returns falsy after initial check."""
        mock_model = create_mock_model_with_relations(['first'])
        
        # First check returns truthy (passes initial validation)
        # Second call returns None (triggers the else branch at line 288-291)
        mock_model.get_relation = Mock(side_effect=[
            Mock(),  # First call for validation - returns truthy
            None,    # Second call for tracking - returns None
        ])

        query = MockQuery(mock_model)

        # Since there's no second relation 'second', it should fail on the model tracking
        with pytest.raises(RelationNotFoundError, match="Relation 'first' not found"):
            query._validate_complete_relation_path("first.second")

    @pytest.mark.asyncio

    async def test_validate_complete_relation_path_exception_during_tracking(self):
        """Test _validate_complete_relation_path when exception is raised during model tracking."""
        mock_model = create_mock_model_with_relations(['first'])
        first_relation = Mock()
        first_relation.get_related_model = Mock(side_effect=RuntimeError("Test error"))

        mock_model.get_relation = Mock(return_value=first_relation)

        query = MockQuery(mock_model)

        with pytest.raises(RuntimeError, match="Test error"):
            query._validate_complete_relation_path("first.second")


class TestAsyncRefactoredHelperMethods:
    """Tests for refactored helper methods that reduce cognitive complexity."""

    @pytest.mark.asyncio

    async def test_parse_relation_arg_string(self):
        """Test _parse_relation_arg with string input."""
        query = MockQuery()
        path, modifier = query._parse_relation_arg("posts")
        assert path == "posts"
        assert modifier is None

    @pytest.mark.asyncio

    async def test_parse_relation_arg_tuple(self):
        """Test _parse_relation_arg with tuple input."""
        query = MockQuery()
        test_modifier = lambda q: q.where(True)
        path, modifier = query._parse_relation_arg(("posts", test_modifier))
        assert path == "posts"
        assert modifier == test_modifier

    @pytest.mark.asyncio

    async def test_validate_relation_calls_both_validations(self):
        """Test _validate_relation calls both path and existence validation."""
        mock_model = create_mock_model_with_relations(['valid_relation'])
        mock_relation = Mock()
        mock_relation.get_related_model = Mock(return_value=Mock(__name__="RelatedModel"))
        mock_model.get_relation = Mock(return_value=mock_relation)
        query = MockQuery(mock_model)

        # Should not raise any exception for valid relation
        query._validate_relation("valid_relation")

    @pytest.mark.asyncio

    async def test_validate_relation_propagates_path_error(self):
        """Test _validate_relation propagates InvalidRelationPathError."""
        query = MockQuery()

        with pytest.raises(InvalidRelationPathError, match="cannot start with a dot"):
            query._validate_relation(".invalid")

    @pytest.mark.asyncio

    async def test_validate_relation_propagates_not_found_error(self):
        """Test _validate_relation propagates RelationNotFoundError."""
        mock_model = create_mock_model_with_relations([])
        query = MockQuery(mock_model)

        with pytest.raises(RelationNotFoundError, match="Relation 'nonexistent' not found"):
            query._validate_relation("nonexistent")

    @pytest.mark.asyncio

    async def test_get_next_level_parts_with_remaining(self):
        """Test _get_next_level_parts when there are remaining parts."""
        query = MockQuery()
        parts = ["user", "posts", "comments"]

        # At index 0, next level should be ["posts"]
        result = query._get_next_level_parts(parts, 0)
        assert result == ["posts"]

        # At index 1, next level should be ["comments"]
        result = query._get_next_level_parts(parts, 1)
        assert result == ["comments"]

    @pytest.mark.asyncio

    async def test_get_next_level_parts_at_end(self):
        """Test _get_next_level_parts when at the last element."""
        query = MockQuery()
        parts = ["user", "posts"]

        # At last index, next level should be empty
        result = query._get_next_level_parts(parts, 1)
        assert result == []

    @pytest.mark.asyncio

    async def test_get_next_level_parts_single_element(self):
        """Test _get_next_level_parts with single element path."""
        query = MockQuery()
        parts = ["user"]

        result = query._get_next_level_parts(parts, 0)
        assert result == []

    @pytest.mark.asyncio

    async def test_should_update_nested_relation_with_new_nested(self):
        """Test _should_update_nested_relation returns True when adding new nested."""
        mock_model = create_mock_model_with_relations(['user'])
        query = MockQuery(mock_model)

        # Add initial config without the nested relation
        query._add_relation_config('user', [], None)

        # Should return True because 'posts' is not in nested
        result = query._should_update_nested_relation('user', ['posts'])
        assert result is True

    @pytest.mark.asyncio

    async def test_should_update_nested_relation_already_exists(self):
        """Test _should_update_nested_relation returns False when nested already exists."""
        mock_model = create_mock_model_with_relations(['user'])
        query = MockQuery(mock_model)

        # Add initial config with 'posts' already in nested
        query._add_relation_config('user', ['posts'], None)

        # Should return False because 'posts' is already in nested
        result = query._should_update_nested_relation('user', ['posts'])
        assert result is False

    @pytest.mark.asyncio

    async def test_should_update_nested_relation_empty_next_level(self):
        """Test _should_update_nested_relation returns False when next_level is empty."""
        mock_model = create_mock_model_with_relations(['user'])
        query = MockQuery(mock_model)

        query._add_relation_config('user', [], None)

        # Should return False because next_level is empty
        result = query._should_update_nested_relation('user', [])
        assert result is False

    @pytest.mark.asyncio

    async def test_determine_modifier_target_relation(self):
        """Test _determine_modifier returns modifier for target relation."""
        query = MockQuery()
        test_modifier = lambda q: q.where(True)

        result = query._determine_modifier(
            is_target=True,
            is_adding_new_nested=False,
            query_modifier=test_modifier
        )
        assert result == test_modifier

    @pytest.mark.asyncio

    async def test_determine_modifier_adding_new_nested(self):
        """Test _determine_modifier returns modifier when adding new nested."""
        query = MockQuery()
        test_modifier = lambda q: q.where(True)

        result = query._determine_modifier(
            is_target=False,
            is_adding_new_nested=True,
            query_modifier=test_modifier
        )
        assert result == test_modifier

    @pytest.mark.asyncio

    async def test_determine_modifier_neither_condition(self):
        """Test _determine_modifier returns None when neither condition is met."""
        query = MockQuery()
        test_modifier = lambda q: q.where(True)

        result = query._determine_modifier(
            is_target=False,
            is_adding_new_nested=False,
            query_modifier=test_modifier
        )
        assert result is None

    @pytest.mark.asyncio

    async def test_determine_modifier_target_takes_precedence(self):
        """Test _determine_modifier with both conditions True (target takes precedence logically)."""
        query = MockQuery()
        test_modifier = lambda q: q.where(True)

        # Both conditions true - should return modifier (target check is first)
        result = query._determine_modifier(
            is_target=True,
            is_adding_new_nested=True,
            query_modifier=test_modifier
        )
        assert result == test_modifier

    @pytest.mark.asyncio

    async def test_with_method_uses_parse_relation_arg(self):
        """Test with_ method uses _parse_relation_arg helper."""
        mock_model = create_mock_model_with_relations(['posts'])
        mock_relation = Mock()
        mock_relation.get_related_model = Mock(return_value=None)
        mock_model.get_relation = Mock(return_value=mock_relation)
        query = MockQuery(mock_model)

        test_modifier = lambda q: q.where(True)
        query.with_(('posts', test_modifier))

        # Verify the modifier was applied
        assert 'posts' in query._eager_loads
        config = query._eager_loads['posts']
        assert config.query_modifier == test_modifier

    @pytest.mark.asyncio

    async def test_with_method_multiple_relations(self):
        """Test with_ method with multiple relations."""
        mock_model = create_mock_model_with_relations(['posts', 'comments'])
        mock_relation = Mock()
        mock_relation.get_related_model = Mock(return_value=None)
        mock_model.get_relation = Mock(return_value=mock_relation)
        query = MockQuery(mock_model)

        query.with_('posts', 'comments')

        assert 'posts' in query._eager_loads
        assert 'comments' in query._eager_loads