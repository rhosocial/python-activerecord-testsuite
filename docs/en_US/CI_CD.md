# Continuous Integration (CI/CD) Guide

This guide provides best practices for configuring and running the `rhosocial-activerecord-testsuite` in a Continuous Integration (CI/CD) environment to enable automated testing for your database backend.

## Core Strategy: Matrix Builds and Service Containers

To perform comprehensive testing across multiple Python versions and various databases, we highly recommend using a "Matrix Build" strategy. This allows you to automatically create an independent test job for each combination of a Python version and a database.

GitHub Actions offers native support for this and is our preferred platform.

## Example GitHub Actions Workflow

Below is an example of a `.github/workflows/ci.yml` file that you can use as a template for your project.

```yaml
name: Python Package CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
        # Define the database services you want to test against
        database:
          - name: mysql
            image: mysql:8.0
            port: 3306
            env:
              MYSQL_ROOT_PASSWORD: password
              MYSQL_DATABASE: test_db
          - name: postgres
            image: postgres:15
            port: 5432
            env:
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
              POSTGRES_DB: test_db

    # Use a service container to start up the database
    services:
      db:
        image: ${{ matrix.database.image }}
        env: ${{ matrix.database.env }}
        ports:
          - ${{ matrix.database.port }}:${{ matrix.database.port }}

    steps:
    - uses: actions/checkout@v3
      with:
        # Fetch all history for all tags and branches
        fetch-depth: 0

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        # If your backend depends on rhosocial-activerecord, install it first
        # pip install rhosocial-activerecord
        # Install your backend library (assuming it's in the current repo)
        pip install .
        # Install the test suite with its extras
        pip install rhosocial-activerecord-testsuite[test,cov]

    - name: Run tests against database in service container
      run: |
        pytest --cov=${{ matrix.database.name }} --cov-report=xml
      env:
        # Dynamically configure the test backend via environment variables
        AR_TEST_BACKEND_NAME_1: ${{ matrix.database.name }}_ci
        AR_TEST_BACKEND_DRIVER_1: ${{ matrix.database.name }}
        AR_TEST_BACKEND_HOST_1: 127.0.0.1
        AR_TEST_BACKEND_PORT_1: ${{ matrix.database.port }}
        AR_TEST_BACKEND_USER_1: ${{ matrix.database.env.MYSQL_USER || matrix.database.env.POSTGRES_USER }}
        AR_TEST_BACKEND_PASSWORD_1: ${{ matrix.database.env.MYSQL_ROOT_PASSWORD || matrix.database.env.POSTGRES_PASSWORD }}
        AR_TEST_BACKEND_DATABASE_1: ${{ matrix.database.env.MYSQL_DATABASE || matrix.database.env.POSTGRES_DB }}

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }} # optional
        file: ./coverage.xml
```

### Workflow Explained

1.  **Matrix**: The `strategy.matrix` defines two dimensions of variables: `python-version` and `database`. GitHub Actions will create a separate job for every possible combination of these variables (e.g., `Python 3.8` + `MySQL 8.0`, `Python 3.14` + `PostgreSQL 15`, etc.).

2.  **Service Containers**: The `services` block uses Docker to start a temporary database container based on the `database.image` variable from the matrix. The `ports` mapping ensures that your test code can access this database via `localhost` and the specified port.

3.  **Dynamic Configuration**: In the "Run tests" step, instead of using a `backends.yml` file, we use the `env` block to set the database connection details as `AR_TEST_BACKEND_*` environment variables. The `config.py` module will automatically read these variables and configure the test target, enabling full automation.

4.  **Coverage**: The value for the `--cov` argument can also be dynamically set from the matrix, allowing you to generate separate coverage reports for each backend you test.

By using this approach, you can easily build a robust and extensible automated testing pipeline for your backend library.
