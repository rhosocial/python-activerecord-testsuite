"""Synchronous query CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.workloads import find_one


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_read
def test_find_one_sync(benchmark, crud_sync_context):
    record_id = crud_sync_context.record_ids[len(crud_sync_context.record_ids) // 2]
    found = benchmark(find_one, crud_sync_context.model_class, record_id)
    assert found.id == record_id
