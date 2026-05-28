"""Synchronous delete CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import delete_one


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_delete_one_sync(benchmark, crud_sync_context):
    counter = {"value": 0}

    def delete_seed_row():
        counter["value"] += 1
        payload = make_user_payload(len(crud_sync_context.payloads) + counter["value"])
        instance = crud_sync_context.model_class(**payload)
        rows = instance.save()
        if rows != 1 or instance.id is None:
            raise AssertionError("delete benchmark could not prepare seed row")
        delete_one(crud_sync_context.model_class, instance.id)
        return instance.id

    deleted_id = benchmark(delete_seed_row)
    assert crud_sync_context.model_class.find_one(deleted_id) is None
