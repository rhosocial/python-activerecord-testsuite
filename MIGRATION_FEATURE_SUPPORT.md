# Migrating to the Feature Support Mechanism

This guide explains how to migrate existing tests to use the new feature support mechanism.

## Before Migration (Legacy Approach)

```python
import pytest

@pytest.fixture(scope="function")
def skip_if_unsupported(request):
    """Skip tests if database doesn't support advanced grouping features."""
    if is_sqlite_backend(request):
        pytest.skip("SQLite does not support advanced grouping features")

def test_cube_basic(extended_order_fixtures, skip_if_unsupported):
    """Test basic CUBE functionality."""
    # Test implementation
    pass
```

## After Migration (New Approach)

```python
import pytest
from ..features import DatabaseFeature
from ..utils import requires_feature

@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic(extended_order_fixtures):
    """Test basic CUBE functionality."""
    # Test implementation
    pass
```

## Migration Steps

### 1. Identify Feature Requirements

Look at existing skip fixtures and conditions to identify required features:
- `skip_if_unsupported` often indicates required features
- Version checks in code indicate feature availability
- Exception handling for unsupported features

### 2. Add Feature Requirement Decorators

Replace skip fixtures with `@requires_feature` decorators:

**Before:**
```python
def test_window_function(order_fixtures, skip_if_unsupported):
    # Test implementation
    pass
```

**After:**
```python
@requires_feature(DatabaseFeature.WINDOW_FUNCTIONS)
def test_window_function(order_fixtures):
    # Test implementation
    pass
```

### 3. Remove Legacy Skip Fixtures

Remove skip fixtures that are now handled by the feature support mechanism:

**Before:**
```python
@pytest.fixture(scope="function")
def skip_if_unsupported(request):
    if is_sqlite_backend(request):
        pytest.skip("SQLite does not support advanced grouping features")

def test_cube_basic(extended_order_fixtures, skip_if_unsupported):
    # Test implementation
    pass
```

**After:**
```python
@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic(extended_order_fixtures):
    # Test implementation
    pass
```

### 4. Handle Multiple Feature Requirements

For tests requiring multiple features, use a list:

**Before:**
```python
def test_complex_query(order_fixtures, skip_if_unsupported):
    # Test requires both window functions and CTEs
    pass
```

**After:**
```python
@requires_feature([DatabaseFeature.WINDOW_FUNCTIONS, DatabaseFeature.CTE])
def test_complex_query(order_fixtures):
    # Test implementation
    pass
```

## Common Migration Patterns

### Pattern 1: Simple Feature Requirement

**Before:**
```python
def test_rollup(order_fixtures, skip_if_unsupported):
    # Test implementation
    pass
```

**After:**
```python
@requires_feature(DatabaseFeature.ROLLUP)
def test_rollup(order_fixtures):
    # Test implementation
    pass
```

### Pattern 2: Version-Based Skipping

**Before:**
```python
def is_window_supported():
    version = sqlite3.sqlite_version_info
    return version >= (3, 25, 0)

@pytest.fixture(scope="module")
def skip_if_unsupported():
    if not is_window_supported():
        pytest.skip("SQLite version doesn't support window functions")

def test_row_number_window_function(order_fixtures, skip_if_unsupported):
    # Test implementation
    pass
```

**After:**
```python
@requires_feature(DatabaseFeature.WINDOW_FUNCTIONS)
def test_row_number_window_function(order_fixtures):
    # Test implementation
    pass
```

### Pattern 3: Backend-Specific Skipping

**Before:**
```python
def is_sqlite_backend(request):
    if hasattr(request, 'node'):
        backend_name = request.node.name.split('-')[0].lower()
        return 'sqlite' in backend_name
    return False

@pytest.fixture(scope="function")
def skip_for_sqlite(request):
    if is_sqlite_backend(request):
        pytest.skip("SQLite does not support advanced grouping")

def test_cube_basic(extended_order_fixtures, skip_for_sqlite):
    # Test implementation
    pass
```

**After:**
```python
@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic(extended_order_fixtures):
    # Test implementation
    pass
```

## Best Practices

### 1. Be Specific About Feature Requirements

Instead of skipping entire test files, mark individual tests with specific requirements:

**Better:**
```python
@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic():
    # Test implementation
    pass

@requires_feature(DatabaseFeature.ROLLUP)
def test_rollup_basic():
    # Test implementation
    pass
```

### 2. Combine Related Features

For tests requiring multiple related features, list them together:

```python
@requires_feature([DatabaseFeature.WINDOW_FUNCTIONS, DatabaseFeature.RETURNING_CLAUSE])
def test_window_with_returning():
    # Test implementation
    pass
```

### 3. Keep Tests Focused

Each test should ideally require a small set of features to maximize compatibility across backends.

## Testing the Migration

After migrating tests, verify that:

1. Tests still pass on backends that support the required features
2. Tests are properly skipped on backends that don't support the required features
3. No functionality is lost in the migration process

Run tests with different backends to ensure proper behavior:

```bash
# Run with SQLite backend
pytest -m "not mysql and not postgresql" tests/

# Check that unsupported tests are skipped
pytest --tb=short -v tests/
```

## Benefits of Migration

1. **Automatic Test Management**: No more manual skip fixtures
2. **Clearer Requirements**: Feature requirements are explicit in test decorators
3. **Better Reporting**: Skipped tests show clear reasons
4. **Reduced Code Duplication**: No more repeated skip logic
5. **Easier Maintenance**: Centralized feature support declarations