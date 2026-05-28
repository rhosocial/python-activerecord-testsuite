# Performance Benchmarks

This directory contains performance and load tests for the RhoSocial ActiveRecord library. These benchmarks measure and compare backend performance under standardized loads to ensure efficient operation.

## Purpose

Performance benchmarks are designed to:

- Measure query execution times
- Evaluate memory usage patterns
- Test concurrent access performance
- Compare different backend implementations
- Identify performance bottlenecks
- Ensure consistent performance across different database systems

## Structure

This directory contains backend-agnostic ActiveRecord benchmarks for CRUD, query, transaction, and mixin behavior. These shared benchmark categories use the same provider pattern as feature tests:

- the testsuite defines benchmark contexts, provider protocols, fixtures, workloads, and common test logic
- each backend repository implements the provider, schema, setup, teardown, seed data, model or backend configuration, and backend-specific differences
- each backend repository registers its provider in `tests/providers/registry.py`

The shared provider-backed benchmark categories are:

- `crud`
- `query`
- `transaction`
- `mixin`

`backend` is the exception. It is a contract-only category for direct `StorageBackend.execute()` and `execute_many()` benchmarks. The testsuite does not provide shared pytest tests or a provider interface for it, and backend repositories must not register `benchmark.backend.IBackendBenchmarkProvider`. Each backend maintains its own `tests/benchmark/backend/` files because SQL placeholders, DDL, insert id handling, and batch execution behavior differ across database implementations.

Future benchmark categories that can share workload and assertions across backends, such as FastAPI HTTP/database benchmarks, should be added as new provider-backed testsuite subdirectories instead of being copied into each backend repository.

## Usage

Backend developers should run these benchmarks to:

1. Validate that their implementation meets performance requirements
2. Compare their backend's performance against other implementations
3. Identify areas for optimization
4. Ensure consistent performance across different hardware and deployment configurations

Benchmark results should be documented and included in the backend's compatibility report.