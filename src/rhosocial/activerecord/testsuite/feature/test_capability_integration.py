# src/rhosocial/activerecord/testsuite/feature/test_capability_integration.py
"""Integration tests for the capability system."""

import pytest
from rhosocial.activerecord.backend.capabilities import (
    DatabaseCapabilities,
    CapabilityCategory,
    WindowFunctionCapability,
    AdvancedGroupingCapability,
    CTECapability,
    JSONCapability,
    ReturningCapability,
    TransactionCapability,
    BulkOperationCapability,
    ALL_WINDOW_FUNCTIONS,
    ALL_CTE_FEATURES
)

class TestDatabaseCapabilities:
    """Test the DatabaseCapabilities class functionality."""

    def test_initialize_capabilities(self):
        """Test initializing capabilities."""
        capabilities = DatabaseCapabilities()

        # Initially, no capabilities should be supported
        assert not capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)
        assert not capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)

    def test_add_window_functions(self):
        """Test adding window function capabilities."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function(WindowFunctionCapability.ROW_NUMBER)

        # Check specific capability
        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)

        # Check category
        assert capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)

        # Check that other window functions are not supported
        assert not capabilities.supports_window_function(WindowFunctionCapability.RANK)

    def test_add_all_window_functions(self):
        """Test adding all window function capabilities."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function(ALL_WINDOW_FUNCTIONS)

        # Check that all window functions are supported
        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)
        assert capabilities.supports_window_function(WindowFunctionCapability.RANK)
        assert capabilities.supports_window_function(WindowFunctionCapability.LAG)
        assert capabilities.supports_window_function(WindowFunctionCapability.LEAD)

        # Check category
        assert capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)

    def test_add_cte_capabilities(self):
        """Test adding CTE capabilities."""
        capabilities = DatabaseCapabilities()
        capabilities.add_cte(CTECapability.BASIC_CTE)

        # Check specific capability
        assert capabilities.supports_cte(CTECapability.BASIC_CTE)

        # Check category
        assert capabilities.supports_category(CapabilityCategory.CTE)

    def test_add_all_cte_capabilities(self):
        """Test adding all CTE capabilities."""
        capabilities = DatabaseCapabilities()
        capabilities.add_cte(ALL_CTE_FEATURES)

        # Check that all CTE capabilities are supported
        assert capabilities.supports_cte(CTECapability.BASIC_CTE)
        assert capabilities.supports_cte(CTECapability.RECURSIVE_CTE)
        assert capabilities.supports_cte(CTECapability.MATERIALIZED_CTE)

        # Check category
        assert capabilities.supports_category(CapabilityCategory.CTE)

    def test_multiple_categories(self):
        """Test adding capabilities from multiple categories."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function(WindowFunctionCapability.ROW_NUMBER)
        capabilities.add_cte(CTECapability.BASIC_CTE)
        capabilities.add_advanced_grouping(AdvancedGroupingCapability.CUBE)

        # Check all categories
        assert capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)
        assert capabilities.supports_category(CapabilityCategory.CTE)
        assert capabilities.supports_category(CapabilityCategory.ADVANCED_GROUPING)

        # Check specific capabilities
        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)
        assert capabilities.supports_cte(CTECapability.BASIC_CTE)
        assert capabilities.supports_advanced_grouping(AdvancedGroupingCapability.CUBE)

    def test_capability_combination(self):
        """Test combining multiple capabilities of the same type."""
        capabilities = DatabaseCapabilities()
        capabilities.add_window_function([
            WindowFunctionCapability.ROW_NUMBER,
            WindowFunctionCapability.RANK,
            WindowFunctionCapability.LAG
        ])

        # Check that all added capabilities are supported
        assert capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER)
        assert capabilities.supports_window_function(WindowFunctionCapability.RANK)
        assert capabilities.supports_window_function(WindowFunctionCapability.LAG)

        # Check that other capabilities are not supported
        assert not capabilities.supports_window_function(WindowFunctionCapability.LEAD)

        # Check category
        assert capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)

if __name__ == "__main__":
    pytest.main([__file__])
