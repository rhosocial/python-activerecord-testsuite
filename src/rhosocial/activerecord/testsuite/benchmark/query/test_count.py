"""Synchronous count query benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.query.workloads import count_active


@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_read
def test_count_active(benchmark, query_sync_context):
    count = benchmark(count_active, query_sync_context.model_class)
    assert count > 0
