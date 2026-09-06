# Running Tests

This guide explains how to execute tests using the test suite.

## Table of Contents
- [1. Running Feature Tests](#1-running-feature-tests)
- [2. PYTHONPATH Configuration](#2-pythonpath-configuration)
- [3. Running Tests](#3-running-tests)
- [4. Generating Code Coverage Reports](#4-generating-code-coverage-reports)
- [5. Writing Tests](#5-writing-tests)

## [1. Running Feature Tests](#1-running-feature-tests)

This section details how to run the `feature` tests. The tests under the `basic` directory cover the fundamental functionalities of ActiveRecord, including:

- **CRUD Operations**: Creating, reading, updating, and deleting records (`test_crud.py`).
- **Field Type Handling**: Verification of various data types (strings, numbers, booleans, datetimes, JSON, etc.) (`test_fields.py`).
- **Data Validation**: Including field-level validation via Pydantic and custom business rule validation (`test_validation.py`).

### Schema Definition and Fixtures

The test suite defines the requirements for database schemas and test fixtures, but does not handle their creation or management directly. Instead, each topic exposes an **interface** (`interfaces.py`) that backends implement to provide these resources.

For each test topic (like `basic`), the test suite defines what schema and fixtures are needed. Your backend implementation is responsible for providing the SQL dialect-specific schema creation and fixture management through the required provider interfaces (`setup_*_fixtures` / `async_setup_*_fixtures` and their teardown counterparts).

### Test Execution Flow

1. **Discovery**: `pytest` discovers the tests imported into the backend's own `tests/` tree.
2. **Provider resolution**: Tests request model fixtures (e.g. `user_class`); these fixtures route through the backend's registered provider, which creates the schema and configures the model classes against a live backend.
3. **Scenario parametrization**: Each backend registers one or more scenarios via its provider (e.g. SQLite `memory`, MySQL `mysql_80`). Tests are parametrized across the registered scenarios; the `--scenarios` option selects a subset.
4. **Test run**: `test_create_user(user_class)` executes using the fully configured model bound to the scenario's backend.
5. **Fixture teardown**: The provider tears down fixtures and disconnects in the correct order (data → cursors → connection).

## [2. PYTHONPATH Configuration](#2-pythonpath-configuration)

**Set `PYTHONPATH` so pytest can import the backend's test utilities.** When running the testsuite from a backend project root, the backend's `tests/` directory contains the provider registry (e.g. `tests/providers/registry.py`) that the testsuite discovers via the `TESTSUITE_PROVIDER_REGISTRY` environment variable. Without `PYTHONPATH=tests`, pytest cannot import this module.

### Why PYTHONPATH is Required

```
backend-project/
├── src/                    # ← the package under test (importable if installed)
└── tests/
    └── providers/registry.py   # ← NOT importable by default; needs PYTHONPATH=tests
```

The testsuite locates the backend's provider registry through
`TESTSUITE_PROVIDER_REGISTRY` (default `providers.registry:provider_registry`).
Without `PYTHONPATH=tests`, python cannot import the `providers` package and the
run fails with `ImportError: No module named 'providers'`.

### Platform-Specific Commands

**Linux/macOS (bash/zsh):**
```bash
# Single command execution (from a backend project root)
PYTHONPATH=tests pytest tests/rhosocial/activerecord_test/feature/

# Persistent for session
export PYTHONPATH=tests
pytest tests/
```

**Windows (PowerShell):**
```powershell
# Single command execution
$env:PYTHONPATH="tests"; pytest tests/

# Persistent for session
$env:PYTHONPATH="tests"
pytest tests/
```

**Windows (CMD):**
```cmd
REM Single command execution
set PYTHONPATH=tests && pytest tests/

REM Persistent for session
set PYTHONPATH=tests
pytest tests/
```

### Common Errors Without PYTHONPATH

```python
# Error you'll see (when PYTHONPATH=tests is missing):
ImportError: No module named 'providers'

# Solution:
# Set PYTHONPATH=tests before running pytest so the backend's
# tests/providers/registry.py can be imported.
```

### IDE Configuration

**PyCharm:**
- Mark the backend's `tests/` as a "Sources Root"
- Test runner automatically adds it to PYTHONPATH

**VS Code:**
```json
// .vscode/settings.json
{
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.pytestEnabled": true,
    "python.envFile": "${workspaceFolder}/.env"
}
```

```bash
# .env file
PYTHONPATH=tests
```

## [3. Running Tests](#3-running-tests)

The test suite is imported by backend packages rather than run on its own.
Run the tests from a backend project root (e.g. `python-activerecord/`), not
from this directory. A backend wires the suite into its own `tests/` tree and
provides `TESTSUITE_PROVIDER_REGISTRY` via its top-level `tests/conftest.py`.

### Running the imported tests

```bash
# Run the feature tests imported by the backend
pytest tests/rhosocial/activerecord_test/feature/basic

# Run a single topic (e.g. relation)
pytest tests/rhosocial/activerecord_test/feature/relation

# Run the whole imported suite
pytest tests/
```

### Sync / async selection

The project configures `asyncio_mode = "auto"`, so pytest-asyncio marks every
`async def test_*` as an `asyncio` test at collection time. No explicit marker
is written in source. To select:

```bash
# Async tests only
pytest tests/ -m asyncio

# Sync tests only
pytest tests/ -m "not asyncio"

# Or by path / name (async files carry the `_async` suffix)
pytest tests/ -k async
pytest tests/ -k "not async"
```

### Test selection by category

Category is expressed through directory layout, not markers:

```bash
# Feature tests
pytest tests/rhosocial/activerecord_test/feature

# Benchmarks
pytest tests/rhosocial/activerecord_test/benchmark
```

### Capability-based filtering

Backend-specific capability skips are driven by two generic markers:
`requires_protocol` and `requires_functions` (see `configuration.md`). You may
filter with:

```bash
# List registered markers
pytest --markers

# Collect only tests that do not require extra capabilities
pytest tests/ -m "not requires_protocol and not requires_functions" --collect-only
```

## [4. Generating Code Coverage Reports](#4-generating-code-coverage-reports)

The purpose of this test suite is to test the `rhosocial-activerecord` library and other third-party backends. Therefore, code coverage should be measured against these target libraries.

To generate a code coverage report, you first need to ensure `pytest-cov` is installed. Then, specify the target package with the `--cov` argument when running `pytest`.

```bash
# Run tests and generate an XML coverage report for rhosocial-activerecord
pytest --cov=rhosocial.activerecord --cov-report=xml
```

This will create a `coverage.xml` file in the project root. You can inspect the `<sources>` and `<packages>` tags within this file to verify that the report was generated for the correct target library.

## [5. Writing Tests](#5-writing-tests)

### For Testsuite Authors

**Rules:**
- NEVER import backend-specific modules
- NEVER write SQL directly (use provider interface)
- NEVER assume database features without declaring capability requirements
- ALWAYS use fixtures provided by provider
- Capability requirements use exactly two decorators: `requires_protocol` and `requires_functions`

**Example:**

```python
# Good - backend-agnostic with a protocol capability declaration
from rhosocial.activerecord.backend.dialect.protocols import WindowFunctionSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol, requires_functions

@requires_protocol(WindowFunctionSupport, "supports_window_functions")
def test_window_functions(order_fixtures):
    """Test window function support."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test', email='test@example.com')
    assert user.save(), "expected user to be saved"

# Good - function-name capability declaration
@requires_functions('json_array_insert', 'jsonb_array_insert')
def test_json_insert(json_user_fixtures):
    """Test JSON insert function support."""
    pass

# Bad - backend-specific
def test_basic_cte():
    from rhosocial.activerecord.backend.mysql import MySQLBackend
    # DON'T DO THIS
```

### For Backend Developers

**Rules:**
- MUST implement all provider interface methods (both `setup_*_fixtures` and
  `async_setup_*_fixtures` pairs as supported by the backend).
- MUST create schema files matching the testsuite structure.
- MUST import the testsuite into your own `tests/` tree via thin bridge files
  (`from ...testsuite.feature.<topic>.test_x import *`).
- MUST handle database connection pooling and clean up test data.
- MUST return tuples from provider methods (even for single model).
- Capability handling is driven by the dialects: `requires_protocol` reads
  Protocol-class support, `requires_functions` reads `supports_functions(...)`
  — backends do not declare capabilities separately with `add_*` methods.