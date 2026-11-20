"""Asynchronous delete CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import delete_one_async


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_delete_one_async(benchmark, crud_async_context):
    context, run_async = crud_async_context
    counter = {"value": 0}

    async def delete_seed_row():
        counter["value"] += 1
        payload = make_user_payload(len(context.payloads) + counter["value"])
        instance = context.model_class(**payload)
        rows = await instance.save()
        if rows != 1 or instance.id is None:
            raise AssertionError("async delete benchmark could not prepare seed row")
        await delete_one_async(context.model_class, instance.id)
        return instance.id

    deleted_id = benchmark(lambda: run_async(delete_seed_row()))
    assert run_async(context.model_class.find_one(deleted_id)) is None
