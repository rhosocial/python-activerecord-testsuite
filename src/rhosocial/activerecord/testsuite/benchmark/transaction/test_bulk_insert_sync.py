"""Synchronous transaction bulk insert benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.transaction.workloads import (
    bulk_insert_transaction,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_bulk_insert_transaction_sync(benchmark, transaction_sync_context):
    payloads = transaction_sync_context.payloads[:10]
    inserted = benchmark(
        bulk_insert_transaction,
        transaction_sync_context.model_class,
        payloads,
    )
    assert len(inserted) == 10
