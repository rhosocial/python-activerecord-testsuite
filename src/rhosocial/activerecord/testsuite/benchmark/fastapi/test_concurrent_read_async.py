"""Asynchronous concurrent FastAPI read benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.fastapi.interfaces import (
    FASTAPI_CONTEXT_STRATEGY,
    FASTAPI_POOL_NEAR_MAX_STRATEGY,
    FASTAPI_POOL_NEAR_MIN_STRATEGY,
    FASTAPI_POOL_OVER_MAX_STRATEGY,
)
from rhosocial.activerecord.testsuite.benchmark.fastapi.workloads import (
    concurrent_get_users_by_email,
)


def assert_pool_stats(context, before, after):
    if after is None:
        return

    assert before is not None
    assert after["total_timeouts"] == 0
    assert after["total_errors"] == 0
    assert after["current_in_use"] == 0

    if not context.pool_config:
        return

    min_size = context.pool_config["min_size"]
    max_size = context.pool_config["max_size"]
    assert after["total_created"] <= max_size

    if context.pool_connection_mode != "persistent":
        return

    if context.connection_strategy == FASTAPI_POOL_NEAR_MIN_STRATEGY:
        assert after["total_created"] == min_size
    elif context.connection_strategy == FASTAPI_POOL_NEAR_MAX_STRATEGY:
        assert min_size <= after["total_created"] <= max_size
        assert after["total_created"] > before["total_created"]
    elif context.connection_strategy == FASTAPI_POOL_OVER_MAX_STRATEGY:
        assert after["total_created"] == max_size


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_fastapi_concurrent_read_async(benchmark, fastapi_async_context, fastapi_concurrent_rounds):
    """Benchmark concurrent user lookups by email via FastAPI."""

    context, run_async = fastapi_async_context
    warmup = 0 if context.connection_strategy == FASTAPI_CONTEXT_STRATEGY else 1
    before = context.pool_stats().to_dict() if context.pool_stats else None
    result = benchmark.pedantic(
        lambda: run_async(concurrent_get_users_by_email(context)),
        rounds=fastapi_concurrent_rounds,
        iterations=1,
        warmup_rounds=warmup,
    )
    after = context.pool_stats().to_dict() if context.pool_stats else None

    assert result["backend"] == context.backend_name
    assert result["scenario"] == context.scenario
    assert result["connection_strategy"] == context.connection_strategy
    assert result["requests"] > 0
    assert result["unique_emails"] > 0
    assert context.concurrency > 0
    assert context.repeat > 0
    assert_pool_stats(context, before, after)
