"""Asynchronous filter/order/limit query benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.query.workloads import filter_order_limit_async


@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_filter_order_limit_async(benchmark, query_async_context):
    context, run_async = query_async_context
    results = benchmark(lambda: run_async(filter_order_limit_async(context.model_class)))
    assert len(results) == 10
