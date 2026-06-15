## [v1.0.0.dev15] - 2026-06-15


### Internal

- Derived field test contracts, fixtures, and async coverage
  Bulk operations test contracts and benchmark comparisons
  Eager loading test coverage expansion with nested and async parity
  Profile model fixtures for sync/async parity testing
  Synchronous/Asynchronous descriptor mixing prohibition
  Dialect mixins refactored into directory-based modules
  Update pytest dependency constraints for broader compatibility ([#18](https://github.com/rhosocial/python-activerecord-testsuite/issues/18))


## [v1.0.0.dev14] - 2026-05-29


### Added

- Added FastAPI concurrent benchmark suite with multi-strategy connection pool testing, configurable rounds, and pool warmup exclusion; expanded Pydantic validation contracts and SQL injection immunity tests. ([#17](https://github.com/rhosocial/python-activerecord-testsuite/issues/17))


## [v1.0.0.dev13] - 2026-05-15

### Removed

- Removed deprecated `requires_capability` marker and `pytest_activerecord_capabilities` plugin. Use `requires_protocol` and `requires_functions` markers instead, which check dialect protocol support via `isinstance` and `supports_functions()` dictionary. ([#16](https://github.com/rhosocial/python-activerecord-testsuite/pull/16)) ([#16](https://github.com/rhosocial/python-activerecord-testsuite/issues/16))



### Changed

- Migrated capability-based test selection to dialect protocol system. Added `requires_functions` decorator for function-level capability checking and `skip_test_if_functions_unsupported()` runtime checker. Removed `test_capability_integration.py` (moved to core library). ([#16](https://github.com/rhosocial/python-activerecord-testsuite/pull/16)) ([#16](https://github.com/rhosocial/python-activerecord-testsuite/issues/16))


## [v1.0.0.dev12] - 2026-05-01


### Fixed

- Fixed CTE test assertions to be dialect-aware for placeholder format. ([#15](https://github.com/rhosocial/python-activerecord-testsuite/pull/15)) ([#15](https://github.com/rhosocial/python-activerecord-testsuite/issues/15))


## [v1.0.0.dev11] - 2026-04-17


### Fixed

- Updated test expectation for LRU cache eviction to properly reflect behavior change. Registered `requires_inner_join` pytest marker for capability-based tests. ([#14](https://github.com/rhosocial/python-activerecord-testsuite/issues/14))


## [v1.0.0.dev10] - 2026-04-12

### Removed

- **BREAKING**: Removed BEFORE_SAVE/AFTER_SAVE events. Use BEFORE_INSERT/AFTER_INSERT and BEFORE_UPDATE/AFTER_UPDATE instead. ([#12](https://github.com/rhosocial/python-activerecord-testsuite/issues/12))



### Added

- Added BEFORE_INSERT, AFTER_INSERT, BEFORE_UPDATE, and AFTER_UPDATE events for more fine-grained control over insert vs update operations. Event callbacks now receive operation-specific parameters: INSERT events receive data dict, UPDATE events receive data dict and dirty_fields set. ([#12](https://github.com/rhosocial/python-activerecord-testsuite/issues/12))


## [v1.0.0.dev9] - 2026-04-08

### Added

- Added connection pool context awareness tests for ActiveRecord and query classes with backend-agnostic provider interfaces ([#10](https://github.com/rhosocial/python-activerecord-testsuite/issues/10))


## [v1.0.0.dev8] - 2026-04-06


### Added

- Added WorkerPool integration tests for ActiveRecord, enabling comprehensive testing of asynchronous database operations with concurrent workers. ([#9](https://github.com/rhosocial/python-activerecord-testsuite/issues/9))


## [v1.0.0.dev7] - 2026-03-19

### Added

- Added environment-aware fixture selection system with Python version-specific model classes for optimized test fixtures. ([#7](https://github.com/rhosocial/python-activerecord-testsuite/issues/7))


## [v1.0.0.dev6] - 2026-03-12

### Added

- Added `requires_protocol` pytest marker for protocol-based test selection, enabling backends to declare ILIKE support via `ILIKESupport` protocol instead of hardcoded skip reasons. ([#6](https://github.com/rhosocial/python-activerecord-testsuite/issues/6))


## [v1.0.0.dev5] - 2026-02-27


### Added

- Added comprehensive CTE query tests with ActiveQuery integration, set operation tests (UNION, INTERSECT, EXCEPT), operator overload tests for set operations, async test classes for validation, field types and column mapping, range query tests, and capability-based skipping for INTERSECT/EXCEPT tests on backends that do not support these operations. ([#5](https://github.com/rhosocial/python-activerecord-testsuite/issues/5))



### Fixed

- Fixed GROUP BY test to use explicit column selection for SQL standard compliance, fixed async fixture cleanup order, fixed deserialization logic in ListToStringAdapter, updated CTE query set operation tests to properly handle async parameters, and fixed various async test issues. ([#5](https://github.com/rhosocial/python-activerecord-testsuite/issues/5))


## [v1.0.0.dev4] - 2025-12-11


### Added

- Added new test infrastructure, comprehensive test cases for custom column name mapping and annotated type adapters. Enhanced fixtures for mapping and query tests, and fixed a foreign key constraint violation in mapped models test. ([#4](https://github.com/rhosocial/python-activerecord-testsuite/issues/4))



### Changed

- Updated tests to use UTC instead of local time to ensure timezone consistency. ([#3](https://github.com/rhosocial/python-activerecord-testsuite/issues/3))


## [1.0.0.dev3] - 2025-11-29

### Added

- Added capability-based skipping for JOIN tests, improving test relevance across different backends. Refined and fixed various query tests for better cross-backend compatibility, including fixes for full outer join and `tree_fixtures` behavior. Removed problematic datetime function tests for stability. ([#2](https://github.com/rhosocial/python-activerecord-testsuite/issues/2))


## [1.0.0.dev2] - 2025-11-07

### Added

- Integrated `towncrier` and `setuptools-scm` for tooling, enhanced CTE and window function testing capabilities, and adapted to the ActiveRecord definition move. ([#1](https://github.com/rhosocial/python-activerecord-testsuite/issues/1))
