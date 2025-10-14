# Feature Testing Framework

## Overview

This directory contains the feature testing framework for the python-activerecord library. The framework uses a capability-based approach to coordinate feature support between tests and database backends.

## Capability-Based Approach

Instead of the previous feature system, we now use a hierarchical capability system defined in `src/rhosocial/activerecord/backend/capabilities.py`. This system provides:

1. **Hierarchical Organization**: Capabilities are organized in logical categories
2. **Type Safety**: Using enums with bit flags for efficient checking
3. **Single Source of Truth**: All capability information is defined in backend modules
4. **Granular Control**: Tests can check for specific capabilities or broad categories

## Key Components

### 1. Capability Definitions (`capabilities.py`)

Defines the hierarchical capability structure using Python enums with bit flags:

```python
class CapabilityCategory(Flag):
    """Top-level capability categories."""
    NONE = 0
    SET_OPERATIONS = auto()
    WINDOW_FUNCTIONS = auto()
    # ... other categories

class WindowFunctionCapability(Flag):
    """Window function capabilities."""
    NONE = 0
    ROW_NUMBER = auto()
    RANK = auto()
    # ... other window functions
```

### 2. Backend Integration

Backends expose their capabilities through the `capabilities` property:

```python
# In your test
backend = get_backend()  # Get the current backend instance
if backend.capabilities.supports_window_function(WindowFunctionCapability.ROW_NUMBER):
    # Test window functions
```

### 3. Test Integration

Tests declare their required capabilities using decorators or markers:

```python
from ...backend.capabilities import WindowFunctionCapability
from ..utils import requires_capability

@requires_capability(WindowFunctionCapability.ROW_NUMBER)
def test_window_function():
    # Test implementation
    pass
```

## Usage

### For Backend Developers

Implement the `_initialize_capabilities()` method in your backend:

```python
class MyBackend(StorageBackend):
    def _initialize_capabilities(self) -> DatabaseCapabilities:
        capabilities = DatabaseCapabilities()
        
        # Add capabilities based on database version, etc.
        capabilities.add_window_function(WindowFunctionCapability.ROW_NUMBER)
        
        return capabilities
```

### For Test Developers

Use the convenience decorators or direct capability checking:

```python
# Using decorators
@requires_window_functions()
def test_window_functions():
    pass

# Using direct markers
@pytest.mark.requires_capability(WindowFunctionCapability.RANK)
def test_rank_function():
    pass

# Checking capabilities directly
def test_something(backend):
    if backend.capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS):
        # Test window function features
```

## Migration

For information on migrating from the old feature system, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).

## Design Documentation

For detailed design information, see [FEATURE_SUPPORT_DESIGN.md](FEATURE_SUPPORT_DESIGN.md).