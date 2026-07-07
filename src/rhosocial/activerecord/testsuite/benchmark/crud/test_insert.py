"""Synchronous insert CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import insert_one


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_insert_one(benchmark, crud_sync_context):
    payload = make_user_payload(len(crud_sync_context.payloads) + 1)
    inserted = benchmark(insert_one, crud_sync_context.model_class, payload)
    found = crud_sync_context.model_class.find_one(inserted.id)
    assert found is not None
    assert found.username == payload["username"]
    assert found.notes == payload["notes"]
