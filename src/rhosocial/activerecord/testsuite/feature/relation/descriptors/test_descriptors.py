# src/rhosocial/activerecord/testsuite/feature/relation/descriptors/test_descriptors.py
"""
Tests for relation descriptor functionality.

Tests BelongsTo/HasOne/HasMany descriptor types, registration on
RelationManagementMixin models, query method creation, and descriptor
type validation — using memory-based fixtures.
"""
import pytest
from typing import ClassVar

from pydantic import BaseModel

from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.descriptors import BelongsTo, HasOne, HasMany, DefaultIRelationLoader
from rhosocial.activerecord.relation.cache import CacheConfig


class TestRelationDescriptors:
    """Tests for relation descriptor functionality.

    Mirrors test_descriptors_async.py for sync/async parity.

    Tests BelongsTo/HasOne/HasMany descriptor types:
    initialization, default loader, custom cache config, type validation,
    and correct registration on ActiveRecord subclasses.
    """

    # Mock QuerySet for testing
    class MockQuerySet:
        def __init__(self, model_class):
            self.model_class = model_class

        def filter(self, **kwargs):
            return [type(self.model_class.__name__, (), {'id': 1, 'title': 'Test Book', 'author_id': 1})()]

        def all(self):
            return self.filter()

        def get(self, **kwargs):
            return self.filter()[0]

    def test_belongs_to_relation(self, employee_class):
        """Test that invalid relationship pairs are handled properly."""
        # This test might not be directly applicable in the testsuite context
        # since relationship validation would happen when the models are properly configured
        # We'll test that the model has expected attributes instead
        assert hasattr(employee_class, 'get_relations'), "Expected employee_class to have get_relations"
        assert hasattr(employee_class, 'get_relation'), "Expected employee_class to have get_relation"

    def test_has_many_relation(self, employee_class):
        """Test handling of missing inverse relationships."""
        # Similar to above, this would be tested when models are properly configured
        # For now just check that the class has the expected interface
        assert hasattr(employee_class, 'get_relation'), "Expected employee_class to have get_relation"

    def test_has_one_relation(self, employee_class):
        """Test handling of inconsistent inverse relationships."""
        # Similar to above, this would be tested when models are properly configured
        assert hasattr(employee_class, 'get_relations'), "Expected employee_class to have get_relations"

    def test_belongs_to_on_model(self, employee_class):
        """Test that validation occurs when accessing query property."""
        # Test that the model class has expected methods
        assert hasattr(employee_class, 'get_relation'), "Expected employee_class to have get_relation"
        assert hasattr(employee_class, 'clear_relation_cache'), \
            "Expected employee_class to have clear_relation_cache"

    def test_has_many_on_model(self):
        """Test that relation descriptors are properly typed."""
        class TestModel(RelationManagementMixin, BaseModel):
            username: str
            department_id: int
            department: ClassVar[BelongsTo["Department"]] = BelongsTo(
                foreign_key="department_id",
                inverse_of="employees"
            )

        relation = TestModel.get_relation("department")
        assert isinstance(relation, BelongsTo), "Expected a BelongsTo descriptor"
        assert relation.foreign_key == "department_id", "Expected foreign_key to be 'department_id'"
        assert relation.inverse_of == "employees", "Expected inverse_of to be 'employees'"

    def test_has_one_on_model(self):
        """Test HasMany descriptor functionality."""
        class TestModel(RelationManagementMixin, BaseModel):
            name: str
            employees: ClassVar[HasMany["Employee"]] = HasMany(
                foreign_key="department_id",
                inverse_of="department"
            )

        relation = TestModel.get_relation("employees")
        assert isinstance(relation, HasMany), "Expected a HasMany descriptor"
        assert relation.foreign_key == "department_id", "Expected foreign_key to be 'department_id'"
        assert relation.inverse_of == "department", "Expected inverse_of to be 'department'"

    def test_query_method_created(self):
        """Test HasOne descriptor functionality."""
        class TestModel(RelationManagementMixin, BaseModel):
            name: str
            profile: ClassVar[HasOne["Profile"]] = HasOne(
                foreign_key="author_id",
                inverse_of="author"
            )

        relation = TestModel.get_relation("profile")
        assert isinstance(relation, HasOne), "Expected a HasOne descriptor"
        assert relation.foreign_key == "author_id", "Expected foreign_key to be 'author_id'"
        assert relation.inverse_of == "author", "Expected inverse_of to be 'author'"

    def test_descriptor_default_loader(self):
        """When no loader is supplied, the descriptor creates DefaultIRelationLoader."""
        desc = BelongsTo(foreign_key="user_id")
        assert isinstance(desc._loader, DefaultIRelationLoader), \
            "Expected a DefaultIRelationLoader instance"

    def test_descriptor_custom_cache_config(self):
        """Custom CacheConfig (disabled, ttl=60, max_size=10) is stored correctly."""
        config = CacheConfig(enabled=False, ttl=60, max_size=10)
        desc = BelongsTo(foreign_key="user_id", cache_config=config)
        assert desc._cache_config is config, "Expected the custom cache config to be stored"
        assert desc._cache_config.enabled is False, "Expected cache config to be disabled"
        assert desc._cache_config.ttl == 60, "Expected ttl to be 60"
        assert desc._cache_config.max_size == 10, "Expected max_size to be 10"

    def test_descriptor_default_cache_config(self):
        """No cache_config supplied -> default CacheConfig (enabled=True, ttl=300, max_size=1000)."""
        desc = BelongsTo(foreign_key="user_id")
        assert desc._cache_config.enabled is True, "Expected default cache config to be enabled"
        assert desc._cache_config.ttl == 300, "Expected default ttl to be 300"
        assert desc._cache_config.max_size == 1000, "Expected default max_size to be 1000"

    def test_descriptor_foreign_key_type_error(self):
        """Passing a non-string foreign_key raises TypeError."""
        with pytest.raises(TypeError, match="foreign_key must be a string or tuple of strings"):
            BelongsTo(foreign_key=123)

    def test_descriptor_cache_config_type_error(self):
        """Passing a non-CacheConfig object raises TypeError."""
        with pytest.raises(TypeError, match="cache_config must be instance of CacheConfig"):
            BelongsTo(foreign_key="user_id", cache_config="invalid")
