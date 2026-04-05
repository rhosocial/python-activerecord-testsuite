# src/rhosocial/activerecord/testsuite/feature/query/worker/conftest.py
"""
Pytest fixtures for WorkerPool tests with query feature.

These fixtures provide Worker-specific configurations that allow tests
to verify WorkerPool integration with ActiveRecord query operations.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
from rhosocial.activerecord.testsuite.core.protocols import WorkerTestProtocol

# Reuse the same provider key and scenario discovery as parent feature
PROVIDER_KEY = "feature.query.IQueryProvider"


def get_scenarios():
    """
    Discover available test scenarios from the backend's registered provider.
    """
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios = get_scenarios()

# If no scenarios are found, create a skip marker
SCENARIO_PARAMS = scenarios if scenarios else [
    pytest.param("default", marks=pytest.mark.skip(reason="No testsuite scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def worker_connection_params(request):
    """
    Get serializable connection parameters for Worker processes.

    Provider must implement WorkerTestProtocol for this fixture to work.

    Returns:
        dict: Connection parameters for Worker processes
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    if not isinstance(provider, WorkerTestProtocol):
        pytest.skip("Provider does not implement WorkerTestProtocol")

    params = provider.get_worker_connection_params(scenario, fixture_type='order')

    yield params

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def order_fixtures_for_worker(request):
    """
    Provides Order-related models and Worker connection parameters.

    Yields:
        dict: {
            'models': (User, Order, OrderItem) tuple,
            'conn_params': Worker connection parameters dict
        }
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    User, Order, OrderItem = provider.setup_order_fixtures(scenario)

    conn_params = None
    if isinstance(provider, WorkerTestProtocol):
        conn_params = provider.get_worker_connection_params(scenario, fixture_type='order')

    yield {
        'models': (User, Order, OrderItem),
        'conn_params': conn_params
    }

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_order_fixtures_for_worker(request):
    """
    Provides async Order-related models and Worker connection parameters.

    Yields:
        dict: {
            'models': (AsyncUser, AsyncOrder, AsyncOrderItem) tuple,
            'conn_params': Worker connection parameters dict
        }
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    AsyncUser, AsyncOrder, AsyncOrderItem = await provider.setup_async_order_fixtures(scenario)

    conn_params = None
    if isinstance(provider, WorkerTestProtocol):
        conn_params = provider.get_worker_connection_params(scenario, fixture_type='async_order')

    yield {
        'models': (AsyncUser, AsyncOrder, AsyncOrderItem),
        'conn_params': conn_params
    }

    await provider.cleanup_after_test_async(scenario)
