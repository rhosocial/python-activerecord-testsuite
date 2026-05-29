"""Asynchronous concurrent FastAPI transactional benchmarks."""

import pytest

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
def test_fastapi_concurrent_transaction_async(benchmark, fastapi_async_context):
    context, run_async = fastapi_async_context
    before = context.pool_stats().to_dict() if context.pool_stats else None
    result = benchmark.pedantic(
        lambda: run_async(concurrent_transactional_updates(context)),
        rounds=1,
        iterations=1,
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
