# src/rhosocial/activerecord/testsuite/feature/utils.py

from typing import List, Union
import pytest
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    SetOperationCapability,
    WindowFunctionCapability,
    AdvancedGroupingCapability,
    CTECapability,
    JSONCapability,
    ReturningCapability,
    TransactionCapability,
    BulkOperationCapability
)

def requires_capability(capability):
    """Decorator to mark a test function as requiring specific database capabilities.
    
    Args:
        capability: Single capability or list of capabilities
        
    Returns:
        pytest.mark.requires_capability decorator
    """
    return pytest.mark.requires_capability(capability)

def skip_if_capability_unsupported(backend, capability):
    """Skip test if backend doesn't support required capabilities.
    
    Args:
        backend: Backend instance
        capability: Single capability or list of capabilities
        
    Raises:
        pytest.skip: If any required capabilities are not supported
    """
    # Ensure it's a list
    if not isinstance(capability, list):
        capability = [capability]
    
    # Check if all required capabilities are supported
    unsupported_capabilities = []
    
    for cap in capability:
        if isinstance(cap, CapabilityCategory):
            if not backend.capabilities.supports_category(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, SetOperationCapability):
            if not backend.capabilities.supports_set_operation(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, WindowFunctionCapability):
            if not backend.capabilities.supports_window_function(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, AdvancedGroupingCapability):
            if not backend.capabilities.supports_advanced_grouping(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, CTECapability):
            if not backend.capabilities.supports_cte(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, JSONCapability):
            if not backend.capabilities.supports_json(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, ReturningCapability):
            if not backend.capabilities.supports_returning(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, TransactionCapability):
            if not backend.capabilities.supports_transaction(cap):
                unsupported_capabilities.append(str(cap))
        elif isinstance(cap, BulkOperationCapability):
            if not backend.capabilities.supports_bulk_operation(cap):
                unsupported_capabilities.append(str(cap))
    
    if unsupported_capabilities:
        pytest.skip(
            f"Skipping test - unsupported capabilities: {', '.join(unsupported_capabilities)}"
        )

# Convenience functions for common capability checks
def requires_window_functions():
    """Decorator for tests requiring window functions."""
    return requires_capability(WindowFunctionCapability.ROW_NUMBER)  # Any window function

def requires_cube():
    """Decorator for tests requiring CUBE grouping."""
    return requires_capability(AdvancedGroupingCapability.CUBE)

def requires_rollup():
    """Decorator for tests requiring ROLLUP grouping."""
    return requires_capability(AdvancedGroupingCapability.ROLLUP)

def requires_cte():
    """Decorator for tests requiring Common Table Expressions."""
    return requires_capability(CTECapability.BASIC_CTE)

def requires_recursive_cte():
    """Decorator for tests requiring recursive CTEs."""
    return requires_capability(CTECapability.RECURSIVE_CTE)

def requires_json_operations():
    """Decorator for tests requiring JSON operations."""
    return requires_capability(JSONCapability.JSON_EXTRACT)  # Any JSON operation

def requires_returning_clause():
    """Decorator for tests requiring RETURNING clause."""
    return requires_capability(ReturningCapability.BASIC_RETURNING)