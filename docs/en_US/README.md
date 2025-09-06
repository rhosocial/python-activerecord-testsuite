# RhoSocial ActiveRecord Test Suite Documentation

## 1. Introduction

Welcome to the RhoSocial ActiveRecord Test Suite. This package provides a standardized testing contract for all database backends integrating with the `rhosocial-activerecord` library.

The primary goal is to ensure that every backend, whether official or third-party, behaves consistently and correctly according to the core library's expectations. The suite is built on three pillars:

-   **Feature Tests**: Validate individual, atomic functionalities (e.g., CRUD operations, query methods, field types).
-   **Real-world Scenarios**: Simulate complex business logic to test interactions between different components.
-   **Benchmark Tests**: Measure and compare performance metrics across different backends.

## 2. Getting Started for Backend Developers

To use this test suite to validate your custom database backend, follow these steps:

### Prerequisites

-   A working database backend implementation that inherits from `rhosocial.activerecord.backend.StorageBackend`.
-   Your backend package should be installable in the test environment.

### Installation

Add `rhosocial-activerecord-testsuite` as a development dependency in your backend's `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "rhosocial-activerecord-testsuite>=0.1.0"
]
```

## 3. Configuration

The test suite is driven by a flexible configuration system that allows you to test against multiple database versions and setups.

### Backend Drivers and Namespaces

Before configuring, it's important to understand how backends are loaded:

-   **Official Backends**: Backends released by `rhosocial` are installed under the `rhosocial.activerecord.backend.impl` namespace (e.g., `...impl.mysql`). The test suite's default configuration loader knows how to find these.
-   **Third-Party Backends**: If you are developing a third-party backend, it should reside in its own namespace (e.g., `acme_corp.activerecord.backend.impl.acme_db`). To make the test suite aware of your driver, you would need to register it, typically using Python's `entry_points` mechanism in your package's `pyproject.toml`.

### Built-in SQLite Support

The test suite includes built-in support for testing the `sqlite` backend that ships with `rhosocial-activerecord`. The configurations are determined by the Python version you are using to run the tests.

-   **Automatic Detection**: By default, the test suite detects the current Python version (e.g., 3.11) and runs tests against its corresponding SQLite version (e.g., `sqlite_py311_mem` and `sqlite_py311_file`).
-   **CI/CD Override**: You can force tests to run against a specific Python version's configuration by setting the `PYTEST_TARGET_VERSION` environment variable. For example:
    ```bash
    PYTEST_TARGET_VERSION=3.10 pytest
    ```

### Custom Backend Configuration (`backends.yml`)

To test your own backend (or other optional backends like MySQL, PostgreSQL), you need to create a `backends.yml` file in the root of your project.

**Example `backends.yml` for a MySQL backend:**
```yaml
mysql:
  # A custom name for this configuration
  mysql_8_0:
    # The driver name must match a registered backend driver
    driver: mysql 
    host: "127.0.0.1"
    port: 3306
    username: "root"
    password: "password"
    database: "testsuite_db"
```
The test runner will automatically discover and use this file to run the entire test suite against your configured MySQL instance.

## 4. Running Feature Tests

This section details how to run the `feature` tests. The tests under the `basic` directory cover the fundamental functionalities of ActiveRecord, including:

-   **CRUD Operations**: Creating, reading, updating, and deleting records (`test_crud.py`).
-   **Field Type Handling**: Verification of various data types (strings, numbers, booleans, datetimes, JSON, etc.) (`test_fields.py`).
-   **Data Validation**: Including field-level validation via Pydantic and custom business rule validation (`test_validation.py`).

### Schema Definition

The test suite uses a convention-over-configuration approach for database schemas. For each test category (like `basic`), you must provide a schema file in a corresponding `schemas` directory. The test runner for your backend needs to provide the SQL dialect-specific version of this file.

-   **Example Path**: `.../testsuite/feature/basic/schemas/basic.sql`
-   **Content**: This file should contain all `CREATE TABLE` statements required for the tests in the `.../feature/basic/` directory.

### Test Execution Flow

1.  **Discovery**: `pytest` discovers the tests (e.g., `test_crud.py`).
2.  **Configuration Loading**: The root `conftest.py` in the test suite calls `load_backend_configs()` to get a list of all database configurations to test against (both built-in SQLite and custom ones from `backends.yml`).
3.  **Parametrization**: `pytest` creates a parameterized run for each configuration.
4.  **Fixture Setup (`database`)**: For each run, the `database` fixture does the following:
    a.  Connects to the specified database.
    b.  Locates the correct schema file (e.g., `basic.sql`) based on the test file's path.
    c.  Executes the SQL to create the necessary tables.
    d.  Yields a tuple containing the configured backend instance and the connection configuration object.
5.  **Model Fixture Setup**: Fixtures like `user_class` receive the result from the `database` fixture and bind the generic `User` model from `fixtures/models.py` to the live database connection.
6.  **Test Run**: The test function (e.g., `test_create_user(user_class)`) executes using the fully configured model.
7.  **Fixture Teardown**: The `database` fixture cleans up the database (drops tables, disconnects).

### Running the Tests

From your backend project's root directory, simply run `pytest`:

```bash
# Run all tests against all configured backends
pytest

# Run only the basic feature tests
pytest src/rhosocial/activerecord/testsuite/feature/basic/
```

## 5. Code Conventions

To maintain a clean and consistent codebase, we adhere to the following convention:

- **Path Comments**: All files within the `src/` directory (including `.py`, `.sql`, etc.) must begin with a comment on the first line that indicates the file's relative path from the project root (`python-activerecord-testsuite`).

  Example: `# src/rhosocial/activerecord/testsuite/conftest.py`

## 6. Troubleshooting

When running and debugging the test suite, you may encounter various environment and code-related issues. We have compiled a detailed guide to help you resolve them.

-   [Troubleshooting Guide](./TROUBLESHOOTING.md)

## 7. Contributing

Contributions to the test suite are welcome! Please refer to the main repository's [contribution guidelines](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md).