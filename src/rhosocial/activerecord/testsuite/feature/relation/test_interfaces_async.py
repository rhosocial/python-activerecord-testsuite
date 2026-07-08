# src/rhosocial/activerecord/testsuite/feature/relation/test_interfaces_async.py
"""
Tests for relation interfaces.
"""

import pytest

from rhosocial.activerecord.relation.interfaces import IRelationManagement


class TestAsyncRelationInterfaces:
    """Tests for the relation management interfaces."""

    @pytest.mark.asyncio

    async def test_relation_management_interface(self, employee_class, department_class):
        """Test RelationManagementInterface implementation."""
        # Verify interface implementation
        assert isinstance(employee_class, type)
        assert issubclass(employee_class, IRelationManagement)

        # Test relation registration
        relations = employee_class.get_relations()
        assert "department" in relations

        relation = employee_class.get_relation("department")
        assert relation is not None
        assert relation.foreign_key == "department_id"
        assert relation.inverse_of == "employees"

        # Test query method creation
        assert hasattr(employee_class, "department_query")

    @pytest.mark.asyncio

    async def test_relation_cache_operations(self, employee):
        """Test relation cache management."""
        # Clear specific relation cache
        employee.clear_relation_cache("department")

        # Clear all relation caches
        employee.clear_relation_cache()

    @pytest.mark.asyncio

    async def test_invalid_relation_access(self, employee):
        """Test accessing invalid relations."""
        try:
            employee.clear_relation_cache("invalid_relation")
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unknown relation" in str(e)
