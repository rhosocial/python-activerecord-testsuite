# Feature Support Coordination Mechanism - Design Summary

## Overview

This document summarizes the design of the feature support coordination mechanism for the RhoSocial ActiveRecord testsuite. The mechanism allows tests to declare required database features and automatically skips tests that require unsupported features.

## Requirements Addressed

1. ✅ **Allow testsuite to define features used by tests** - Implemented through `DatabaseFeature` constants
2. ✅ **Provide a way to mark test units with required features** - Implemented through `@requires_feature` decorator and pytest markers
3. ✅ **Enable backends to declare their supported features** - Implemented through `FeatureSupport` classes
4. ✅ **Automatically skip unsupported tests during pytest collection** - Implemented through `pytest_collection_modifyitems` hook
5. ✅ **Generate warnings about unsupported features** - Implemented through `pytest_sessionstart` hook

## Design Components

### 1. Feature Definition System

Centralized feature constants ensure consistency:
```python
class DatabaseFeature:
    WINDOW_FUNCTIONS = "window_functions"
    CUBE = "cube"
    ROLLUP = "rollup"
    # ... more features
```

### 2. Backend Feature Declaration

Each backend implements a `FeatureSupport` subclass:
```python
class SQLiteFeatureSupport(FeatureSupport):
    def _declare_features(self):
        if self.version >= (3, 25, 0):
            self.supports(DatabaseFeature.WINDOW_FUNCTIONS)
```

### 3. Test Feature Requirements

Tests declare requirements using decorators:
```python
@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic():
    pass
```

### 4. Automatic Test Skipping

Pytest plugin automatically skips unsupported tests:
```python
def pytest_collection_modifyitems(config, items):
    # Check each test for required features
    # Skip if any required features are not supported
```

### 5. Feature Warning System

Warnings are generated for important unsupported features:
```python
def pytest_sessionstart(session):
    # Generate warnings for important unsupported features
```

## Alternative Approaches Considered

### Approach 1: Decorator-Based Feature Declaration

**Pros:**
- More explicit and readable
- Can include additional metadata
- Familiar to Python developers

**Cons:**
- Requires importing decorator in each test file
- Less standard than pytest markers

**Decision:** Used this approach as primary method because it's more explicit and readable.

### Approach 2: Class-Level Feature Declaration

**Pros:**
- Applies to all tests in the class
- Reduces repetition

**Cons:**
- Less granular control
- All tests in class must require same features

**Decision:** Not implemented as primary approach but could be used in addition for test classes where all tests require the same features.

### Approach 3: Fixture-Based Feature Checking

**Pros:**
- Leverages existing pytest fixture system
- Automatic dependency injection

**Cons:**
- Less explicit about requirements
- Harder to understand at a glance
- More complex implementation

**Decision:** Not implemented as it's less clear than decorator-based approach.

## Implementation Benefits

1. **Automatic Test Management**: Tests automatically skipped based on backend capabilities
2. **Clear Requirements**: Test requirements explicitly declared through decorators
3. **Backend Independence**: Each backend can declare its own feature support
4. **Version Awareness**: Feature support conditional on database version
5. **Developer Feedback**: Warnings inform developers about important unsupported features
6. **Maintainability**: Centralized feature definitions and support logic
7. **Extensibility**: Easy to add new features and backends

## Migration Strategy

1. **Phase 1**: Implement core feature support mechanism
2. **Phase 2**: Update existing tests to use new mechanism
3. **Phase 3**: Remove legacy feature checking code
4. **Phase 4**: Document and train developers on new approach

## Future Enhancements

1. **Feature Compatibility Matrix**: Generate reports showing which backends support which features
2. **Feature Deprecation**: Warn about deprecated features
3. **Feature Requirements Documentation**: Automatically generate documentation of test feature requirements
4. **Backend-Specific Test Markers**: Allow running tests for specific backends only

## Conclusion

The implemented feature support coordination mechanism provides a clean, maintainable solution that meets all requirements while being easy to use and extend. The decorator-based approach is intuitive for developers, and the automatic test skipping ensures that tests only run on compatible backends.