# Running Tests

This guide explains how to execute tests using the test suite.

## 1. Running Feature Tests

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
2.  **Configuration Loading**: The root `conftest.py` in the test suite calls `load_backend_configs()` to get a list of all database configurations to test against (both built-in SQLite and custom ones).
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

### Generating Code Coverage Reports

The purpose of this test suite is to test the `rhosocial-activerecord` library and other third-party backends. Therefore, code coverage should be measured against these target libraries.

To generate a code coverage report, you first need to ensure `pytest-cov` is installed. Then, specify the target package with the `--cov` argument when running `pytest`.

```bash
# Run tests and generate an XML coverage report for rhosocial-activerecord
pytest --cov=rhosocial.activerecord --cov-report=xml
```

This will create a `coverage.xml` file in the project root. You can inspect the `<sources>` and `<packages>` tags within this file to verify that the report was generated for the correct target library.
