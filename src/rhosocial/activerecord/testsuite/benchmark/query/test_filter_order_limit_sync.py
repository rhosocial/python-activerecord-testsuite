"""Synchronous filter/order/limit query benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.query.workloads import filter_order_limit


@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_read
def test_filter_order_limit_sync(benchmark, query_sync_context):
    results = benchmark(filter_order_limit, query_sync_context.model_class)
    assert len(results) == 10
