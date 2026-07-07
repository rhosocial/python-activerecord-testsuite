"""Asynchronous FastAPI read benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.fastapi.workloads import (
    get_user,
    list_users,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_fastapi_get_user_async(benchmark, fastapi_async_context):
    context, run_async = fastapi_async_context
    record_id = context.record_ids[len(context.record_ids) // 2]
    result = benchmark(lambda: run_async(get_user(context.client, record_id)))
    assert result["id"] == record_id


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_fastapi_list_users_async(benchmark, fastapi_async_context):
    context, run_async = fastapi_async_context
    limit = min(20, len(context.record_ids))
    result = benchmark(lambda: run_async(list_users(context.client, limit)))
    assert len(result) <= limit
