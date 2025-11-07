# src/rhosocial/activerecord/testsuite/feature/relation/test_base.py
"""
Tests for relation base functionality.
"""
import pytest
from typing import ClassVar, Any, Dict, List

from pydantic import BaseModel

from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.cache import CacheConfig
from rhosocial.activerecord.relation.descriptors import HasOne, HasMany, BelongsTo, RelationDescriptor
from rhosocial.activerecord.relation.interfaces import RelationLoader


class TestRelationDescriptor:
    """Tests for the relation descriptor functionality."""

    class CustomLoader(RelationLoader):
        def load(self, instance):
            return {"id": 1, "name": "Test"}

        def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
            pass

    def test_relation_descriptor_init(self):
        """Test RelationDescriptor initialization."""
        descriptor = RelationDescriptor(
            foreign_key="test_id",
            inverse_of="test",
            loader=self.CustomLoader(),
            cache_config=CacheConfig(enabled=True)
        )

        assert descriptor.foreign_key == "test_id"
        assert descriptor.inverse_of == "test"
        assert descriptor._loader is not None
        # assert descriptor._cache is not None

    def test_relation_descriptor_get_related_model(self, employee_class, department_class):
        """Test getting related model class."""
        relation = employee_class.get_relation("department")
        assert relation is not None

        model = relation.get_related_model(employee_class)
        assert model == department_class

        # Test inverse relationship
        inverse_relation = department_class.get_relation("employees")
        assert inverse_relation is not None

        inverse_model = inverse_relation.get_related_model(department_class)
        assert inverse_model == employee_class

    def test_relation_descriptor_load(self, employee):
        """Test loading relation data."""
        relation = employee.get_relation("department")
        relation._loader = self.CustomLoader()

        # First load (from loader)
        data = relation._load_relation(employee)
        assert data == {"id": 1, "name": "Test"}

        # Second load (from cache)
        data = relation._load_relation(employee)
        assert data == {"id": 1, "name": "Test"}

    # def test_relation_descriptor_query(self):
    #     """Test querying relation data."""
    #     relation = employee_class.get_relation("department")
    #
    #     # Test instance query
    #     employee = employee_class(id=1, name="John", department_id=1)
    #     result = relation.__get__(employee)(filter="test")
    #     assert result == [{"id": 1, "name": "Test"}]
    #
    #     # Test class query
    #     result = employee_class.department_query(filter="test")
    #     assert result == [{"id": 1, "name": "Test"}]

    def test_relation_descriptor_cache_clear(self, employee):
        """Test clearing relation cache."""
        relation = employee.get_relation("department")
        relation._loader = self.CustomLoader()

        # Load data into cache
        data = relation._load_relation(employee)
        assert data == {"id": 1, "name": "Test"}

        # Clear cache
        relation.__delete__(employee)

        # Verify cache is cleared by checking if loader is called again
        data = relation._load_relation(employee)
        assert data == {"id": 1, "name": "Test"}

    def test_relation_registration_validation(self):
        """Test validation during relation registration."""
        # This is a unit test that doesn't require database functionality
        class TestModel(RelationManagementMixin, BaseModel):
            username: str
            department_id: int
            test: ClassVar[HasOne["Other"]] = HasOne(
                foreign_key="test_id",
                inverse_of="inverse"
            )
            test: ClassVar[HasMany["Other"]] = HasMany(
                foreign_key="test_id",
                inverse_of="inverse"
            )

    def test_relation_inheritance(self):
        """Test that derived classes can override relations"""
        class ParentModel(RelationManagementMixin, BaseModel):
            id: int
            test: ClassVar[HasOne["Other"]] = HasOne(
                foreign_key="test_id",
                inverse_of="inverse"
            )

        class ChildModel(ParentModel):
            test: ClassVar[HasMany["Other"]] = HasMany(
                foreign_key="test_id",
                inverse_of="inverse"
            )

        parent_relation = ParentModel.get_relation("test")
        child_relation = ChildModel.get_relation("test")

        # Verify parent relation remains HasOne
        assert isinstance(parent_relation, HasOne)
        assert parent_relation.foreign_key == "test_id"

        # Verify child relation is overridden to HasMany
        assert isinstance(child_relation, HasMany)
        assert child_relation.foreign_key == "test_id"

        # Verify relations are different objects
        assert parent_relation is not child_relation

    def test_forward_reference_resolution(self, author, book):
        """Test resolution of forward references in relationship declarations."""
        # This test uses the already defined models with forward references
        # The fixture definitions handle forward reference resolution
        assert author is not None
        assert book is not None
        # If the fixtures were set up properly, the forward references would be resolved
        # and we can access the relations without error
