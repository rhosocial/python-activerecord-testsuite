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
