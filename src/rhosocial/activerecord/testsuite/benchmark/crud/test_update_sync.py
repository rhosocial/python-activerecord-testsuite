"""Synchronous update CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import update_one


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_update_one_sync(benchmark, crud_sync_context):
    counter = {"value": 0}

    def update_seed_row():
        counter["value"] += 1
        payload = make_user_payload(len(crud_sync_context.payloads) + counter["value"])
        instance = crud_sync_context.model_class(**payload)
        rows = instance.save()
        if rows != 1 or instance.id is None:
            raise AssertionError("update benchmark could not prepare seed row")
        return update_one(crud_sync_context.model_class, instance.id, str(counter["value"]))

    updated = benchmark(update_seed_row)
    assert updated.username == f"bench_updated_{counter['value']}"
