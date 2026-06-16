# src/rhosocial/activerecord/testsuite/feature/composite_pk/conftest.py
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY = "feature.composite_pk.ICompositePKProvider"


def get_scenarios():
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios = get_scenarios()
SCENARIO_PARAMS = scenarios if scenarios else [
    pytest.param("default", marks=pytest.mark.skip(reason="No testsuite scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def order_item_class(request):
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_order_item_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def order_class(request):
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_order_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def store_inventory_class(request):
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_store_inventory_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_order_item_class(request):
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = await provider.setup_async_order_item_model(scenario)
    yield model
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_order_class(request):
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = await provider.setup_async_order_model(scenario)
    yield model
    await provider.cleanup_after_test_async(scenario)
