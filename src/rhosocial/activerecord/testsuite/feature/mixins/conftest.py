# src/rhosocial/activerecord/testsuite/feature/mixins/conftest.py
"""
This file defines the pytest fixtures for the "mixins" feature test group.

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

PROVIDER_KEY_SYNC = "feature.mixins.IMixinsSyncProvider"
PROVIDER_KEY_ASYNC = "feature.mixins.IMixinsAsyncProvider"


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
    pytest.param("default", marks=pytest.mark.skip(reason="No sync mixins testsuite scenarios found"))
]
SCENARIO_PARAMS_ASYNC = scenarios_async if scenarios_async else [
    pytest.param("default", marks=pytest.mark.skip(reason="No async mixins testsuite scenarios found"))
]


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def timestamped_post_model(request):
    """
    A pytest fixture that provides a configured `TimestampedPost` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the TimestampedPost model for this scenario.
    Model = provider.setup_timestamped_post_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_timestamped_post_model(request):
    """
    An async pytest fixture that provides a configured `AsyncTimestampedPost` model class for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    Model = await provider.setup_timestamped_post_model(scenario)
    yield Model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def versioned_product_model(request):
    """
    A pytest fixture that provides a configured `VersionedProduct` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the VersionedProduct model for this scenario.
    Model = provider.setup_versioned_product_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_versioned_product_model(request):
    """
    An async pytest fixture that provides a configured `AsyncVersionedProduct` model class for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    Model = await provider.setup_versioned_product_model(scenario)
    yield Model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def task_model(request):
    """
    A pytest fixture that provides a configured `Task` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the Task model for this scenario.
    Model = provider.setup_task_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_task_model(request):
    """
    An async pytest fixture that provides a configured `AsyncTask` model class for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    Model = await provider.setup_task_model(scenario)
    yield Model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def combined_article_model(request):
    """
    A pytest fixture that provides a configured `CombinedArticle` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()

    # Ask the provider to set up the database and configure the CombinedArticle model for this scenario.
    Model = provider.setup_combined_article_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield Model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_combined_article_model(request):
    """
    An async pytest fixture that provides a configured `AsyncCombinedArticle` model class for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    Model = await provider.setup_combined_article_model(scenario)
    yield Model
    await provider.cleanup_after_test(scenario)
