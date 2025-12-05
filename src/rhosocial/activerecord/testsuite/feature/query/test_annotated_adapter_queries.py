# src/rhosocial/activerecord/testsuite/feature/query/test_annotated_adapter_queries.py

import pytest
from typing import Type, Tuple

from rhosocial.activerecord.model import ActiveRecord
from .fixtures.annotated_adapter_models import SearchableItem


@pytest.mark.feature
@pytest.mark.feature_query
class TestAnnotatedAdapterQueries:
    """
    Tests for querying with Annotated type adapters.
    """

    def test_create_and_load_with_adapter(self, annotated_query_fixtures: Tuple[Type[SearchableItem]]):
        """
        Tests creating a record with a list, saving it, and loading it back
        to ensure correct type adaptation.
        """
        SearchableItemModel = annotated_query_fixtures[0]
        item = SearchableItemModel(name="Test Item 1", tags=["tag1", "tag2", "tag3"])
        assert item.save() == 1
        assert item.id is not None

        loaded_item = SearchableItemModel.find_one(item.id)
        assert loaded_item is not None
        assert loaded_item.name == "Test Item 1"
        assert loaded_item.tags == ["tag1", "tag2", "tag3"]

    def test_update_with_adapter(self, annotated_query_fixtures: Tuple[Type[SearchableItem]]):
        """
        Tests updating a record's annotated field and ensuring correct adaptation.
        """
        SearchableItemModel = annotated_query_fixtures[0]
        item = SearchableItemModel(name="Update Me", tags=["old_tag"])
        item.save()
        assert item.id is not None

        item_to_update = SearchableItemModel.find_one(item.id)
        assert item_to_update is not None
        item_to_update.tags = ["new_tag1", "new_tag2"]
        assert item_to_update.save() == 1

        loaded_item = SearchableItemModel.find_one(item.id)
        assert loaded_item is not None
        assert loaded_item.tags == ["new_tag1", "new_tag2"]

    def test_query_by_exact_string(self, annotated_query_fixtures: Tuple[Type[SearchableItem]]):
        """
        Tests querying using the database-native string format.
        """
        SearchableItemModel = annotated_query_fixtures[0]
        item1 = SearchableItemModel(name="Query Item A", tags=["apple", "banana"])
        item1.save()

        # Query using the raw string that the DB stores
        found_item = SearchableItemModel.query().where("tags = ?", ("apple,banana",)).one()
        assert found_item is not None
        assert found_item.id == item1.id
        assert found_item.tags == ["apple", "banana"]

    def test_empty_list_handling(self, annotated_query_fixtures: Tuple[Type[SearchableItem]]):
        """
        Tests handling of empty lists for annotated fields.
        """
        SearchableItemModel = annotated_query_fixtures[0]
        item = SearchableItemModel(name="Empty Tags", tags=[])
        item.save()
        assert item.id is not None

        loaded_item = SearchableItemModel.find_one(item.id)
        assert loaded_item is not None
        assert loaded_item.tags == []

    def test_null_value_handling(self, annotated_query_fixtures: Tuple[Type[SearchableItem]]):
        """
        Tests that setting tags to None saves a NULL to the DB, which then
        loads back as an empty list due to the pydantic validator.
        """
        SearchableItemModel = annotated_query_fixtures[0]
        item = SearchableItemModel(name="DB Null Handled", tags=['initial'])
        item.save()
        assert item.id is not None

        item_to_update = SearchableItemModel.find_one(item.id)
        assert item_to_update is not None
        item_to_update.tags = None
        item_to_update.save()

        reloaded_item = SearchableItemModel.find_one(item.id)
        assert reloaded_item is not None
        assert reloaded_item.tags == []
