"""Asynchronous backend execute_many benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.backend.workloads import execute_many_insert_async


@pytest.mark.benchmark
@pytest.mark.benchmark_backend
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_backend_execute_many_insert_async(benchmark, backend_async_context):
    context, run_async = backend_async_context
    counter = {"value": 0}
    batch_size = len(context.payloads)

    async def insert_rows():
        start = len(context.payloads) + counter["value"] * batch_size
        counter["value"] += 1
        payloads = [make_user_payload(start + offset) for offset in range(batch_size)]
        return await execute_many_insert_async(context, payloads)

    affected_rows = benchmark(lambda: run_async(insert_rows()))
    assert affected_rows == batch_size
