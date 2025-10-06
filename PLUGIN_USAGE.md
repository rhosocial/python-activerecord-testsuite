# Using the Capability Checking Plugin

## Overview

The `rhosocial-activerecord-capabilities` pytest plugin provides automatic capability checking for tests that use the `@requires_capability` decorator. This ensures that tests are automatically skipped if the current backend doesn't support the required capabilities.

## Installation in Backend Projects

Backend projects that use the test suite should install the test suite package:

```bash
pip install rhosocial-activerecord-testsuite
```

## Backend Project Configuration

There are two ways to enable the plugin in backend projects:

### Option 1: Automatic Discovery (Recommended)
Since the plugin is registered via entry points, it should be automatically discovered by pytest when the package is installed.

### Option 2: Explicit Loading
You can explicitly load the plugin in your backend's `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-p rhosocial.activerecord.testsuite.plugin.pytest_activerecord_capabilities"
```

Or in your `pytest.ini`:

```ini
[tool:pytest]
addopts = -p rhosocial.activerecord.testsuite.plugin.pytest_activerecord_capabilities
```

## Usage

Once the plugin is available, tests using `@requires_capability` decorators will automatically be checked:

```python
from rhosocial.activerecord.backend.capabilities import CapabilityCategory, CTECapability
from rhosocial.activerecord.testsuite.utils import requires_capability

@requires_capability(CapabilityCategory.CTE, CTECapability.BASIC_CTE)
def test_basic_cte(extended_order_fixtures):
    """This test will be skipped if the backend doesn't support basic CTEs."""
    User, ExtendedOrder, ExtendedOrderItem = extended_order_fixtures
    # Test implementation here
    pass
```

## Plugin Behavior

1. The plugin hooks into pytest's test execution lifecycle
2. It detects tests with the `requires_capability` marker
3. During test execution, it accesses the model fixtures provided to the test
4. It checks if the backend supports the required capabilities
5. If not supported, the test is automatically skipped with an informative message

## Requirements

- The test must accept at least one fixture that provides an ActiveRecord model
- The model must have a `get_backend()` method (this is provided by the provider mechanism)
- The capability requirement must be in the format `(CapabilityCategory, specific_capability)`