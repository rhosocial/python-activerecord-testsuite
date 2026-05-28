"""Pytest fixtures for CRUD benchmark scenarios."""

import asyncio

import pytest

from rhosocial.activerecord.testsuite.benchmark.crud.interfaces import (
    UnsupportedBenchmarkScenario,
)
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY = "benchmark.crud.ICrudBenchmarkProvider"


def _get_provider_class():
    provider_registry = get_provider_registry()
    return provider_registry.get_provider(PROVIDER_KEY)


def _get_scenarios():
    provider_class = _get_provider_class()
    if not provider_class:
        return []
    return provider_class().get_benchmark_scenarios()


SCENARIO_PARAMS = _get_scenarios() or [
    pytest.param("default", marks=pytest.mark.skip(reason="No CRUD benchmark provider found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def crud_sync_context(request, benchmark_size):
    provider_class = _get_provider_class()
    if not provider_class:
        pytest.skip("No CRUD benchmark provider found")
    provider = provider_class()
    scenario = request.param
    try:
        context = provider.setup_benchmark_sync(scenario, benchmark_size)
    except UnsupportedBenchmarkScenario as exc:
        pytest.skip(str(exc))
    if context is None:
        pytest.skip(f"CRUD sync benchmark is not supported for scenario {scenario!r}")
    yield context
    provider.teardown_benchmark_sync(scenario, context)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def crud_async_context(request, benchmark_size):
    provider_class = _get_provider_class()
    if not provider_class:
        pytest.skip("No CRUD benchmark provider found")
    provider = provider_class()
    scenario = request.param
    loop = asyncio.new_event_loop()
    try:
        try:
            context = loop.run_until_complete(
                provider.setup_benchmark_async(scenario, benchmark_size)
            )
        except UnsupportedBenchmarkScenario as exc:
            pytest.skip(str(exc))
        if context is None:
            pytest.skip(f"CRUD async benchmark is not supported for scenario {scenario!r}")
        yield context, loop.run_until_complete
        loop.run_until_complete(provider.teardown_benchmark_async(scenario, context))
    finally:
        loop.close()
