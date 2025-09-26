# Project Overview: rhosocial-activerecord-testsuite

## Project Name
- **Repository Name**: python-activerecord-testsuite
- **Python Package Name**: rhosocial-activerecord-testsuite

## Project Purpose
This project is a standardized test suite for the `rhosocial-activerecord` Python package. It provides contracts for features, real-world scenarios, and benchmarks to validate backend implementations.

## Key Design Principles
1. **Backend-Agnostic**: Only handles test logic and fixture definitions
2. **Provider Interface Pattern**: Defines contracts backends must implement
3. **Multi-Fixture Support**: Accommodates tests requiring multiple fixture classes
4. **Standardized Testing**: Ensures consistent validation across backend implementations

## Documentation

The project includes comprehensive documentation in the `docs/` directory organized as follows:

- **`docs/en_US/`**: English documentation
  - `README.md`: Overview and getting started guide
  - `configuration.md`: Configuration options and interface requirements
  - `running_tests.md`: How to execute tests with interface-based fixture management
- **`docs/zh_CN/`**: Chinese documentation (mirror of English documentation)
  - Contains the same documents as the English version, localized for Chinese speakers
- **`docs/plan.md`**: Design document outlining the architecture and responsibilities of the test suite and backend providers

The documentation emphasizes that the test suite only contains test logic and does not include environment preparation (fixtures/schema). Instead, it provides interfaces that backends must implement to provide these resources. Each backend implementation is responsible for creating and managing its own test environment according to the provided interfaces.