"""Asynchronous transaction bulk insert benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.transaction.workloads import (
    bulk_insert_transaction_async,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_transaction
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_bulk_insert_transaction_async(benchmark, transaction_async_context):
    context, run_async = transaction_async_context
    payloads = context.payloads[:10]
    inserted = benchmark(
        lambda: run_async(bulk_insert_transaction_async(context.model_class, payloads))
    )
    assert len(inserted) == 10
