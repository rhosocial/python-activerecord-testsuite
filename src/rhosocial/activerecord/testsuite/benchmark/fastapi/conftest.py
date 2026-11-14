"""Pytest fixtures for FastAPI benchmark scenarios."""
__parity__ = "async_only"

import asyncio

import pytest

from rhosocial.activerecord.testsuite.benchmark.fastapi.interfaces import (
    UnsupportedBenchmarkScenario,
)
from rhosocial.activerecord.testsuite.benchmark.registry import benchmarks

FEATURE = "fastapi"


def _scenario_strategy_params():
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        return []
    return [
        pytest.param((scenario, strategy), id=f"{scenario}-{strategy}")
        for scenario in implementation.scenarios()
        for strategy in implementation.connection_strategies()
    ]


SCENARIO_STRATEGY_PARAMS = _scenario_strategy_params() or [
    pytest.param(
        ("default", "context"),
        marks=pytest.mark.skip(reason="No FastAPI benchmark implementation registered"),
    )
]


@pytest.fixture(scope="function", params=SCENARIO_STRATEGY_PARAMS)
def fastapi_async_context(request, benchmark_size):
    implementation = benchmarks.get(FEATURE)
    if implementation is None:
        pytest.skip("No FastAPI benchmark implementation registered")
    scenario, connection_strategy = request.param
    loop = asyncio.new_event_loop()
    try:
        try:
            context = loop.run_until_complete(
                implementation.async_setup(
                    scenario, benchmark_size, connection_strategy
                )
            )
        except UnsupportedBenchmarkScenario as exc:
            pytest.skip(str(exc))
        if context is None:
            pytest.skip(
                f"FastAPI async benchmark is not supported for scenario {scenario!r}"
            )
        yield context, loop.run_until_complete
        loop.run_until_complete(implementation.async_teardown(scenario, context))
    finally:
        loop.close()
