# src/rhosocial/activerecord/testsuite/feature/cli/conftest.py
"""Pytest fixtures for the CLI feature tests."""

import pytest

from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY_SYNC = "feature.cli.ICLISyncProvider"
PROVIDER_KEY_ASYNC = "feature.cli.ICLIAsyncProvider"


def _provider_class(key):
    registry = get_provider_registry()
    return registry.get_provider(key)


def _scenarios(key):
    provider_class = _provider_class(key)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


SCENARIO_PARAMS_SYNC = _scenarios(PROVIDER_KEY_SYNC) or [
    pytest.param("default", marks=pytest.mark.skip(reason="No sync CLI scenarios found"))
]
SCENARIO_PARAMS_ASYNC = _scenarios(PROVIDER_KEY_ASYNC) or [
    pytest.param("default", marks=pytest.mark.skip(reason="No async CLI scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def cli_models(request):
    scenario = request.param
    provider_class = _provider_class(PROVIDER_KEY_SYNC)
    provider = provider_class()
    models = provider.setup_cli_models(scenario)
    yield models
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_cli_models(request):
    scenario = request.param
    provider_class = _provider_class(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    models = await provider.setup_cli_models(scenario)
    yield models
    await provider.cleanup_after_test(scenario)
