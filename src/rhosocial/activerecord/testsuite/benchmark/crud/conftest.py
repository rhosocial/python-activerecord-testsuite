"""Pytest fixtures for CRUD benchmark scenarios."""
import asyncio

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.interfaces import (
    UnsupportedBenchmarkScenario,
)
from rhosocial.activerecord.testsuite.benchmark.registry import benchmarks

FEATURE = "crud"


def _scenarios():
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        return []
    return implementation.scenarios()


SCENARIO_PARAMS = _scenarios() or [
    pytest.param(
        "default", marks=pytest.mark.skip(reason="No CRUD benchmark implementation registered")
    )
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def crud_sync_context(request, benchmark_size):
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        pytest.skip("No CRUD benchmark implementation registered")
    scenario = request.param
    try:
        context = implementation.sync_setup(scenario, benchmark_size)
    except UnsupportedBenchmarkScenario as exc:
        pytest.skip(str(exc))
    if context is None:
        pytest.skip(f"CRUD sync benchmark is not supported for scenario {scenario!r}")
    yield context
    implementation.sync_teardown(scenario, context)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def crud_async_context(request, benchmark_size):
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        pytest.skip("No CRUD benchmark implementation registered")
    scenario = request.param
    loop = asyncio.new_event_loop()
    try:
        try:
            context = loop.run_until_complete(
                implementation.async_setup(scenario, benchmark_size)
            )
        except UnsupportedBenchmarkScenario as exc:
            pytest.skip(str(exc))
        if context is None:
            pytest.skip(f"CRUD async benchmark is not supported for scenario {scenario!r}")
        yield context, loop.run_until_complete
        loop.run_until_complete(implementation.async_teardown(scenario, context))
    finally:
        loop.close()
