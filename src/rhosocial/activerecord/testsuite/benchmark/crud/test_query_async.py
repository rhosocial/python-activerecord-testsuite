"""Asynchronous query CRUD benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.workloads import find_one_async


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_async
@pytest.mark.benchmark_read
def test_find_one_async(benchmark, crud_async_context):
    context, run_async = crud_async_context
    record_id = context.record_ids[len(context.record_ids) // 2]
    found = benchmark(lambda: run_async(find_one_async(context.model_class, record_id)))
    assert found.id == record_id
