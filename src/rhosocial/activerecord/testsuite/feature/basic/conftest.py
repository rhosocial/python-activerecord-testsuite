# src/rhosocial/activerecord/testsuite/feature/basic/conftest.py
"""
This file defines the pytest fixtures for the "basic" feature test group.

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

# The correct key for the provider is its short name string.
PROVIDER_KEY = "feature.basic.IBasicProvider"

def get_scenarios():
    """
    A helper function that runs during pytest's collection phase to discover
    all available test scenarios from the backend's registered provider.
    """
    # Dynamically get the registry and the provider for this test group.
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    if not provider_class:
        return []
    # Instantiate the provider and get the list of scenario names.
    return provider_class().get_test_scenarios()

# Discover the scenarios at module import time.
scenarios = get_scenarios()

# If no scenarios are found, create a single dummy parameter that will cause
# the tests to be skipped with a helpful message.
SCENARIO_PARAMS = scenarios if scenarios else [pytest.param("default", marks=pytest.mark.skip(reason="No testsuite scenarios found"))]

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def user_class(request):
    """
    A pytest fixture that provides a configured `User` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Ask the provider to set up the database and configure the User model for this scenario.
    model = provider.setup_user_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield model

    # After the test function finishes, the code below this line runs as a teardown.
    provider.cleanup_after_test(scenario)

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def type_case_class(request):
    """
    Provides a configured `TypeCase` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = provider.setup_type_case_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def type_test_model(request):
    """
    Provides a configured `TypeTestModel` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = provider.setup_type_test_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def validated_user_class(request):
    """
    Provides a configured `ValidatedFieldUser` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = provider.setup_validated_field_user_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def validated_user(request):
    """
    Provides a configured `ValidatedUser` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = provider.setup_validated_user_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def type_adapter_fixtures(request):
    """
    Provides fixtures for type adapter tests, including the model, backend,
    and a custom 'yes/no' adapter.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # The setup method returns a tuple: (Model, backend_instance)
    model = provider.setup_type_adapter_model_and_schema(scenario)
    yes_no_adapter = provider.get_yes_no_adapter()
    
    # Yield all resources needed by the tests
    yield model

    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def mapped_models_fixtures(request):
    """
    A pytest fixture that provides configured `MappedUser`, `MappedPost`,
    and `MappedComment` model classes for testing, parameterized by scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Ask the provider to set up the database and configure the Mapped models for this scenario.
    user_model, post_model, comment_model = provider.setup_mapped_models(scenario)

    # Yield the configured model classes as a tuple.
    yield user_model, post_model, comment_model

    # After the test function finishes, perform cleanup.
    provider.cleanup_after_test(scenario)

# Import async models
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncUser as AsyncUserModel,
    AsyncTypeCase as AsyncTypeCaseModel,
    AsyncValidatedUser as AsyncValidatedUserModel,
    AsyncTypeTestModel as AsyncTypeTestModel,
    AsyncValidatedFieldUser as AsyncValidatedFieldUserModel,
    AsyncTypeAdapterTest as AsyncTypeAdapterTestModel,
    AsyncYesOrNoBooleanAdapter as AsyncYesOrNoBooleanAdapter,
    AsyncMappedUser as AsyncMappedUserModel,
    AsyncMappedPost as AsyncMappedPostModel,
    AsyncMappedComment as AsyncMappedCommentModel,
    AsyncColumnMappingModel as AsyncColumnMappingModel,
    AsyncMixedAnnotationModel as AsyncMixedAnnotationModel
)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def mixed_models_fixtures(request):
    """
    A pytest fixture that provides configured models with mixed annotations
    (`ColumnMappingModel`, `MixedAnnotationModel`) for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # The provider's setup method returns a tuple of configured models
    models = provider.setup_mixed_models(scenario)

    yield models

    # After the test function finishes, perform cleanup.
    provider.cleanup_after_test(scenario)


# --- Async Fixtures ---

@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_user_class(request):
    """
    A pytest fixture that provides an async-configured `AsyncUser` model class for testing.
    It is parameterized to run for each available scenario.
    It also handles the async setup and teardown for each test.
    """
    # `request.param` holds the current scenario name (e.g., "memory", "file").
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Ask the provider to set up the database and configure the AsyncUser model for this scenario.
    model = await provider.setup_async_user_model(scenario)

    # `yield` passes the configured model class to the test function.
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    # After the test function finishes, the code below this line runs as a teardown.
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_type_case_class(request):
    """
    Provides an async-configured `AsyncTypeCase` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = await provider.setup_async_type_case_model(scenario)
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_validated_user_class(request):
    """
    Provides an async-configured `AsyncValidatedUser` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = await provider.setup_async_validated_user_model(scenario)
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_type_test_model(request):
    """
    Provides an async-configured `AsyncTypeTestModel` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = await provider.setup_async_type_test_model(scenario)
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_validated_field_user_class(request):
    """
    Provides an async-configured `AsyncValidatedFieldUser` model class for each scenario."""
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    model = await provider.setup_async_validated_field_user_model(scenario)
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_mapped_models_fixtures(request):
    """
    A pytest fixture that provides async-configured `AsyncMappedUser`, `AsyncMappedPost`,
    and `AsyncMappedComment` model classes for testing, parameterized by scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # Ask the provider to set up the database and configure the AsyncMapped models for this scenario.
    user_model, post_model, comment_model = await provider.setup_async_mapped_models(scenario)

    # Yield the configured model classes as a tuple.
    yield user_model, post_model, comment_model

    # After the test function finishes, perform async cleanup.
    # Determine which model has the backend to disconnect
    backend_to_close = user_model.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_mixed_models_fixtures(request):
    """
    Provides async-configured models with mixed annotations
    (`AsyncColumnMappingModel`, `AsyncMixedAnnotationModel`) for testing.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # The provider's setup method returns a tuple of configured models
    models = await provider.setup_async_mixed_models(scenario)

    yield models

    # After the test function finishes, perform async cleanup.
    # Determine which model has the backend to disconnect
    backend_to_close = models[0].__backend__  # Assuming first model has the backend
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_type_adapter_fixtures(request):
    """
    Provides async fixtures for type adapter tests, including the async model, backend,
    and a custom "yes/no" adapter.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()

    # The setup method returns an async model
    model = await provider.setup_async_type_adapter_model_and_schema(scenario)

    # Yield all resources needed by the tests
    yield model

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = model.__backend__
    await backend_to_close.disconnect()

    await provider.cleanup_after_test_async(scenario)
