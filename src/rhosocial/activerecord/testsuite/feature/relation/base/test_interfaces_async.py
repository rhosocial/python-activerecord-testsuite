# src/rhosocial/activerecord/testsuite/feature/relation/base/test_interfaces_async.py
"""
Tests for relation interfaces.
"""


from rhosocial.activerecord.relation.interfaces import IRelationManagement


class TestAsyncRelationInterfaces:
    """Tests for the relation management interfaces."""


    async def test_relation_management_interface(self, employee_class, department_class):
        """Test RelationManagementInterface implementation."""
        # Verify interface implementation
        assert isinstance(employee_class, type), "Expected employee_class to be a type"
        assert issubclass(employee_class, IRelationManagement), \
            "Expected employee_class to implement IRelationManagement"

        # Test relation registration
        relations = employee_class.get_relations()
        assert "department" in relations, "Expected 'department' to be a registered relation"

        relation = employee_class.get_relation("department")
        assert relation is not None, "Expected 'department' relation to be retrieved"
        assert relation.foreign_key == "department_id", \
            "Expected relation foreign_key to be 'department_id'"
        assert relation.inverse_of == "employees", \
            "Expected relation inverse_of to be 'employees'"

        # Test query method creation
        assert hasattr(employee_class, "department_query"), \
            "Expected department_query attribute to exist"


    async def test_relation_cache_operations(self, employee):
        """Test relation cache management."""
        # Clear specific relation cache
        employee.clear_relation_cache("department")

        # Clear all relation caches
        employee.clear_relation_cache()


    async def test_invalid_relation_access(self, employee):
        """Test accessing invalid relations."""
        try:
            employee.clear_relation_cache("invalid_relation")
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unknown relation" in str(e), "Expected error message to contain 'Unknown relation'"
