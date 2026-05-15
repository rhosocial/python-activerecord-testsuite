# src/rhosocial/activerecord/testsuite/feature/examples/capability_usage_example.py
"""
Example showing how to use the protocol-based requirement system in tests.

This module demonstrates how to use requires_protocol and requires_functions
decorators to mark tests that require specific database capabilities.
"""

import pytest
from rhosocial.activerecord.testsuite.utils import (
    requires_protocol,
    requires_window_functions,
    requires_cube,
    requires_cte,
    requires_json_operations,
    requires_returning_clause,
    requires_functions,
)


# Example 1: Using requires_protocol with protocol class
@requires_protocol(WindowFunctionSupport, 'supports_window_functions')
def test_window_functions_protocol():
    """Test window functions using requires_protocol."""
    # This test will be automatically skipped if the backend
    # doesn't support window functions
    assert True


# Example 2: Using convenience decorators (recommended)
@requires_window_functions()
def test_window_functions_convenience():
    """Test window functions using convenience decorator."""
    # This test will be automatically skipped if the backend
    # doesn't support any window functions
    assert True


@requires_cube()
def test_cube_grouping():
    """Test CUBE grouping using convenience decorator."""
    # This test will be automatically skipped if the backend
    # doesn't support CUBE grouping
    assert True


@requires_cte()
def test_common_table_expressions():
    """Test common table expressions using convenience decorator."""
    # This test will be automatically skipped if the backend
    # doesn't support basic CTEs
    assert True


@requires_json_operations()
def test_json_operations():
    """Test JSON operations using convenience decorator."""
    # This test will be automatically skipped if the backend
    # doesn't support any JSON operations
    assert True


@requires_returning_clause()
def test_returning_clause():
    """Test RETURNING clause using convenience decorator."""
    # This test will be automatically skipped if the backend
    # doesn't support the RETURNING clause
    assert True


# Example 3: Using requires_functions for function-level requirements
@requires_functions('json_array_insert', 'jsonb_array_insert')
def test_json_array_functions():
    """Test JSON array insert functions."""
    # This test will be automatically skipped if the backend
    # doesn't support json_array_insert or jsonb_array_insert
    assert True


# Example 4: Using requires_protocol with specific method
@requires_protocol(AdvancedGroupingSupport, 'supports_cube')
def test_cube_specific_method():
    """Test CUBE using requires_protocol with specific method."""
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])