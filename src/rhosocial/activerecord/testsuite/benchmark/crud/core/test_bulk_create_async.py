"""Asynchronous bulk_create vs sequential insert benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payloads
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import (
    bulk_create_batch_async,
    insert_sequential_async,
)

BATCH_SIZE = 1000


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_sequential_insert_async(benchmark, crud_async_context):
    context, run_async = crud_async_context
    payloads = make_user_payloads(BATCH_SIZE)
    inserted = benchmark(
        lambda: run_async(insert_sequential_async(context.model_class, payloads))
    )
    assert len(inserted) == BATCH_SIZE


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_bulk_create_async(benchmark, crud_async_context):
    context, run_async = crud_async_context
    payloads = make_user_payloads(BATCH_SIZE)
    result = benchmark(
        lambda: run_async(bulk_create_batch_async(context.model_class, payloads))
    )
    assert len(result) == BATCH_SIZE
