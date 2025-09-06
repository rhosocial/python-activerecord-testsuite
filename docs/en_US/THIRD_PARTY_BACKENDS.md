# Third-Party Backend Integration Guide

One of the core design goals of `rhosocial-activerecord-testsuite` is extensibility. It allows any third-party database backend to seamlessly plug into the suite to validate its compatibility with `rhosocial-activerecord`.

This guide details the requirements and configuration steps for a third-party backend to be tested.

## 1. The Core Mechanism: Entry Points

The test suite automatically discovers and loads backend drivers using Python's standard `entry_points` mechanism. This means that any backend library wishing to be recognized by the suite must register itself to a specific entry point.

## 2. Integration Steps

Let's assume you are developing a backend library named `acme-corp-superdb`, and its driver class is `AcmeDBBackend`.

### Step 1: Register the Entry Point in Your Backend Library

In the `pyproject.toml` file of your `acme-corp-superdb` project, add the following:

```toml
[project.entry-points."rhosocial.activerecord.backend"]
acme_db = "acme_corp.activerecord.backend.impl.acme_db:AcmeDBBackend"
```

- **`[project.entry-points."rhosocial.activerecord.backend"]`**: This is a fixed entry point group name. All backends must register under this group.
- **`acme_db`**: This is the "short name" you define for your driver. This name is important, as it will be used as the `driver` value in `backends.yml`.
- **`"acme_corp.activerecord.backend.impl.acme_db:AcmeDBBackend"`**: This is the full, importable path to your backend driver's main class.

### Step 2: Install Your Backend Library

Ensure that your `acme-corp-superdb` library is installed (either in editable mode with `pip install -e .` or as a regular package) into the same Python virtual environment where you are running the test suite.

### Step 3: Configure a Test Instance

You can configure the database instances to be tested in two ways. **Environment variables take precedence over the `backends.yml` file**.

#### Method 1: Using `backends.yml` (Recommended for Local Development)

In the root of the `python-activerecord-testsuite` project, create or modify the `backends.yml` file:

```yaml
acme:
  acme_test_instance_1:
    driver: acme_db
    host: "db.acme.com"
    port: 9999
    username: "test_user"
    password: "secret"
    database: "testsuite_db_for_acme"
```

#### Method 2: Using Environment Variables (Recommended for CI/CD)

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

## 3. Running the Tests

After completing the steps above, no other changes are needed. Simply run `pytest` from the root of the `python-activerecord-testsuite` project:

```bash
pytest
```

The test suite loader will automatically discover and load all configurations, then run the full suite against them.