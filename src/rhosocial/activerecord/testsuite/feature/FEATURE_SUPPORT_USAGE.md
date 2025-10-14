# Feature Support Mechanism

## Overview

The feature support mechanism allows tests to declare which database features they require and automatically skips tests that require unsupported features. This ensures that tests only run on backends that support the required functionality.

## Components

### 1. Feature Definitions

Features are defined as constants in `features.py`:

```python
class DatabaseFeature:
    WINDOW_FUNCTIONS = "window_functions"
    CUBE = "cube"
    ROLLUP = "rollup"
    # ... more features
```

### 2. Feature Support Declaration

Each backend declares its supported features:

```python
class SQLiteFeatureSupport(FeatureSupport):
    def __init__(self, version: Tuple[int, int, int]):
        super().__init__()
        self.version = version
        self._declare_features()
    
    def _declare_features(self):
        # Window functions supported from 3.25.0+
        if self.version >= (3, 25, 0):
            self.supports(DatabaseFeature.WINDOW_FUNCTIONS)
        # ... more feature declarations
```

### 3. Test Feature Requirements

Tests declare their required features using decorators or markers:

```python
@requires_feature(DatabaseFeature.CUBE)
def test_cube_basic():
    # Test implementation
    pass

@requires_feature([DatabaseFeature.WINDOW_FUNCTIONS, DatabaseFeature.CTE])
def test_window_with_cte():
    # Test implementation
    pass
```

## Usage

### For Test Authors

1. Import the required modules:
   ```python
   from ..features import DatabaseFeature
   from ..utils import requires_feature
   ```

2. Decorate test functions with required features:
   ```python
   @requires_feature(DatabaseFeature.CUBE)
   def test_cube_basic():
       # Test implementation
       pass
   ```

3. For tests requiring multiple features:
   ```python
   @requires_feature([DatabaseFeature.WINDOW_FUNCTIONS, DatabaseFeature.CTE])
   def test_window_with_cte():
       # Test implementation
       pass
   ```

### For Backend Developers

1. Create a feature support class for your backend:
   ```python
   class MyBackendFeatureSupport(FeatureSupport):
       def __init__(self, version):
           super().__init__()
           self.version = version
           self._declare_features()
       
       def _declare_features(self):
           # Declare supported features based on version
           if self.version >= (1, 0, 0):
               self.supports([
                   DatabaseFeature.WINDOW_FUNCTIONS,
                   DatabaseFeature.CTE
               ])
   ```

2. Integrate with the pytest configuration to provide your backend's feature support.

## How It Works

1. **Feature Declaration**: Backends declare which features they support
2. **Test Marking**: Tests are marked with required features
3. **Automatic Skipping**: During test collection, pytest automatically skips tests requiring unsupported features
4. **Warnings**: Important unsupported features generate warnings at session start

## Benefits

- **Automatic Test Management**: Tests are automatically skipped based on backend capabilities
- **Clear Requirements**: Test requirements are explicitly declared
- **Backend Independence**: Each backend can declare its own feature support
- **Version Awareness**: Feature support can be conditional on database version
- **Developer Feedback**: Warnings inform developers about important unsupported features