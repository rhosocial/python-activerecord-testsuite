"""Asynchronous FastAPI write benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.fastapi.workloads import create_user


@pytest.mark.benchmark
@pytest.mark.benchmark_fastapi
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_fastapi_create_user_async(benchmark, fastapi_async_context):
    context, run_async = fastapi_async_context
    counter = {"value": 0}

    def create_row():
        counter["value"] += 1
        payload = make_user_payload(len(context.payloads) + counter["value"])
        return run_async(create_user(context.client, payload))

    result = benchmark(create_row)
    assert result["username"] == f"bench_user_{len(context.payloads) + counter['value']}"
