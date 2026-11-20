# RhoSocial ActiveRecord Test Suite

> **⚠️ Development Stage Notice:** This project is currently under development. Features may be added or removed at any time, and there may be defects or inconsistencies with actual implementations. Therefore, the documentation content is subject to change at any time and is for reference only.

[![PyPI version](https://badge.fury.io/py/rhosocial-activerecord-testsuite.svg)](https://badge.fury.io/py/rhosocial-activerecord-testsuite)
[![Python](https://img.shields.io/pypi/pyversions/rhosocial-activerecord-testsuite.svg)](https://pypi.org/project/rhosocial-activerecord-testsuite/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

This package contains the standardized test suite for the [RhoSocial ActiveRecord](https://github.com/rhosocial/python-activerecord) library. Its primary purpose is to provide a consistent set of test contracts that all official and third-party database backends must implement to ensure compatibility and reliability.

By separating the test definitions from the backend implementations, we can guarantee that all backends adhere to the same core functionalities and behaviors expected by the ActiveRecord interface.

## Testing Philosophy

The suite's mature, actively maintained pillar is **feature tests**: a single
copy of each contract, shared by every backend through thin bridge files. The
other two categories exist but are **not mature and not documented here**:

-   **Real-world scenarios** (`/realworld`) — not mature; not covered in this README.
-   **Performance benchmarks** (`/benchmark`) — not mature; not covered in this
    README. Backends run benchmarks in their own dedicated CI jobs.

## Structure

Everything importable lives under `src/rhosocial/activerecord/testsuite/`:

-   `/feature` — **mature**, the main subject of this suite (see below).
-   `/realworld` — immature; out of scope for this document.
-   `/benchmark` — immature; out of scope for this document.
-   `/pytest_plugin` — the capability/parallelism plugin (see its own README).

### Feature topics

`feature/` is split into topic directories, each a self-contained contract unit
with its own fixtures and a directory-level `Declaration`. A backend imports a
topic by adding thin `conftest.py` + `test_*.py` bridges that star-import the
shared modules — the test bodies exist once.

| Topic | What it validates | Sync/async |
|-------|-------------------|------------|
| `basic/` | The core object model: CRUD, composite-PK CRUD, field types and type adapters, validation, connection/worker lifecycle, transactions, bulk CRUD, field generation, derived fields, DDL statements, materialized views, and keyless/read-only models. Also hosts `basic/events/` (model lifecycle events) and `basic/fixtures/` (the single definition site for shared models). | both |
| `query/` | `ActiveQuery` — construction, joins, aggregates, range/window queries, JSON/special/typed-column queries, query contexts and error handling. | both |
| `cte/` | `CTEQuery` — common table expressions (recursive, composite-PK). | both |
| `setop/` | `SetOperationQuery` — UNION / INTERSECT / EXCEPT. | both |
| `query_integration/` | Cross-type combinations of `ActiveQuery` / `CTEQuery` / `SetOperationQuery` (each paired query type contributes its own combined fixtures). | both |
| `query/relation/` | Model relationships — belongs-to / has-many / has-one, eager loading, descriptors, caching, modifiers, ordering, validation. (Historically `feature/relation`.) | both |
| `cli/` | The model CLI (`rhosocial.activerecord.cli`) — DML/DQL/bulk/read-only/soft-delete/validation/set-CTE commands, in-process. | both |
| `mixins/` | Reusable field mixins — timestamps, soft delete, optimistic lock, UUID, etc. | both |
| `adapters/`, `interface/`, `contracts/`, `backend/`, `ddl/` | Lower-level contracts: type adapters, interface compliance, shared contract helpers, backend capabilities, DDL source derivation. | varies |

> Note: `ddl/` is still maturing and is **not yet wired into any backend**; it is
> kept in the suite but excluded from backend CI.

Each topic may declare `uses_database`, `parallel`, and dialect `requires`
through its `DECLARATION`. Database use is opt-in: topics that only render SQL
or compute values declare nothing and never open a connection. See the
[plugin README](src/rhosocial/activerecord/testsuite/pytest_plugin/README.md)
for the full mechanism.

## Capability-based Testing

An integrated pytest plugin evaluates what each backend dialect answers. Tests
marked `@requires_protocol(...)` are skipped only when the dialect genuinely
answers "no"; a dialect that does not implement a required probe fails loudly
instead of silently skipping a whole group. The plugin registers itself through
the package's `pytest11` entry point — installing this package is enough.

See [`pytest_plugin/README.md`](src/rhosocial/activerecord/testsuite/pytest_plugin/README.md)
for the full mechanism.

## Backend wiring and parallel units

Two parts of the suite are now considered mature:

- **Backend integration** — a backend supplies one `backend_scenario` fixture and
  thin conftest/bridge files that import the shared directories; test bodies live
  in exactly one place.
- **Minimum parallel unit** — each test directory declares its own unit
  (`Declaration.parallel`, `uses_database`, `requires`). A directory sharing a
  database is pinned to one xdist worker, and database use is opt-in: scopes that
  only render or compute declare nothing and open no connection.

Both are documented in detail in the [plugin README](src/rhosocial/activerecord/testsuite/pytest_plugin/README.md).

## Usage for Backend Developers

If you are developing a database backend for RhoSocial ActiveRecord, include this
suite as a development dependency. The plugin installs automatically; you provide
the scenarios and thin bridges, not a copy of the tests.

A typical workflow involves:
1.  Adding `rhosocial-activerecord-testsuite` to your `pyproject.toml`.
2.  Defining a parametrized `backend_scenario` fixture that yields your scenarios
    (each knows its backend classes, config factory and database reset).
3.  Adding thin `conftest.py` files that star-import the corresponding shared
    directory, plus bridge modules that import the shared test functions.
4.  Running the suite; use `--dist=loadgroup` for parallel runs so tests sharing
    one database stay on one worker.
5.  Fixing dialect gaps reported loudly by the capability checks, and recording
    your backend's compliance level.

For detailed instructions, please refer to the main project's [testing documentation](https://github.com/rhosocial/python-activerecord/blob/main/tests/rhosocial/activerecord_test/README.md).

## Contributing

Contributions are welcome! Please refer to the main repository's [contribution guidelines](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md).

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
