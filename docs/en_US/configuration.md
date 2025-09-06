# Configuration Guide

This document details the various configuration options available for the test suite.

## 1. Flexible Configuration System

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

### SQLite Test Scenarios

The `rhosocial-activerecord` backend for SQLite supports several predefined test scenarios, which can be activated via environment variables. These scenarios allow for testing different operational modes and performance characteristics of SQLite.

-   **`memory`**: The default and fastest scenario, using an in-memory SQLite database. This is always active.
-   **`tempfile`**: Uses a temporary file on disk for the database. Useful for testing features that require database persistence. Activated by setting `TEST_SQLITE_FILE=true`.
-   **`debug`**: An in-memory database with SQL echoing enabled (via logging configuration) for debugging purposes. Activated by setting `TEST_SQLITE_DEBUG=true`.
-   **`performance`**: An in-memory database configured with optimized PRAGMA settings for performance testing. Activated by setting `TEST_SQLITE_PERFORMANCE=true`.
-   **`concurrent`**: Uses a file-based database with WAL (Write-Ahead Logging) mode enabled for concurrency testing. Activated by setting `TEST_SQLITE_CONCURRENT=true`.

You can enable multiple scenarios simultaneously by setting their respective environment variables. For example:

```bash
export TEST_SQLITE_FILE=true
export TEST_SQLITE_DEBUG=true
export TEST_SQLITE_PERFORMANCE=true
export TEST_SQLITE_CONCURRENT=true
pytest
```

Alternatively, you can specify which scenarios to run using the `--test-scenarios` pytest option:

```bash
pytest --test-scenarios="memory,debug"
```

### Custom Backend Configuration

To test your own backend (or other optional backends like MySQL, PostgreSQL), you need to configure the connection details. This can be done using environment variables.

#### Using Environment Variables (Recommended)

You can define one or more test targets by setting a series of environment variables in the shell where `pytest` is executed. Use a numeric suffix (`_1`, `_2`, etc.) to distinguish between different configurations.

For example, to define a test target named `mysql_ci`:
```bash
export AR_TEST_BACKEND_NAME_1=mysql_ci
export AR_TEST_BACKEND_DRIVER_1=mysql
export AR_TEST_BACKEND_HOST_1=127.0.0.1
export AR_TEST_BACKEND_PORT_1=3306
export AR_TEST_BACKEND_USER_1=root
export AR_TEST_BACKEND_PASSWORD_1=password
export AR_TEST_BACKEND_DATABASE_1=test_db
```
