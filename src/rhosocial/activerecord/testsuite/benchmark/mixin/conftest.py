"""Pytest fixtures for mixin benchmark scenarios."""
import asyncio

import pytest

from rhosocial.activerecord.testsuite.benchmark.mixin.interfaces import (
    UnsupportedBenchmarkScenario,
)
from rhosocial.activerecord.testsuite.benchmark.registry import benchmarks

FEATURE = "mixin"


def _scenarios():
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        return []
    return implementation.scenarios()


SCENARIO_PARAMS = _scenarios() or [
    pytest.param(
        "default", marks=pytest.mark.skip(reason="No mixin benchmark implementation registered")
    )
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def mixin_sync_context(request, benchmark_size):
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        pytest.skip("No mixin benchmark implementation registered")
    scenario = request.param
    try:
        context = implementation.sync_setup(scenario, benchmark_size)
    except UnsupportedBenchmarkScenario as exc:
        pytest.skip(str(exc))
    if context is None:
        pytest.skip(f"Mixin sync benchmark is not supported for scenario {scenario!r}")
    yield context
    implementation.sync_teardown(scenario, context)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def mixin_async_context(request, benchmark_size):
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        pytest.skip("No mixin benchmark implementation registered")
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
            pytest.skip(f"Mixin async benchmark is not supported for scenario {scenario!r}")
        yield context, loop.run_until_complete
        loop.run_until_complete(implementation.async_teardown(scenario, context))
    finally:
        loop.close()
