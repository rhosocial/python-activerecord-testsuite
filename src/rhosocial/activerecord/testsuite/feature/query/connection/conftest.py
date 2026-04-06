# src/rhosocial/activerecord/testsuite/feature/query/connection/conftest.py
"""
Pytest fixtures for query connection pool context awareness tests.

This module provides fixtures that use the IQueryConnectionProvider interface
to set up connection pools and models for query testing.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY = "feature.query.connection.IQueryConnectionProvider"


def get_scenarios():
    """Discover available test scenarios from the backend provider."""
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios = get_scenarios()
SCENARIO_PARAMS = scenarios if scenarios else [
    pytest.param("default", marks=pytest.mark.skip(reason="No IQueryConnectionProvider found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def sync_pool_and_model(request):
    """
    Provides a sync connection pool and model for query context tests.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    pool, model = provider.setup_sync_pool_and_model(scenario)
    yield pool, model
    provider.cleanup_sync(scenario, pool)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_pool_and_model(request):
    """
    Provides an async connection pool and model for query context tests.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    pool, model = await provider.setup_async_pool_and_model(scenario)
    yield pool, model
    await provider.cleanup_async(scenario, pool)
