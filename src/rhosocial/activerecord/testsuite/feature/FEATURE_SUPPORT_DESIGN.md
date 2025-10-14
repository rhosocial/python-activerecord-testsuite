# Feature Support Coordination Mechanism Design (Capability-Based Approach)

## Overview

This document outlines the design of a mechanism for coordinating feature support between the testsuite and specific database backends using a capability-based approach. The mechanism allows:

1. Backends to define their capabilities in a hierarchical structure
2. Tests to declare their required capabilities
3. Automatic skipping of tests that require unsupported capabilities
4. Generation of warnings about unsupported capabilities

## Design Approach

### 1. Capability Definition System

Capabilities are defined using a hierarchical enum structure with bit flags for efficient combination and checking:

```python
# backend/capabilities.py

from enum import Flag, auto

class CapabilityCategory(Flag):
    """Top-level capability categories."""
    NONE = 0
    SET_OPERATIONS = auto()
    WINDOW_FUNCTIONS = auto()
    ADVANCED_GROUPING = auto()
    # ... other categories

class WindowFunctionCapability(Flag):
    """Window function capabilities."""
    NONE = 0
    ROW_NUMBER = auto()
    RANK = auto()
    LAG = auto()
    # ... other window functions

# Main capability structure
class DatabaseCapabilities:
    """Database capability descriptor."""
    
    def __init__(self):
        self.categories: CapabilityCategory = CapabilityCategory.NONE
        self.window_functions: WindowFunctionCapability = WindowFunctionCapability.NONE
        # ... other capability types
    
    def supports_window_function(self, function: WindowFunctionCapability) -> bool:
        """Check if a window function is supported."""
        return bool(self.window_functions & function)
    
    def add_window_function(self, function: WindowFunctionCapability) -> 'DatabaseCapabilities':
        """Add a window function capability."""
        self.window_functions |= function
        self.categories |= CapabilityCategory.WINDOW_FUNCTIONS
        return self
```

### 2. Backend Capability Declaration

Each backend declares its capabilities by implementing the `_initialize_capabilities` method:

```python
# SQLite backend example
class SQLiteBackend(StorageBackend):
    def _initialize_capabilities(self) -> DatabaseCapabilities:
        """Initialize SQLite capabilities based on version."""
        capabilities = DatabaseCapabilities()
        
        # Get SQLite version
        version = self.get_server_version()
        
        # Window functions supported from 3.25.0+
        if version >= (3, 25, 0):
            capabilities.add_window_function(ALL_WINDOW_FUNCTIONS)
        
        # RETURNING clause supported from 3.35.0+
        if version >= (3, 35, 0):
            capabilities.add_returning(ALL_RETURNING_FEATURES)
        
        # ... other capabilities
        
        return capabilities
```

### 3. Test Capability Requirements

Tests declare their required capabilities using pytest markers or decorators:

```python
# Example test file
import pytest
from ...backend.capabilities import WindowFunctionCapability, AdvancedGroupingCapability

@pytest.mark.requires_capability(WindowFunctionCapability.ROW_NUMBER)
def test_window_function_basic():
    # Test implementation
    pass

@pytest.mark.requires_capability([WindowFunctionCapability.ROW_NUMBER, AdvancedGroupingCapability.CUBE])
def test_window_with_cube():
    # Test implementation
    pass
```

Or using convenience decorators:

```python
from ..utils import requires_window_functions, requires_cube

@requires_window_functions()
def test_window_function_basic():
    # Test implementation
    pass

@requires_cube()
def test_cube_basic():
    # Test implementation
    pass
```

### 4. Automatic Test Skipping

A pytest plugin automatically skips tests that require unsupported capabilities:

```python
# testsuite/conftest.py
def pytest_collection_modifyitems(config, items):
    """Hook to automatically skip tests that require unsupported capabilities."""
    try:
        # Get current backend instance
        backend = get_current_backend()
        
        for item in items:
            # Check for capability requirements
            requires_capability_marker = item.get_closest_marker("requires_capability")
            if requires_capability_marker:
                required_capabilities = requires_capability_marker.args[0]
                
                # Skip test if capabilities are not supported
                from .feature.utils import skip_if_capability_unsupported
                try:
                    skip_if_capability_unsupported(backend, required_capabilities)
                except pytest.skip.Exception:
                    # Test should be skipped, let pytest handle it
                    pass
    except Exception as e:
        # If we can't determine capability support, continue normally
        warnings.warn(f"Could not check capability support: {e}", UserWarning)
```

### 5. Capability Warning System

Generate warnings about unsupported capabilities during test execution:

```python
# testsuite/conftest.py
def pytest_sessionstart(session):
    """Hook to generate capability support warnings at session start."""
    try:
        # Get current backend
        backend = get_current_backend()
        
        # Generate warnings for important unsupported capabilities
        capabilities = backend.capabilities
        
        unsupported_important_capabilities = []
        
        # Check for important capabilities
        if not capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS):
            unsupported_important_capabilities.append("Window Functions")
        
        if not capabilities.supports_advanced_grouping(AdvancedGroupingCapability.CUBE):
            unsupported_important_capabilities.append("CUBE Grouping")
        
        # ... other important capabilities
        
        if unsupported_important_capabilities:
            warnings.warn(
                f"Current backend does not support important capabilities: "
                f"{', '.join(unsupported_important_capabilities)}. "
                f"Some tests will be automatically skipped.",
                UserWarning
            )
    except Exception as e:
        # If we can't determine capability support, continue normally
        warnings.warn(f"Could not check capability support at session start: {e}", UserWarning)
```

## Benefits of the Capability-Based Approach

1. **Single Source of Truth**: All capability information is defined in the backend modules
2. **Hierarchical Organization**: Capabilities are organized in a logical hierarchy
3. **Type Safety**: Using enums with bit flags provides compile-time checking
4. **Flexible Checking**: Tests can check for specific capabilities or categories
5. **Version Awareness**: Backends can declare capabilities based on database version
6. **Extensibility**: New capability categories can be added without breaking existing code
7. **Clear Interface**: Backend instances expose capabilities through a clean, read-only property
8. **Test Integration**: Tests consume capability information directly from backend instances

## Implementation Plan

1. Create the capability definition module with all enums and structures
2. Modify the base StorageBackend to include capability support
3. Update backend implementations to declare their capabilities
4. Update the test utilities to work with the new capability system
5. Update the pytest plugin to use the new capability system
6. Migrate existing tests to use the new capability-based decorators
7. Document the new capability system for developers