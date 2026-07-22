# src/rhosocial/activerecord/testsuite/feature/basic/transaction/conftest.py
"""
Pytest fixtures for transaction API black-box tests.

Reuses IBasicConnectionProvider when available to keep provider surface
minimal. Backend providers that need different setup can implement
ITransactionBasicProvider instead; this conftest prefers the dedicated
provider and falls back to BasicConnectionProvider.
"""
import logging
import pytest

from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY = "feature.basic.transaction.ITransactionBasicProvider"
FALLBACK_KEY = "feature.basic.connection.IBasicConnectionProvider"

logger = logging.getLogger(__name__)


def _resolve_provider():
    registry = get_provider_registry()
    provider_class = registry.get_provider(PROVIDER_KEY)
    if provider_class:
        return provider_class, "dedicated"
    fallback_class = registry.get_provider(FALLBACK_KEY)
    if fallback_class:
        return fallback_class, "fallback"
    return None, None


def get_scenarios():
    provider_class, _ = _resolve_provider()
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios = get_scenarios()
SCENARIO_PARAMS = scenarios if scenarios else [
    pytest.param("default", marks=pytest.mark.skip(reason="No transaction basic provider found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def sync_pool_and_model(request):
    provider_class, kind = _resolve_provider()
    provider = provider_class()
    scenario = request.param
    pool, model = provider.setup_sync_pool_and_model(scenario)
    yield pool, model
    provider.cleanup_sync(scenario, pool)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_pool_and_model(request):
    provider_class, _ = _resolve_provider()
    provider = provider_class()
    scenario = request.param
    pool, model = await provider.setup_async_pool_and_model(scenario)
    yield pool, model
    await provider.cleanup_async(scenario, pool)
