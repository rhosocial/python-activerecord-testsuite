"""Synchronous timestamp mixin benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.mixin.workloads import (
    timestamp_insert,
    timestamp_update,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_mixin
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_timestamp_insert_sync(benchmark, mixin_sync_context):
    payload = dict(mixin_sync_context.payloads[0])
    payload["username"] = "bench_timestamp_insert_sync"
    inserted = benchmark(timestamp_insert, mixin_sync_context.model_class, payload)
    assert inserted.created_at is not None
    assert inserted.updated_at is not None


@pytest.mark.benchmark
@pytest.mark.benchmark_mixin
@pytest.mark.benchmark_sync
@pytest.mark.benchmark_write
def test_timestamp_update_sync(benchmark, mixin_sync_context):
    counter = {"value": 0}

    def update_seed_row():
        counter["value"] += 1
        payload = make_user_payload(len(mixin_sync_context.payloads) + counter["value"])
        instance = mixin_sync_context.model_class(**payload)
        rows = instance.save()
        if rows != 1 or instance.id is None:
            raise AssertionError("timestamp update benchmark could not prepare seed row")
        return timestamp_update(
            mixin_sync_context.model_class,
            instance.id,
            str(counter["value"]),
        )

    updated = benchmark(update_seed_row)
    assert updated.username == f"bench_timestamp_{counter['value']}"
