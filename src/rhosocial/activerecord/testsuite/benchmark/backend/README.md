# Direct Backend Benchmark Contract

`benchmark/backend` is a contract-only area for direct backend benchmarks. The testsuite does not provide shared pytest tests or provider interfaces for this benchmark category.

Direct backend benchmarks call `StorageBackend.execute()` and `execute_many()` directly. SQL placeholders, DDL, insert id handling, `RETURNING` support, and batch execution behavior differ across database implementations, so each backend repository owns its own test files, schema, SQL, setup, and teardown.

Do not register `benchmark.backend.IBackendBenchmarkProvider`. Backend implementations should keep their local `tests/benchmark/backend/` test coverage aligned instead.

## Required local test files

Each backend repository should provide the same benchmark test items:

- `test_execute_crud_sync.py`
  - insert
  - find/get
  - update
  - delete
- `test_execute_crud_async.py`
  - insert
  - find/get
  - update
  - delete
- `test_execute_many_sync.py`
  - bulk insert
- `test_execute_many_async.py`
  - bulk insert

Supporting files such as `conftest.py` and `workloads.py` remain backend-owned. They may differ as needed for schema definition, SQL templates, parameter formatting, insert id extraction, and connection lifecycle management.
