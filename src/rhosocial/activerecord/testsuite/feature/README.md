# Feature Testing Framework

## Overview

This directory contains the feature testing framework for the python-activerecord library. The
framework uses a capability-based approach to coordinate feature support between tests and database
backends.

## Feature Categories

Tests are organized into two-level categories for discoverability and maintainability:

| Category | Description |
|----------|-------------|
| `basic/` | Core CRUD, field types, type adapters, validation, column mapping, connection/worker lifecycle, **composite PK CRUD**, **derived field** — [details](basic/README.md) |
| `query/` | ActiveQuery — building, execution, aggregation, joins, CTEs, window functions, eager loading, cross-database, **composite PK queries/CTE/set operations** — [details](query/README.md) |
| `relation/` | Relationship descriptors (`BelongsTo`/`HasOne`/`HasMany`), caching, eager loading, validation, modifiers, derived fields, edge cases — [details](relation/README.md) |
| `events/` | Lifecycle hooks and event handler registration — [details](events/README.md) |
| `mixins/` | Built-in mixins — timestamps, soft delete, optimistic locking — [details](mixins/README.md) |
| `interface/` | Core interface utilities — `ThreadSafeDict` — [details](interface/README.md) |
| `examples/` | Documentation examples for the capability-based framework — [details](examples/README.md) |
| `backend/` | Backend feature declaration utilities (not tests) — [details](backend/README.md) |

### Two-Level Classification (执行分级)

Feature categories are further grouped into two execution levels (**一级 / 二级**).
A backend integration is expected to run level-1 suites first and in order
(`basic` → `relation` → `query`), and only proceed to level-2 suites once
level-1 suites pass (failures limited to correctly capability-gated skips).

| Level | Categories | Rationale |
|-------|------------|-----------|
| **一级 (Level 1)** | `basic/`, `relation/`, `query/` | Core ActiveRecord contract: models, CRUD, fields/types, relationships, and ActiveQuery. A backend that cannot pass level-1 is not considered usable. |
| **二级 (Level 2)** | `events/`, `mixins/`, `interface/`, `examples/` | Extended behaviors built on top of level-1 primitives (lifecycle hooks, timestamp/soft-delete/optimistic-locking mixins, interface utilities). |

Notes:
- `backend/` is a utility directory (backend feature declaration helpers), not a
  test suite, and does not belong to either level.
- `composite_pk/` and `derived_field/` no longer exist as top-level suites;
  their tests are merged into level-1 (`basic/` and `query/`), so they count as
  level-1 content.
- Within each level, run categories one at a time; long-running suites should
  not be mixed into a single pytest invocation when validating a backend
  integration.
- Level assignments are about **execution ordering and acceptance gates**, not
  capability gating: individual tests may still be skipped via the capability
  system (`@requires_protocol`, provider registration, etc.) regardless of
  their level.


> **Note:** `composite_pk/` and `derived_field/` have been merged into `basic/` and `query/`.
> Their `interfaces.py`, `conftest.py`, and `fixtures/` remain as shared providers.

Each subdirectory under a category represents a focused topic area. Tests within a subdirectory
are paired as sync/async variants following the testsuite's parity conventions.

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