## [1.0.0.dev3] - 2025-11-29

### Added

- Added capability-based skipping for JOIN tests, improving test relevance across different backends. Refined and fixed various query tests for better cross-backend compatibility, including fixes for full outer join and `tree_fixtures` behavior. Removed problematic datetime function tests for stability. ([#2](https://github.com/rhosocial/python-activerecord-testsuite/issues/2))


## [1.0.0.dev2] - 2025-11-07

### Added

- Integrated `towncrier` and `setuptools-scm` for tooling, enhanced CTE and window function testing capabilities, and adapted to the ActiveRecord definition move. ([#1](https://github.com/rhosocial/python-activerecord-testsuite/issues/1))
