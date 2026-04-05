# src/rhosocial/activerecord/testsuite/feature/basic/worker/conftest.py
"""
Pytest fixtures for WorkerPool tests with basic feature.

These fixtures provide Worker-specific configurations that allow tests
to verify WorkerPool integration with ActiveRecord CRUD operations.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
from rhosocial.activerecord.testsuite.core.protocols import WorkerTestProtocol

# Reuse the same provider key and scenario discovery as parent feature
PROVIDER_KEY = "feature.basic.IBasicProvider"


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
    Tests will be skipped if the provider doesn't implement the protocol.

    Returns:
        dict: Connection parameters containing:
            - backend_module: Module path for the backend class
            - backend_class_name: Name of the backend class
            - config_class_module: Module path for the config class
            - config_class_name: Name of the config class
            - config_kwargs: Dictionary of config constructor arguments
            - schema_sql: Optional SQL to create required tables
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Check if provider implements WorkerTestProtocol
    if not isinstance(provider, WorkerTestProtocol):
        pytest.skip("Provider does not implement WorkerTestProtocol")

    params = provider.get_worker_connection_params(scenario, fixture_type='user')

    yield params

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def user_class_for_worker(request):
    """
    Provides configured User model class and Worker connection parameters.

    This fixture sets up the model in the main process for verification,
    and provides connection parameters for Worker processes to create
    their own connections.

    Yields:
        dict: {
            'model': User model class (sync),
            'conn_params': Worker connection parameters dict
        }
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Setup User model in main process
    User = provider.setup_user_model(scenario)

    # Get Worker connection params if available
    conn_params = None
    if isinstance(provider, WorkerTestProtocol):
        conn_params = provider.get_worker_connection_params(scenario, fixture_type='user')

    yield {
        'model': User,
        'conn_params': conn_params
    }

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_user_class_for_worker(request):
    """
    Provides configured AsyncUser model class and Worker connection parameters.

    This fixture sets up the async model in the main process for verification,
    and provides connection parameters for Worker processes.

    Yields:
        dict: {
            'model': AsyncUser model class,
            'conn_params': Worker connection parameters dict
        }
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Setup AsyncUser model in main process
    AsyncUser = await provider.setup_async_user_model(scenario)

    # Get Worker connection params if available (use 'async_user' for async backend)
    conn_params = None
    if isinstance(provider, WorkerTestProtocol):
        conn_params = provider.get_worker_connection_params(scenario, fixture_type='async_user')

    yield {
        'model': AsyncUser,
        'conn_params': conn_params
    }

    await provider.cleanup_after_test_async(scenario)
