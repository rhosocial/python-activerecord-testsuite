# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_field_column_mapping.py
"""
This test file is dedicated to verifying the functionality of field-to-column
mapping and the use of type adapters in ActiveRecord models.

It covers several scenarios:
1.  **Mapped Models**: Tests models where Python field names are explicitly
    mapped to different database column names using `Annotated` with `UseColumn`.
2.  **Mixed Annotation Models**: Tests models that use a combination of standard
    fields, fields with `UseColumn`, fields with `UseAdapter`, and fields with
    both `UseColumn` and `UseAdapter`. This ensures that all annotation types
    can coexist and function correctly.
3.  **Invalid Cases**: Tests that the framework correctly raises errors when
    models are defined with invalid combinations of annotations.
"""
import pytest
from typing import List, Dict, Optional, Any, Tuple, Type

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.fields import UseColumn, UseAdapter
from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter
# ModelDefinitionError was incorrectly assumed, using standard Python exceptions (TypeError, ValueError).


# Fixtures are defined in conftest.py and are assumed to be available.
# We import them here to make the code more readable and to satisfy linters.
from rhosocial.activerecord.testsuite.feature.basic.conftest import (
    mapped_models_fixtures,
    mixed_models_fixtures
)
class TestMappedModels:
    """
    Tests for models that use UseColumn mapping for attribute-to-column name mapping.
    """

    def test_mapped_user_create_and_find(self, mapped_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Verify that a record can be created and retrieved using mapped field names.
        """
        MappedUser, _, _ = mapped_models_fixtures

        # Create a user using Python attribute names
        user = MappedUser(user_name="test_user", email_address="test@example.com", creation_date="2023-01-01T00:00:00")
        assert user.save()
        assert user.user_id is not None

        # Retrieve the user by the mapped primary key
        found_user = MappedUser.find_one(user.user_id)
        assert found_user is not None
        assert found_user.user_name == "test_user"
        assert found_user.email_address == "test@example.com"
        assert found_user.creation_date is not None

        # Verify that querying by the Python attribute name works
        queried_user = MappedUser.query().where("username = ?", ("test_user",)).one()
        assert queried_user is not None
        assert queried_user.user_id == user.user_id

    def test_mapped_post_and_comment(self, mapped_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test creation and retrieval for multiple related mapped models.
        """
        MappedUser, MappedPost, MappedComment = mapped_models_fixtures

        # Create a MappedUser first to satisfy foreign key constraint
        user = MappedUser(
            user_id=1,
            user_name="test_user",
            email_address="test@example.com",
            created_at="2023-01-01T00:00:00"
        )
        assert user.save()
        
        # Create a post
        post = MappedPost(
            author_id=user.user_id,
            post_title="My Mapped Post",
            post_content="Content here.",
            is_published=True,
            publication_time="2023-01-01T00:00:00"
        )
        assert post.save()
        assert post.post_id is not None

        # Create a comment related to the post
        comment = MappedComment(
            post_id=post.post_id,
            author_id=user.user_id, # Use the ID of the created user
            comment_text="This is a comment.",
            is_approved=True,
            comment_creation_date="2023-01-02T00:00:00"
        )
        assert comment.save()
        assert comment.comment_id is not None

        # Retrieve and verify the post
        found_post = MappedPost.find_one(post.post_id)
        assert found_post is not None
        assert found_post.post_title == "My Mapped Post"
        assert found_post.author_id == 1
        assert found_post.publication_time is not None

        # Retrieve and verify the comment
        found_comment = MappedComment.query().where("post_ref = ?", (post.post_id,)).one()
        assert found_comment is not None
        assert found_comment.comment_text == "This is a comment."
        assert found_comment.author_id == user.user_id
        assert found_comment.comment_creation_date is not None

class TestMixedAnnotationModels:
    """
    Tests for models that use a mix of standard fields, UseColumn, and UseAdapter.
    """

    def test_column_mapping_model_crud(self, mixed_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test CRUD operations for a model with a mix of mapped fields and an adapter.
        """
        ColumnMappingModel, _ = mixed_models_fixtures

        # The 'notes' field is a string, but the adapter converts it to an int for the DB.
        item = ColumnMappingModel(name="test_item", item_count=100, notes="12345")
        assert item.save()
        assert item.item_id is not None

        # Retrieve the item
        found_item = ColumnMappingModel.find_one(item.item_id)
        assert found_item is not None
        assert found_item.name == "test_item"
        assert found_item.item_count == 100
        
        # Verify the adapter correctly converted the int from DB back to a string
        assert found_item.notes == "12345"

        # Test querying by a mapped field
        queried_item = ColumnMappingModel.query().where("item_total = ?", (100,)).one()
        assert queried_item is not None
        assert queried_item.item_id == item.item_id

        # Test updating
        found_item.item_count = 150
        assert found_item.save()

        # Re-fetch and verify
        updated_item = ColumnMappingModel.find_one(item.item_id)
        assert updated_item.item_count == 150

    def test_mixed_annotation_model_crud(self, mixed_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test CRUD for the model with all combinations of annotations.
        """
        _, MixedAnnotationModel = mixed_models_fixtures

        # Create an instance
        # 'tags' is List[str], adapter converts to "tag1,tag2"
        # 'metadata' is Optional[Dict], adapter converts to string, column is 'meta'
        item_data = {
            "name": "Mixed Item",
            "item_id": 1,
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
        }
        item = MixedAnnotationModel(**item_data)
        assert item.save()

        # Retrieve and verify
        found_item = MixedAnnotationModel.query().where("id = ?", (1,)).one()
        assert found_item is not None
        assert found_item.name == "Mixed Item"
        
        # Verify adapter for 'tags'
        assert isinstance(found_item.tags, list)
        assert found_item.tags == ["tag1", "tag2"]
        
        # Verify adapter and column mapping for 'metadata'
        assert isinstance(found_item.metadata, dict)
        assert found_item.metadata == {'key': 'value'}
        
        # Verify default value
        assert found_item.status == "active"
        
        # Test updating a field with an adapter
        found_item.tags = ["tag3", "tag4", "tag5"]
        assert found_item.save()
        
        # Re-fetch and verify update
        updated_item = MixedAnnotationModel.query().where("id = ?", (1,)).one()
        assert updated_item.tags == ["tag3", "tag4", "tag5"]

class TestInvalidCases:
    """
    Tests for invalid model definitions related to field mapping and adapters.
    These tests ensure the framework raises errors at definition time.
    """

    def test_multiple_use_column_raises_error(self):
        """Verify that using multiple UseColumn annotations raises an error."""
        with pytest.raises(TypeError) as excinfo:
            class InvalidModel(ActiveRecord):
                __table_name__ = "invalid"
                # This field has two UseColumn annotations, which is invalid.
                name: Annotated[str, UseColumn("col1"), UseColumn("col2")]

        assert "A field can have at most one UseColumn specified" in str(excinfo.value)

    def test_multiple_use_adapter_raises_error(self):
        """Verify that using multiple UseAdapter annotations raises an error."""
        class DummyAdapter(BaseSQLTypeAdapter):
            def _do_to_database(self, value, **kwargs): return value
            def _do_from_database(self, value, **kwargs): return value

        with pytest.raises(TypeError) as excinfo:
            class InvalidModel(ActiveRecord):
                __table_name__ = "invalid"
                # This field has two UseAdapter annotations, which is invalid.
                data: Annotated[
                    str,
                    UseAdapter(DummyAdapter(), str),
                    UseAdapter(DummyAdapter(), str)
                ]

        assert "A field can have at most one UseAdapter specified" in str(excinfo.value)

    def test_use_column_with_invalid_type_raises_error(self):
        """Verify that UseColumn expects a string argument."""
        with pytest.raises(TypeError) as excinfo:
            class InvalidModel(ActiveRecord):
                __table_name__ = "invalid"
                # UseColumn is given an integer, but it expects a string.
                name: Annotated[str, UseColumn(123)]

        assert "Invalid type for column_name. Expected str, but received type int." in str(excinfo.value)

    def test_use_adapter_with_invalid_adapter_raises_error(self):
        """Verify that UseAdapter expects a valid adapter instance."""
        class NotAnAdapter:
            pass

        with pytest.raises(TypeError) as excinfo:
            class InvalidModel(ActiveRecord):
                __table_name__ = "invalid"
                # UseAdapter is given an object that is not a BaseSQLTypeAdapter.
                data: Annotated[str, UseAdapter(NotAnAdapter(), str)]

        assert "Invalid type for adapter. Expected an instance of SQLTypeAdapter, but received type NotAnAdapter." in str(excinfo.value)

    def test_duplicate_column_name_raises_error(self):
        """Verify that two fields mapping to the same column raises an error."""
        with pytest.raises(ValueError) as excinfo:
            class InvalidModelWithDuplicates(ActiveRecord):
                __table_name__ = "invalid_duplicates"

                field_a: Annotated[str, UseColumn("shared_column")]
                field_b: Annotated[int, UseColumn("shared_column")]

            # The error is raised when the class's MRO is being constructed
            # and metaclass are applied. We explicitly trigger validation
            # to ensure the check is performed.
            InvalidModelWithDuplicates.validate_column_names()

        assert "Duplicate explicit column name 'shared_column' found" in str(excinfo.value)

