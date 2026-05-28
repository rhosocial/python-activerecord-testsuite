"""Asynchronous count query benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.query.workloads import count_active_async


@pytest.mark.benchmark
@pytest.mark.benchmark_query
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_count_active_async(benchmark, query_async_context):
    context, run_async = query_async_context
    count = benchmark(lambda: run_async(count_active_async(context.model_class)))
    assert count > 0
