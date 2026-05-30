"""Synchronous bulk_create vs sequential insert benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payloads
from rhosocial.activerecord.testsuite.benchmark.crud.workloads import (
    bulk_create_batch,
    insert_sequential,
)

BATCH_SIZE = 50


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_sequential_insert_sync(benchmark, crud_sync_context):
    payloads = make_user_payloads(BATCH_SIZE)
    inserted = benchmark(insert_sequential, crud_sync_context.model_class, payloads)
    assert len(inserted) == BATCH_SIZE


@pytest.mark.benchmark
@pytest.mark.benchmark_crud
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_bulk_create_sync(benchmark, crud_sync_context):
    payloads = make_user_payloads(BATCH_SIZE)
    result = benchmark(bulk_create_batch, crud_sync_context.model_class, payloads)
    assert len(result) == BATCH_SIZE
