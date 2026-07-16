# src/rhosocial/activerecord/testsuite/feature/events/conftest.py
"""
This file defines the pytest fixtures for the "events" feature test group.

Fixtures are a core concept in pytest. They are functions that provide a fixed
baseline state or data for tests. In this case, they provide fully configured
ActiveRecord model classes that are ready to be used in tests.

The key mechanism here is `pytest.fixture` parameterization. The fixtures are
parameterized by the list of "scenarios" provided by the backend's provider.
This causes pytest to run each test that uses one of these fixtures multiple times,
once for each database configuration (scenario) the backend supports.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY_SYNC = "feature.events.IEventsSyncProvider"
PROVIDER_KEY_ASYNC = "feature.events.IEventsAsyncProvider"


def get_scenarios_sync():
    """
    A helper function that runs during pytest's collection phase to discover
    all available test scenarios from the backend's registered provider.
    """
    # Dynamically get the registry and the provider for this test group.
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    if not provider_class:
        return []
    # Instantiate the provider and get the list of scenario names.
    return provider_class().get_test_scenarios()


def get_scenarios_async():
    """
    A helper function that runs during pytest's collection phase to discover
    all available test scenarios from the backend's registered provider.
    """
    # Dynamically get the registry and the provider for this test group.
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    if not provider_class:
        return []
    # Instantiate the provider and get the list of scenario names.
    return provider_class().get_test_scenarios()


# Discover the scenarios at module import time.
scenarios_sync = get_scenarios_sync()
scenarios_async = get_scenarios_async()

# If no scenarios are found, create a single dummy parameter that will cause
# the tests to be skipped with a helpful message.
SCENARIO_PARAMS_SYNC = scenarios_sync if scenarios_sync else [
    pytest.param("default", marks=pytest.mark.skip(reason="No sync events testsuite scenarios found"))
]
SCENARIO_PARAMS_ASYNC = scenarios_async if scenarios_async else [
    pytest.param("default", marks=pytest.mark.skip(reason="No async events testsuite scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def event_model(request):
    """
    A pytest fixture that provides a configured `EventTestModel` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the EventTestModel for this scenario.
    Model = provider.setup_event_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_event_model(request):
    """
    An async pytest fixture that provides a configured `AsyncEventTestModel` model class for testing.
    It is parameterized to run for each available scenario.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the AsyncEventTestModel for this scenario.
    Model = await provider.setup_event_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def event_tracking_model(request):
    """
    A pytest fixture that provides a configured `EventTrackingModel` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the EventTrackingModel for this scenario.
    # We'll need to add a specific method for this in the provider
    Model = provider.setup_event_tracking_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_event_tracking_model(request):
    """
    An async pytest fixture that provides a configured `AsyncEventTrackingModel` model class for testing.
    It is parameterized to run for each available scenario.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the AsyncEventTrackingModel for this scenario.
    Model = await provider.setup_event_tracking_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    await provider.cleanup_after_test(scenario)
