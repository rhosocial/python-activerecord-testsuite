# Troubleshooting Guide

This document records common issues, errors, and their solutions that you may encounter when running the test suite. These lessons were learned from a full debugging session and are intended to help backend developers quickly pinpoint and resolve problems.

## 1. Environment Configuration Issues

A correctly configured Python and dependency environment is crucial before running tests.

### Error: `poetry: command not found`

**Cause**:

`poetry` is not installed, or its installation path has not been added to the system's `PATH` environment variable.

**Solution**:

1.  **Recommended**: Ensure `poetry` is correctly installed and configured in your `PATH`.
2.  **Alternative**: If you do not want to or cannot add `poetry` to the `PATH`, you can directly use the Python interpreter from the virtual environment created by `poetry` to run `pytest`. Assuming your virtual environment is in `.venv3.13` within the project directory:

    ```bash
    # Execute from the project root
    .venv3.13/bin/python -m pytest src/rhosocial/activerecord/testsuite/feature/
    ```

### Error: `ModuleNotFoundError: No module named 'email_validator'`

**Cause**:

The test environment is missing a required dependency. The `EmailStr` type in `pydantic` requires the `email-validator` package, which may not have been installed correctly.

**Solution**:

Use `pip` from the virtual environment to install the missing dependency. `pydantic` manages these optional dependencies through an "extras" mechanism.

```bash
.venv3.13/bin/python -m pip install "pydantic[email]"
```

### Error: `SSL: CERTIFICATE_VERIFY_FAILED`

**Cause**:

An SSL certificate verification error occurred while `pip` was installing dependencies. This typically happens in corporate networks or environments with a network proxy, where your system cannot verify PyPI's SSL certificate.

**Solution**:

Add the `--trusted-host` argument to the `pip` command to trust PyPI's host. This is a common workaround in restricted network environments.

```bash
.venv3.13/bin/python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org "pydantic[email]"
```

## 2. API Mismatch Between Test Code and Core Library

When the test suite version does not perfectly match the `rhosocial-activerecord` core library version, a series of `TypeError` and `AttributeError` exceptions may occur.

### Debugging Journey Recap

During one debugging session, we encountered the following sequence of errors, which revealed issues in the test fixture design:

1.  **`TypeError: BaseActiveRecord.configure() got an unexpected keyword argument 'backend'`**
    *   **Problem**: Fixtures like `user_class` in `conftest.py` incorrectly called the model configuration method as `User.configure(backend=db_session)`.
    *   **Analysis**: The `ActiveRecord.configure` method expects `config` (a connection configuration object) and `backend_class` (the backend class), not an instance of the `backend`.

2.  **`AttributeError: 'dict' object has no attribute 'connection_config'`**
    *   **Problem**: After fixing the previous issue, we tried `User.configure(config=db_session.connection_config, ...)`. This led to a new error because the `db_session` parameter was actually the configuration dictionary (`dict`) passed in by `pytest`'s parametrization, not a `backend` instance.
    *   **Analysis**: This was due to a misunderstanding of `pytest`'s fixture parametrization. A directly parametrized fixture receives the parameter value itself, not the result of the fixture's execution.

3.  **`AttributeError: 'SQLiteBackend' object has no attribute 'connection_config'`** and **`'SQLiteBackend' object has no attribute 'name'`**
    *   **Problem**: After correcting the fixture execution flow with `indirect=True`, we found that the `backend` instance did not have attributes like `connection_config` or `name`.
    *   **Analysis**: This information existed in the original `config` dictionary loaded at the start of the test run but was not stored on the `backend` instance itself.

### Final Solution: Refactoring Fixtures

To resolve these issues comprehensively, we refactored `conftest.py` and `utils/helpers.py` to ensure all required information was created and passed correctly.

1.  **Changes in `helpers.py`**:
    *   The `setup_database` function was modified to return a tuple `(backend, connection_config)`, containing both the `backend` instance and the `connection_config` object it uses.
    *   The `teardown_database` function was modified to accept a `backend_name` parameter for clearer logging.

2.  **Changes in `conftest.py`**:
    *   The `database` fixture (formerly `db_session`) was parametrized using `indirect=True`.
    *   The `database` fixture calls `setup_database` and then `yield`s the tuple containing the `backend` instance and the `connection_config` object.
    *   During the teardown phase, the `database` fixture calls `teardown_database`, passing the `backend_name` from the original `config` dictionary.
    *   All model fixtures depending on it (e.g., `user_class`) receive this tuple, unpack it to get the objects they need, and correctly call `User.configure()`.

This refactored structure ensures a clear and correct data flow, which is a good practice for writing robust test suites.

## 3. Resolving Test Warnings and Subsequent Errors

After fixing the main errors, tests may still fail or produce warnings. Here are the final steps taken to resolve all remaining issues.

### Error: `sqlite3.OperationalError: table users already exists`

*   **Cause**: Although `teardown_database` was being called after each test, the `DROP TABLE` statements within it were not being committed to the database. This is because the `ActiveRecord` library's `execute` method, by default, only auto-commits DML statements (like `INSERT`, `UPDATE`), not DDL statements like `DROP TABLE`.
*   **Solution**: Modify the `teardown_database` function in `testsuite/utils/helpers.py` to wrap all `DROP TABLE` statements within a transaction. This ensures that the operations are properly committed.

    ```python
    def teardown_database(backend, backend_name):
        # ...
        try:
            with backend.transaction():
                backend.execute("DROP TABLE IF EXISTS users;")
                backend.execute("DROP TABLE IF EXISTS type_cases;")
                backend.execute("DROP TABLE IF EXISTS validated_field_users;")
        # ...
    ```

### Warning: `PytestConfigWarning: Unknown config option: python_paths`

*   **Cause**: `pytest` found an unrecognized configuration option, `python_paths`, in its configuration file (`pyproject.toml` under the `[tool.pytest.ini_options]` section).
*   **Solution**: Edit the `pyproject.toml` file and remove the `python_paths = ["src"]` line from the `[tool.pytest.ini_options]` section.

### Warning: `Pydantic serializer warnings` (Decimal to float conversion)

*   **Cause**: In the test code, a high-precision `Decimal` value was being assigned to a model field typed as a `float`. Pydantic issued a warning because this conversion could lead to a loss of precision.
*   **Solution**: Modify the test cases in `test_crud.py` to ensure that the value assigned to the `balance` field is a `float` type, not a `Decimal`. For example, change `Decimal("100.50")` to `100.50`.

### Warning: `ConnectionError` (on test exit)

*   **Cause**: When all tests have finished and the Python interpreter is shutting down, the `__del__` method of `SQLiteBackend` is called for final cleanup. However, some modules it depends on (like `os` or `sys`) may have already been unloaded, causing an error when it tries to delete the database file.
*   **Solution**: This is a robustness issue in the `python-activerecord` library itself. It was fixed by modifying `python-activerecord/src/rhosocial/activerecord/backend/impl/sqlite/backend.py`. The file deletion logic was moved from the `disconnect` method to a new `_delete_db_files` method, which is registered with the `atexit` module to ensure it is called reliably during interpreter shutdown.

    ```python
    # Added to SQLiteBackend's __init__ method:
    if self.config.delete_on_close and not self.config.is_memory_db():
        import atexit
        atexit.register(self._delete_db_files)

    # The file deletion logic was moved to the new _delete_db_files method.
    ```
