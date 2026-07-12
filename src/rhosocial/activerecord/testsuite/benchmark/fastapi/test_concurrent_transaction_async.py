"""Asynchronous concurrent FastAPI transactional benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.fastapi.interfaces import (
    FASTAPI_CONTEXT_STRATEGY,
)
from rhosocial.activerecord.testsuite.benchmark.fastapi.test_concurrent_read_async import (
    assert_pool_stats,
)
from rhosocial.activerecord.testsuite.benchmark.fastapi.workloads import (
    concurrent_transactional_updates,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_fastapi_concurrent_transaction_async(benchmark, fastapi_async_context, fastapi_concurrent_rounds):
    """Benchmark concurrent transactional updates via FastAPI."""

    context, run_async = fastapi_async_context
    warmup = 0 if context.connection_strategy == FASTAPI_CONTEXT_STRATEGY else 1
    before = context.pool_stats().to_dict() if context.pool_stats else None
    result = benchmark.pedantic(
        lambda: run_async(concurrent_transactional_updates(context)),
        rounds=fastapi_concurrent_rounds,
        iterations=1,
        warmup_rounds=warmup,
    )
    after = context.pool_stats().to_dict() if context.pool_stats else None

    assert result["backend"] == context.backend_name
    assert result["scenario"] == context.scenario
    assert result["connection_strategy"] == context.connection_strategy
    assert result["requests"] > 0
    assert result["workers"] > 0
    assert len(result["final_ids"]) == result["workers"]
    assert context.concurrency > 0
    assert context.repeat > 0
    assert_pool_stats(context, before, after)
