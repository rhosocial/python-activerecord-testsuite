# src/rhosocial/activerecord/testsuite/feature/basic/test_field_column_mapping_async.py
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
class TestAsyncMappedModels:
    """
    Async version of TestMappedModels to ensure sync/async parity.
    """

    async def test_mapped_user_create_and_find(self, async_mapped_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Verify that a record can be created and retrieved using mapped field names asynchronously.
        """
        AsyncMappedUser, _, _ = async_mapped_models_fixtures

        # Create a user using Python attribute names
        user = AsyncMappedUser(user_name="test_user", email_address="test@example.com", creation_date="2023-01-01T00:00:00")
        assert await user.save()
        assert user.user_id is not None

        # Retrieve the user by the mapped primary key
        found_user = await AsyncMappedUser.find_one(user.user_id)
        assert found_user is not None
        assert found_user.user_name == "test_user"
        assert found_user.email_address == "test@example.com"
        assert found_user.creation_date is not None

        # Verify that querying by the Python attribute name works
        queried_user = await AsyncMappedUser.query().where("username = ?", ("test_user",)).one()
        assert queried_user is not None
        assert queried_user.user_id == user.user_id

    async def test_mapped_post_and_comment(self, async_mapped_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test creation and retrieval for multiple related mapped models asynchronously.
        """
        AsyncMappedUser, AsyncMappedPost, AsyncMappedComment = async_mapped_models_fixtures

        # Create a AsyncMappedUser first to satisfy foreign key constraint
        user = AsyncMappedUser(
            user_id=1,
            user_name="test_user",
            email_address="test@example.com",
            created_at="2023-01-01T00:00:00"
        )
        assert await user.save()

        # Create a post
        post = AsyncMappedPost(
            author_id=user.user_id,
            post_title="My Mapped Post",
            post_content="Content here.",
            is_published=True,
            publication_time="2023-01-01T00:00:00"
        )
        assert await post.save()
        assert post.post_id is not None

        # Create a comment related to the post
        comment = AsyncMappedComment(
            post_id=post.post_id,
            author_id=user.user_id, # Use the ID of the created user
            comment_text="This is a comment.",
            is_approved=True,
            comment_creation_date="2023-01-02T00:00:00"
        )
        assert await comment.save()
        assert comment.comment_id is not None

        # Retrieve and verify the post
        found_post = await AsyncMappedPost.find_one(post.post_id)
        assert found_post is not None
        assert found_post.post_title == "My Mapped Post"
        assert found_post.author_id == 1
        assert found_post.publication_time is not None

        # Retrieve and verify the comment
        found_comment = await AsyncMappedComment.query().where("post_ref = ?", (post.post_id,)).one()
        assert found_comment is not None
        assert found_comment.comment_text == "This is a comment."
        assert found_comment.author_id == user.user_id
        assert found_comment.comment_creation_date is not None

class TestAsyncMixedAnnotationModels:
    """
    Async version of TestMixedAnnotationModels to ensure sync/async parity.
    """

    async def test_column_mapping_model_crud(self, async_mixed_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test CRUD operations for a model with a mix of mapped fields and an adapter asynchronously.
        """
        AsyncColumnMappingModel, _ = async_mixed_models_fixtures

        # The 'notes' field is a string, but the adapter converts it to an int for the DB.
        item = AsyncColumnMappingModel(name="test_item", item_count=100, notes="12345")
        assert await item.save()
        assert item.item_id is not None

        # Retrieve the item
        found_item = await AsyncColumnMappingModel.find_one(item.item_id)
        assert found_item is not None
        assert found_item.name == "test_item"
        assert found_item.item_count == 100

        # Verify the adapter correctly converted the int from DB back to a string
        assert found_item.notes == "12345"

        # Test querying by a mapped field
        queried_item = await AsyncColumnMappingModel.query().where("item_total = ?", (100,)).one()
        assert queried_item is not None
        assert queried_item.item_id == item.item_id

        # Test updating
        found_item.item_count = 150
        assert await found_item.save()

        # Re-fetch and verify
        updated_item = await AsyncColumnMappingModel.find_one(item.item_id)
        assert updated_item.item_count == 150

    async def test_mixed_annotation_model_crud(self, async_mixed_models_fixtures: Tuple[Type[ActiveRecord], ...]):
        """
        Test CRUD for the model with all combinations of annotations asynchronously.
        """
        _, AsyncMixedAnnotationModel = async_mixed_models_fixtures

        # Create an instance
        # 'tags' is List[str], adapter converts to "tag1,tag2"
        # 'metadata' is Optional[Dict], adapter converts to string, column is 'meta'
        item_data = {
            "name": "Mixed Item",
            "item_id": 1,
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
        }
        item = AsyncMixedAnnotationModel(**item_data)
        assert await item.save()

        # Retrieve and verify
        found_item = await AsyncMixedAnnotationModel.query().where("id = ?", (1,)).one()
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
        assert await found_item.save()

        # Re-fetch and verify update
        updated_item = await AsyncMixedAnnotationModel.query().where("id = ?", (1,)).one()
        assert updated_item.tags == ["tag3", "tag4", "tag5"]

class TestAsyncInvalidCases:
    """
    Tests for invalid async model definitions related to field mapping and adapters.
    These tests ensure the framework raises errors at definition time.
    """

    async def test_multiple_use_column_raises_error(self):
        """Verify that using multiple UseColumn annotations raises an error for async models."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        with pytest.raises(TypeError) as excinfo:
            class AsyncInvalidModel(AsyncActiveRecord):
                __table_name__ = "invalid"
                name: Annotated[str, UseColumn("col1"), UseColumn("col2")]

        assert "A field can have at most one UseColumn specified" in str(excinfo.value)

    async def test_multiple_use_adapter_raises_error(self):
        """Verify that using multiple UseAdapter annotations raises an error for async models."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        class DummyAdapter(BaseSQLTypeAdapter):
            def _do_to_database(self, value, **kwargs): return value
            def _do_from_database(self, value, **kwargs): return value

        with pytest.raises(TypeError) as excinfo:
            class AsyncInvalidModel(AsyncActiveRecord):
                __table_name__ = "invalid"
                data: Annotated[
                    str,
                    UseAdapter(DummyAdapter(), str),
                    UseAdapter(DummyAdapter(), str)
                ]

        assert "A field can have at most one UseAdapter specified" in str(excinfo.value)

    async def test_use_column_with_invalid_type_raises_error(self):
        """Verify that UseColumn expects a string argument for async models."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        with pytest.raises(TypeError) as excinfo:
            class AsyncInvalidModel(AsyncActiveRecord):
                __table_name__ = "invalid"
                name: Annotated[str, UseColumn(123)]

        assert "Invalid type for column_name. Expected str, but received type int." in str(excinfo.value)

    async def test_use_adapter_with_invalid_adapter_raises_error(self):
        """Verify that UseAdapter expects a valid adapter instance for async models."""
        from rhosocial.activerecord.model import AsyncActiveRecord
        class NotAnAdapter:
            pass

        with pytest.raises(TypeError) as excinfo:
            class AsyncInvalidModel(AsyncActiveRecord):
                __table_name__ = "invalid"
                data: Annotated[str, UseAdapter(NotAnAdapter(), str)]

        assert "Invalid type for adapter. Expected an instance of SQLTypeAdapter, but received type NotAnAdapter." in str(excinfo.value)

    async def test_duplicate_column_name_raises_error(self):
        """Verify that two fields mapping to the same column raises an error for async models."""
        from rhosocial.activerecord.model import AsyncActiveRecord

        with pytest.raises(ValueError) as excinfo:
            class AsyncInvalidModelWithDuplicates(AsyncActiveRecord):
                __table_name__ = "invalid_duplicates"

                field_a: Annotated[str, UseColumn("shared_column")]
                field_b: Annotated[int, UseColumn("shared_column")]

            AsyncInvalidModelWithDuplicates.validate_column_names()

        assert "Duplicate explicit column name 'shared_column' found" in str(excinfo.value)


