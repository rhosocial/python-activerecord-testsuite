# Migration Guide: From Feature System to Capability System

## Overview

This guide explains how to migrate from the old feature system to the new capability-based system for coordinating feature support between tests and backends.

## Key Differences

| Old Feature System | New Capability System |
|-------------------|----------------------|
| String-based feature identifiers | Enum-based hierarchical capabilities |
| FeatureSupport class | DatabaseCapabilities class |
| Feature constants in features.py | Enum constants in capabilities.py |
| Feature checking with `is_supported()` | Capability checking with specific methods |
| Flat feature organization | Hierarchical capability organization |

## Migration Steps

### 1. Update Test Decorators

**Old:**
```python
from ..features import DatabaseFeature
from ..utils import requires_feature

@requires_feature(DatabaseFeature.WINDOW_FUNCTIONS)
def test_window_function():
    pass
```

**New:**
```python
from ...backend.capabilities import WindowFunctionCapability
from ..utils import requires_capability

@requires_capability(WindowFunctionCapability.ROW_NUMBER)  # or any specific window function
def test_window_function():
    pass
```

### 2. Update Test Markers

**Old:**
```python
@pytest.mark.requires_feature([DatabaseFeature.CUBE, DatabaseFeature.ROLLUP])
def test_grouping():
    pass
```

**New:**
```python
@pytest.mark.requires_capability([AdvancedGroupingCapability.CUBE, AdvancedGroupingCapability.ROLLUP])
def test_grouping():
    pass
```

### 3. Replace Feature Constants

**Old Feature Constants:**
- `DatabaseFeature.WINDOW_FUNCTIONS`
- `DatabaseFeature.CUBE`
- `DatabaseFeature.ROLLUP`
- `DatabaseFeature.CTE`
- `DatabaseFeature.RETURNING_CLAUSE`

**New Capability Constants:**
- `WindowFunctionCapability.ROW_NUMBER` (or other specific functions)
- `AdvancedGroupingCapability.CUBE`
- `AdvancedGroupingCapability.ROLLUP`
- `CTECapability.BASIC_CTE`
- `ReturningCapability.BASIC_RETURNING`

### 4. Update Utility Functions

The utility functions in `testsuite/feature/utils.py` have been updated to work with the new capability system. The API is similar but uses capability enums instead of string features.

### 5. Backend Implementation

Backends now implement `_initialize_capabilities()` instead of using separate feature support classes.

## Common Migration Patterns

### Pattern 1: Simple Feature Check

**Old:**
```python
if feature_support.is_supported(DatabaseFeature.WINDOW_FUNCTIONS):
    # do something
```

**New:**
```python
if backend.capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS):
    # do something
```

### Pattern 2: Specific Feature Check

**Old:**
```python
if feature_support.is_supported(DatabaseFeature.CUBE):
    # do something
```

**New:**
```python
if backend.capabilities.supports_advanced_grouping(AdvancedGroupingCapability.CUBE):
    # do something
```

### Pattern 3: Multiple Feature Check

**Old:**
```python
features = [DatabaseFeature.WINDOW_FUNCTIONS, DatabaseFeature.CTE]
all_supported = all(feature_support.is_supported(f) for f in features)
```

**New:**
```python
# Check if both categories are supported
has_window = backend.capabilities.supports_category(CapabilityCategory.WINDOW_FUNCTIONS)
has_cte = backend.capabilities.supports_category(CapabilityCategory.CTE)
all_supported = has_window and has_cte
```

## Updated Convenience Functions

The convenience functions in `testsuite/feature/utils.py` have been updated:

- `requires_window_functions()` - now checks for any window function capability
- `requires_cube()` - now checks for CUBE grouping capability
- `requires_rollup()` - now checks for ROLLUP grouping capability
- `requires_cte()` - now checks for basic CTE capability
- `requires_recursive_cte()` - now checks for recursive CTE capability
- `requires_json_operations()` - now checks for any JSON operation capability
- `requires_returning_clause()` - now checks for basic RETURNING capability

## Benefits of Migration

1. **Type Safety**: Compile-time checking of capability references
2. **Hierarchical Organization**: Better organization of related capabilities
3. **Granular Control**: Ability to check for specific capabilities rather than broad categories
4. **Performance**: Bit flag operations for efficient capability checking
5. **Extensibility**: Easy to add new capability categories and specific capabilities
6. **Single Source of Truth**: Capabilities defined in backend modules, not duplicated in tests

## Timeline

It's recommended to migrate tests gradually:

1. Update the most critical tests first
2. Replace string-based feature checks with capability checks
3. Update test decorators and markers
4. Remove references to the old feature system
5. Eventually remove the deprecated features.py file

The old feature system will be maintained for backward compatibility during the transition period but will eventually be removed.