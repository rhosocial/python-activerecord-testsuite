"""Synchronous backend execute_many benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.backend.workloads import execute_many_insert


@pytest.mark.benchmark
@pytest.mark.benchmark_backend
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_backend_execute_many_insert_sync(benchmark, backend_sync_context):
    counter = {"value": 0}
    batch_size = len(backend_sync_context.payloads)

    def insert_rows():
        start = len(backend_sync_context.payloads) + counter["value"] * batch_size
        counter["value"] += 1
        payloads = [make_user_payload(start + offset) for offset in range(batch_size)]
        return execute_many_insert(backend_sync_context, payloads)

    affected_rows = benchmark(insert_rows)
    assert affected_rows == batch_size
