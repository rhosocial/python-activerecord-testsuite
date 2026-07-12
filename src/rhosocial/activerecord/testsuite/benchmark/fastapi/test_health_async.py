"""Asynchronous FastAPI route benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.fastapi.interfaces import (
    FASTAPI_CONNECTION_STRATEGIES,
)
from rhosocial.activerecord.testsuite.benchmark.fastapi.workloads import health


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_fastapi_health_async(benchmark, fastapi_async_context):
    """Benchmark the FastAPI health check endpoint."""

    context, run_async = fastapi_async_context
    result = benchmark(lambda: run_async(health(context.client)))
    assert result["backend"] == context.backend_name
    assert result["scenario"] == context.scenario
    assert context.connection_strategy in FASTAPI_CONNECTION_STRATEGIES
