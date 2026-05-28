"""Asynchronous timestamp mixin benchmarks."""

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.fixtures.data import make_user_payload
from rhosocial.activerecord.testsuite.benchmark.mixin.workloads import (
    timestamp_insert_async,
    timestamp_update_async,
)


@pytest.mark.benchmark
@pytest.mark.benchmark_mixin
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_timestamp_insert_async(benchmark, mixin_async_context):
    context, run_async = mixin_async_context
    payload = dict(context.payloads[0])
    payload["username"] = "bench_timestamp_insert_async"
    inserted = benchmark(lambda: run_async(timestamp_insert_async(context.model_class, payload)))
    assert inserted.created_at is not None
    assert inserted.updated_at is not None


@pytest.mark.benchmark
@pytest.mark.benchmark_mixin
@pytest.mark.benchmark_async
@pytest.mark.benchmark_write
def test_timestamp_update_async(benchmark, mixin_async_context):
    context, run_async = mixin_async_context
    counter = {"value": 0}

    async def update_seed_row():
        counter["value"] += 1
        payload = make_user_payload(len(context.payloads) + counter["value"])
        instance = context.model_class(**payload)
        rows = await instance.save()
        if rows != 1 or instance.id is None:
            raise AssertionError("async timestamp update benchmark could not prepare seed row")
        return await timestamp_update_async(
            context.model_class,
            instance.id,
            str(counter["value"]),
        )

    updated = benchmark(lambda: run_async(update_seed_row()))
    assert updated.username == f"bench_timestamp_{counter['value']}"
