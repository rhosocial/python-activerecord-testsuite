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

This directory contains backend-agnostic ActiveRecord benchmarks for CRUD, query, transaction, and mixin behavior. Direct `StorageBackend.execute()` benchmarks are intentionally maintained in each backend repository, because insert result handling and SQL details differ across database implementations.

## Usage

Backend developers should run these benchmarks to:

1. Validate that their implementation meets performance requirements
2. Compare their backend's performance against other implementations
3. Identify areas for optimization
4. Ensure consistent performance across different hardware and deployment configurations

Benchmark results should be documented and included in the backend's compatibility report.