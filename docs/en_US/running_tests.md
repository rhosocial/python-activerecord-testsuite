# Running Tests

This guide explains how to execute tests using the test suite.

## Table of Contents
- [1. Running Feature Tests](#1-running-feature-tests)
- [2. CRITICAL: PYTHONPATH Configuration](#2-critical-pythonpath-configuration)
- [3. Running Tests](#3-running-tests)
- [4. Generating Code Coverage Reports](#4-generating-code-coverage-reports)
- [5. Writing Tests](#5-writing-tests)

## [1. Running Feature Tests](#1-running-feature-tests)

This section details how to run the `feature` tests. The tests under the `basic` directory cover the fundamental functionalities of ActiveRecord, including:

- **CRUD Operations**: Creating, reading, updating, and deleting records (`test_crud.py`).
- **Field Type Handling**: Verification of various data types (strings, numbers, booleans, datetimes, JSON, etc.) (`test_fields.py`).
- **Data Validation**: Including field-level validation via Pydantic and custom business rule validation (`test_validation.py`).

### Schema Definition and Fixtures

The test suite defines the requirements for database schemas and test fixtures, but does not handle their creation or management directly. Instead, it provides **interfaces** that backends must implement to provide these resources.

For each test category (like `basic`), the test suite defines what schema and fixtures are needed. Your backend implementation is responsible for providing the SQL dialect-specific schema creation and fixture management through the required interfaces.

- **Schema Interface**: Backends must implement the schema creation interface to handle database-specific DDL statements.
- **Fixture Interface**: Backends need to provide test fixtures according to the specified requirements.

### Test Execution Flow

1. **Discovery**: `pytest` discovers the tests (e.g., `test_crud.py`).
2. **Configuration Loading**: The root `conftest.py` in the test suite calls `load_backend_configs()` to get a list of all database configurations to test against (both built-in SQLite and custom ones).
3. **Parametrization**: `pytest` creates a parameterized run for each configuration.
4. **Fixture Setup (`database`)**: For each run, the `database` fixture does the following:
    a. Connects to the specified database.
    b. Locates the correct schema file (e.g., `basic.sql`) based on the test file's path.
    c. Executes the SQL to create the necessary tables.
    d. Yields a tuple containing the configured backend instance and the connection configuration object.
5. **Model Fixture Setup**: Fixtures like `user_class` receive the result from the `database` fixture and bind the generic `User` model from `fixtures/models.py` to the live database connection.
6. **Test Run**: The test function (e.g., `test_create_user(user_class)`) executes using the fully configured model.
7. **Fixture Teardown**: The `database` fixture cleans up the database (drops tables, disconnects).

## 2. CRITICAL: PYTHONPATH Configuration

**MUST configure PYTHONPATH before running tests.** The test directories (`tests/`, `tests_original/`) are **NOT** on the Python path by default.

### Why PYTHONPATH is Required

```
project-root/
├── src/rhosocial/activerecord/    # ← Python can import this
├── tests/                          # ← NOT importable by default
└── tests_original/                 # ← NOT importable by default
```

Tests import from `rhosocial.activerecord`, but the test files themselves are not in the package structure. Without PYTHONPATH, pytest cannot find the source code.

### Platform-Specific Commands

**Linux/macOS (bash/zsh):**
```bash
# Single command execution
PYTHONPATH=src pytest tests/

# Persistent for session
export PYTHONPATH=src
pytest tests/
```

**Windows (PowerShell):**
```powershell
# Single command execution
$env:PYTHONPATH="src"; pytest tests/

# Persistent for session
$env:PYTHONPATH="src"
pytest tests/
```

**Windows (CMD):**
```cmd
REM Single command execution
set PYTHONPATH=src && pytest tests/

REM Persistent for session
set PYTHONPATH=src
pytest tests/
```

### Common Errors Without PYTHONPATH

```python
# Error you'll see:
ModuleNotFoundError: No module named 'rhosocial.activerecord'

# Solution:
# Set PYTHONPATH=src before running pytest
```

### IDE Configuration

**PyCharm:**
- Mark `src/` as "Sources Root"
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
PYTHONPATH=src
```

## 3. Running Tests

### Quick Reference

```bash
# ALWAYS set PYTHONPATH first
export PYTHONPATH=src  # or equivalent for your platform

# Run local backend tests only (default)
pytest tests/

# Run testsuite validation tests
pytest tests/ --run-testsuite

# Run specific feature tests
pytest tests/ --run-testsuite -m "feature_crud"

# Run original comprehensive tests
pytest tests_original/

# Run with capability report
pytest tests/ --run-testsuite --show-skipped-capabilities
```

### Test Selection by Markers

```bash
# Feature tests
pytest -m "feature"
pytest -m "feature_crud"
pytest -m "feature_query"

# Real-world scenarios
pytest -m "realworld"
pytest -m "scenario_ecommerce"

# Benchmarks
pytest -m "benchmark"
pytest -m "benchmark_bulk"
```

## 4. Generating Code Coverage Reports

The purpose of this test suite is to test the `rhosocial-activerecord` library and other third-party backends. Therefore, code coverage should be measured against these target libraries.

To generate a code coverage report, you first need to ensure `pytest-cov` is installed. Then, specify the target package with the `--cov` argument when running `pytest`.

```bash
# Run tests and generate an XML coverage report for rhosocial-activerecord
pytest --cov=rhosocial.activerecord --cov-report=xml
```

This will create a `coverage.xml` file in the project root. You can inspect the `<sources>` and `<packages>` tags within this file to verify that the report was generated for the correct target library.

## 5. Writing Tests

### For Testsuite Authors

**Rules:**
- NEVER import backend-specific modules
- NEVER write SQL directly (use provider interface)
- NEVER assume database features without declaring capability requirements
- ALWAYS use fixtures provided by provider
- ALWAYS use pytest markers
- ALWAYS specify BOTH category AND specific capability in requirements

**Example:**

```python
# Good - backend-agnostic with capability declaration
from rhosocial.activerecord.backend.capabilities import (
    CapabilityCategory,
    CTECapability
)
from rhosocial.activerecord.testsuite.utils import requires_capabilities

@pytest.mark.feature
@pytest.mark.feature_query
@requires_capabilities((CapabilityCategory.CTE, CTECapability.BASIC_CTE))
def test_basic_cte(order_fixtures):
    """Test basic CTE functionality."""
    User, Order, OrderItem = order_fixtures
    
    user = User(username='test', email='test@example.com')
    assert user.save()

# Bad - missing category in capability requirement
@requires_capabilities(CTECapability.BASIC_CTE)  # WRONG - no category
def test_basic_cte(order_fixtures):
    pass

# Bad - backend-specific
def test_basic_cte():
    from rhosocial.activerecord.backend.mysql import MySQLBackend
    # DON'T DO THIS
```

### For Backend Developers

**Rules:**
- MUST implement all provider interface methods
- MUST create schema files matching testsuite structure
- MUST prefix backend-specific tests with `test_{backend}_`
- MUST handle database connection pooling
- MUST clean up test data
- MUST declare backend capabilities accurately using add_* methods
- MUST return tuples from provider methods (even for single model)