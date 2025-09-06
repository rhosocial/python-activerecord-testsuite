# RhoSocial ActiveRecord Test Suite

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

This package contains the standardized test suite for the [RhoSocial ActiveRecord](https://github.com/rhosocial/python-activerecord) library. Its primary purpose is to provide a consistent set of test contracts that all official and third-party database backends must implement to ensure compatibility and reliability.

By separating the test definitions from the backend implementations, we can guarantee that all backends adhere to the same core functionalities and behaviors expected by the ActiveRecord interface.

## Testing Philosophy

Our testing strategy is built on three core pillars:

1.  **Feature Tests**: Validate individual functionality points (e.g., `where` queries, `save` methods, `BelongsTo` relationships).
2.  **Real-world Scenarios**: Simulate actual business scenarios to verify complex interactions and data integrity.
3.  **Performance Benchmarks**: Measure and compare backend performance under standardized loads.

## Structure

The test suite is organized into the following main categories, located in `src/rhosocial/activerecord/testsuite/`:

-   `/feature`: Core feature tests.
-   `/realworld`: Complex, real-world application scenarios.
-   `/benchmark`: Performance and load tests.

## Usage for Backend Developers

If you are developing a database backend for RhoSocial ActiveRecord, you should include this test suite as a development dependency. Your backend's test runner will execute these tests against your implementation, using your provided database schema fixtures.

A typical workflow involves:
1.  Adding `rhosocial-activerecord-testsuite` to your `pyproject.toml`.
2.  Creating database schema fixtures that match the structure required by the tests.
3.  Running the test suite against your backend to identify and fix compatibility issues.
4.  Generating a compatibility report to document your backend's compliance level.

For detailed instructions, please refer to the main project's [testing documentation](https://github.com/rhosocial/python-activerecord/blob/main/tests/rhosocial/activerecord_test/README.md).

## Contributing

Contributions are welcome! Please refer to the main repository's [contribution guidelines](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md).

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
