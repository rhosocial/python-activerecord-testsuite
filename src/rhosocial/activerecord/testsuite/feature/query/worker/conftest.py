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
PROVIDER_KEY_SYNC = "feature.query.IQuerySyncProvider"
PROVIDER_KEY_ASYNC = "feature.query.IQueryAsyncProvider"


def get_scenarios_sync():
    """
    Discover available test scenarios from the backend's registered provider.
    """
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


def get_scenarios_async():
    """
    Discover available test scenarios from the backend's registered provider.
    """
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios_sync = get_scenarios_sync()
scenarios_async = get_scenarios_async()

# If no scenarios are found, create a skip marker
SCENARIO_PARAMS_SYNC = scenarios_sync if scenarios_sync else [
    pytest.param("default", marks=pytest.mark.skip(reason="No testsuite scenarios found"))
]
SCENARIO_PARAMS_ASYNC = scenarios_async if scenarios_async else [
    pytest.param("default", marks=pytest.mark.skip(reason="No testsuite scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def worker_connection_params(request):
    """
    Get serializable connection parameters for Worker processes.

    Provider must implement WorkerTestProtocol for this fixture to work.

    Returns:
        dict: Connection parameters for Worker processes
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    if not isinstance(provider, WorkerTestProtocol):
        pytest.skip("Provider does not implement WorkerTestProtocol")

    params = provider.get_worker_connection_params(scenario, fixture_type='order')

    yield params

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
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
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
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


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
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
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()

    AsyncUser, AsyncOrder, AsyncOrderItem = await provider.setup_order_fixtures(scenario)

    conn_params = None
    if isinstance(provider, WorkerTestProtocol):
        conn_params = provider.get_worker_connection_params(scenario, fixture_type='async_order')

    yield {
        'models': (AsyncUser, AsyncOrder, AsyncOrderItem),
        'conn_params': conn_params
    }

    await provider.cleanup_after_test(scenario)
