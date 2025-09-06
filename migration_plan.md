# Test Suite Migration Plan

This document outlines the plan to migrate tests from `python-activerecord` to the new `python-activerecord-testsuite` package. The migration will be done in phases to ensure a smooth transition.

## Phase 1: Migrate Basic CRUD Tests

The first phase focuses on migrating the fundamental CRUD (Create, Read, Update, Delete) tests, as they are the most self-contained and form the core of the test suite.

### Step 1: Move Core Test Files

The following files will be moved from the `python-activerecord` project to the `python-activerecord-testsuite` project:

-   **Move Test File:**
    -   **From**: `python-activerecord/tests/rhosocial/activerecord_test/basic/test_crud.py`
    -   **To**: `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/feature/basic/test_crud.py`
-   **Move Fixture Models:**
    -   **From**: `python-activerecord/tests/rhosocial/activerecord_test/basic/fixtures/models.py`
    -   **To**: `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py`

### Step 2: Create Test Utilities

The original tests rely on helper functions from `python-activerecord/tests/rhosocial/activerecord_test/utils.py`. We need to create a generic version of these utilities within the test suite.

-   **Create New Utility File:**
    -   **File**: `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/utils/helpers.py`
    -   **Content**: This file will contain functions to help backend developers set up tests, such as a simplified `create_active_record_fixture` that can be used by any backend. It will also contain a base `conftest.py` setup that backends can extend.

### Step 3: Refactor Migrated Tests and Models

The moved files need to be adapted to be backend-agnostic.

-   **In `.../testsuite/feature/basic/fixtures/models.py`**:
    -   Remove any direct dependency on a specific backend.
    -   Models like `User`, `TypeCase` will be defined as pure, backend-agnostic Pydantic models inheriting from `ActiveRecord`.
    -   The expectation will be that the test runner (from a specific backend project) provides the database connection and table schema.

-   **In `.../testsuite/feature/basic/test_crud.py`**:
    -   Update imports to point to the new fixture location within the test suite.
    -   Modify test functions to accept model fixtures (e.g., `user_class`) that are provided by the backend's test setup, rather than being imported directly. This makes the tests reusable.

### Step 4: Create Initial `__init__.py`

-   **Create New `__init__.py` File:**
    -   **File**: `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/__init__.py`
    -   **Content**: Define the initial version numbers for the test suite as planned in the documentation.
        ```python
        # rhosocial/activerecord/testsuite/__init__.py
        __version__ = "0.1.0"
        __feature_version__ = "0.1.0"
        __realworld_version__ = "0.1.0"
        __benchmark_version__ = "0.1.0"
        ```

## Phase 2: Migrate Validation and Field Tests

Once the CRUD tests are successfully migrated and validated, we will proceed with the other tests from the `basic` module.

-   **Move Test Files:**
    -   `test_validation.py` -> `.../testsuite/feature/basic/test_validation.py`
    -   `test_fields.py` -> `.../testsuite/feature/basic/test_fields.py`
-   **Refactor**: Apply the same refactoring principles from Phase 1 to these files and their corresponding models in `fixtures/models.py`.

## Phase 3: Migrate Query and Relation Tests

This phase is more complex as query and relation tests can have more backend-specific nuances.

-   **Move Test Files:**
    -   `python-activerecord/tests/rhosocial/activerecord_test/query/*` -> `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/feature/query/`
    -   `python-activerecord/tests/rhosocial/activerecord_test/relation/*` -> `python-activerecord-testsuite/src/rhosocial/activerecord/testsuite/feature/relation/`
-   **Analyze and Refactor**:
    -   Carefully separate generic test logic from any backend-specific SQL or behavior.
    -   Backend-specific tests (like `EXPLAIN` for SQLite) will remain in the original repository for now.
    -   Update all fixtures and models to be backend-agnostic.
