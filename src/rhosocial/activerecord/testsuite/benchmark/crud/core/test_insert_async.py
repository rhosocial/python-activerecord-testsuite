"""Asynchronous insert CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import insert_one_async


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_insert_one_async(benchmark, crud_async_context):
    context, run_async = crud_async_context
    payload = make_user_payload(len(context.payloads) + 1)
    inserted = benchmark(lambda: run_async(insert_one_async(context.model_class, payload)))
    found = run_async(context.model_class.find_one(inserted.id))
    assert found is not None
    assert found.username == payload["username"]
    assert found.notes == payload["notes"]
