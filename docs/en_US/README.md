# Test Suite Documentation

This documentation provides comprehensive guides for using the test suite.

## Table of Contents

- [Introduction](README.md)
- [Configuration](configuration.md)
- [Running Tests](running_tests.md)

## 1. Introduction

Welcome to the ActiveRecord Test Suite. This package provides a standardized testing contract for all database backends integrating with the `rhosocial-activerecord` library.

The primary goal is to ensure that every backend, whether official or third-party, behaves consistently and correctly according to the core library's expectations. The suite is built on three pillars:

-   **Feature Tests**: Validate individual, atomic functionalities (e.g., CRUD operations, query methods, field types).
-   **Real-world Scenarios**: Simulate complex business logic to test interactions between different components.
-   **Benchmark Tests**: Measure and compare performance metrics across different backends.

**Important**: This test suite contains only the test logic and does not include environment preparation such as fixtures or database schemas. Instead, it provides interfaces that backends should implement to provide these resources. Each backend implementation is responsible for creating and managing its own test environment according to the provided interfaces.

## 2. Getting Started for Backend Developers

To use this test suite to validate your custom database backend, follow these steps:

### Prerequisites

-   A working database backend implementation that inherits from `rhosocial.activerecord.backend.StorageBackend`.
-   Your backend package should be installable in the test environment.
-   Your backend must implement the required interfaces for providing test fixtures and database schemas.

### Installation

Add `rhosocial-activerecord-testsuite` as a development dependency in your backend's `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "rhosocial-activerecord-testsuite>=0.1.0",
    "pytest-cov>=4.0.0"
]
```