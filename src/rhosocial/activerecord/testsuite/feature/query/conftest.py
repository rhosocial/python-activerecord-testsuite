# src/rhosocial/activerecord/testsuite/feature/query/conftest.py
"""
This file defines the pytest fixtures for the "query" feature test group.

Fixtures are a core concept in pytest. They are functions that provide a fixed
baseline state or data for tests. In this case, they provide fully configured
ActiveRecord model classes that are ready to be used in tests.

The key mechanism here is `pytest.fixture` parameterization. The fixtures are
parameterized by the list of "scenarios" provided by the backend's provider.
This causes pytest to run each test that uses one of these fixtures multiple times,
once for each database configuration (scenario) the backend supports.

DESIGN PRINCIPLE: Synchronous and Asynchronous Equivalence
---------------------------------------------------------
Considering that the framework itself is designed with complete equivalence
between synchronous and asynchronous operations, to fulfill this commitment,
all tests under this directory also maintain synchronous/asynchronous equivalence.
This means that for every synchronous feature, there is an equivalent asynchronous
counterpart. Therefore, the design principle for each test file and fixture is
functional equivalence. The schemas corresponding to fixture classes should also
be identical to ensure parity between sync and async testing environments.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry


def get_scenarios():
    """
    A helper function that runs during pytest's collection phase to discover
    all available test scenarios from the backend's registered provider.
    """
    # Dynamically get the registry and the provider for this test group.
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
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
def order_fixtures(request):
    """
    A pytest fixture that provides configured (User, Order, OrderItem) model classes
    for testing complex queries with related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    User, Order, OrderItem = provider.setup_order_fixtures(scenario)

    yield User, Order, OrderItem

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def blog_fixtures(request):
    """
    A pytest fixture that provides configured (User, Post, Comment) model classes
    for testing complex queries with related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    User, Post, Comment = provider.setup_blog_fixtures(scenario)

    yield User, Post, Comment

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def json_user_fixture(request):
    """
    A pytest fixture that provides configured JsonUser model class
    for testing JSON functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get JsonUser model for the test via fixture group
    (JsonUser,) = provider.setup_json_user_fixtures(scenario)

    yield JsonUser

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def tree_fixtures(request):
    """
    A pytest fixture that provides configured Node model class
    for testing tree structure and recursive CTE functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get Node model for the test via fixture group
    result = provider.setup_tree_fixtures(scenario)

    # Ensure we return a tuple for consistency with other fixtures
    if isinstance(result, tuple):
        yield result
    else:
        # If only a single model is returned, wrap it in a tuple
        yield (result,)

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def combined_fixtures(request):
    """
    A pytest fixture that provides configured (User, Order, OrderItem, Post, Comment) model classes
    for testing complex queries with multiple related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    User, Order, OrderItem, Post, Comment = provider.setup_combined_fixtures(scenario)

    yield User, Order, OrderItem, Post, Comment

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def extended_order_fixtures(request):
    """
    A pytest fixture that provides configured extended (User, ExtendedOrder, ExtendedOrderItem) model classes
    for testing advanced grouping functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    User, ExtendedOrder, ExtendedOrderItem = provider.setup_extended_order_fixtures(scenario)

    yield User, ExtendedOrder, ExtendedOrderItem

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def annotated_query_fixtures(request):
    """
    A pytest fixture that provides the configured SearchableItem model class.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get the SearchableItem model for the test via fixture group
    result = provider.setup_annotated_query_fixtures(scenario)

    yield result

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def mapped_models_fixtures(request):
    """
    A pytest fixture that provides configured `MappedUser`, `MappedPost`,
    and `MappedComment` model classes for testing, parameterized by scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Ask the provider to set up the database and configure the Mapped models for this scenario.
    user_model, post_model, comment_model = provider.setup_mapped_models(scenario)

    # Yield the configured model classes as a tuple.
    yield user_model, post_model, comment_model

    # After the test function finishes, perform cleanup.
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", autouse=True)
def check_protocol_requirements(request):
    """
    Auto-used fixture that checks if the current backend supports required protocols.

    This fixture runs automatically for each test and checks if the test has
    a 'requires_protocol' marker. If so, it verifies that the current backend
    supports the required protocols, skipping the test if not.
    """
    # Check if the test has a requires_protocol marker
    requires_protocol_marker = request.node.get_closest_marker("requires_protocol")
    if requires_protocol_marker:
        required_protocol_info = requires_protocol_marker.args[0]

        # At this point, the parametrized fixtures have already been set up
        # Look for any of the model fixtures that contain the models we need
        model_to_check = None

        # Check for common fixture names that contain models
        fixture_options = ['extended_order_fixtures', 'order_fixtures', 'blog_fixtures',
                          'json_user_fixture', 'tree_fixtures', 'combined_fixtures',
                          'annotated_query_fixtures', 'mapped_models_fixtures',
                          'async_order_fixtures', 'async_blog_fixtures', 'async_json_user_fixture',
                          'async_tree_fixtures', 'async_combined_fixtures', 'async_extended_order_fixtures',
                          'async_annotated_query_fixtures', 'async_mapped_models_fixtures']

        for fixture_name in fixture_options:
            if fixture_name in request.fixturenames:
                try:
                    fixture_value = request.getfixturevalue(fixture_name)

                    # Handle different types of fixture returns
                    if isinstance(fixture_value, tuple):
                        # If it's a tuple of models, use the first one that has a backend
                        for model in fixture_value:
                            if hasattr(model, 'backend') or hasattr(model, '__backend__'):
                                model_to_check = model
                                break
                    elif hasattr(fixture_value, 'backend') or hasattr(fixture_value, '__backend__'):
                        # If it's a single model/class with backend
                        model_to_check = fixture_value
                    elif hasattr(fixture_value, '__getitem__') and len(fixture_value) > 0:
                        # If it's an array-like structure
                        first_item = fixture_value[0]
                        if hasattr(first_item, 'backend') or hasattr(first_item, '__backend__'):
                            model_to_check = first_item

                    if model_to_check is not None:
                        break
                except Exception:
                    # If we can't get the fixture value, continue to the next option
                    continue

        if model_to_check is not None and (hasattr(model_to_check, 'backend') or hasattr(model_to_check, '__backend__')):
            # Use the model to check protocols
            from rhosocial.activerecord.testsuite.utils import skip_test_if_protocol_unsupported
            try:
                protocol_class, method_name = required_protocol_info
                skip_test_if_protocol_unsupported(model_to_check, protocol_class, method_name)
            except Exception:
                # If protocol checking fails for any reason, continue with the test
                # This ensures tests don't break due to protocol checking issues
                pass
        # If no appropriate model was found, the test will continue normally
        # This might happen if the protocol decorator is used inappropriately

    # Check for requires_functions marker
    requires_functions_marker = request.node.get_closest_marker("requires_functions")
    if requires_functions_marker:
        required_functions = requires_functions_marker.args[0]

        # Look for model fixture (similar to requires_protocol)
        model_to_check = None
        for fixture_name in fixture_options:
            if fixture_name in request.fixturenames:
                try:
                    fixture_value = request.getfixturevalue(fixture_name)
                    if isinstance(fixture_value, tuple):
                        for model in fixture_value:
                            if hasattr(model, 'backend') or hasattr(model, '__backend__'):
                                model_to_check = model
                                break
                    elif hasattr(fixture_value, 'backend') or hasattr(fixture_value, '__backend__'):
                        model_to_check = fixture_value
                    elif hasattr(fixture_value, '__getitem__') and len(fixture_value) > 0:
                        first_item = fixture_value[0]
                        if hasattr(first_item, 'backend') or hasattr(first_item, '__backend__'):
                            model_to_check = first_item
                    if model_to_check is not None:
                        break
                except Exception:
                    continue

        if model_to_check is not None and (hasattr(model_to_check, 'backend') or hasattr(model_to_check, '__backend__')):
            from rhosocial.activerecord.testsuite.utils import skip_test_if_functions_unsupported
            try:
                skip_test_if_functions_unsupported(model_to_check, required_functions)
            except Exception:
                pass


# --- Async Fixtures ---

# Add imports for async models
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncUser, AsyncOrder, AsyncOrderItem
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_blog_models import AsyncUser as AsyncBlogUser, AsyncPost, AsyncComment
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_extended_models import AsyncUser as AsyncExtendedUser, AsyncExtendedOrder, AsyncExtendedOrderItem


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_order_fixtures(request):
    """
    A pytest fixture that provides async-configured (AsyncUser, AsyncOrder, AsyncOrderItem) model classes
    for testing complex queries with related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    AsyncUser, AsyncOrder, AsyncOrderItem = await provider.setup_async_order_fixtures(scenario)

    yield AsyncUser, AsyncOrder, AsyncOrderItem

    # Disconnect the backend to allow the event loop to close.
    # The backend instance is shared across all models in this fixture group.
    backend_to_close = AsyncUser.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_blog_fixtures(request):
    """
    A pytest fixture that provides async-configured (AsyncUser, AsyncPost, AsyncComment) model classes
    for testing complex queries with related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    AsyncUser, AsyncPost, AsyncComment = await provider.setup_async_blog_fixtures(scenario)

    yield AsyncUser, AsyncPost, AsyncComment

    # Disconnect the backend to allow the event loop to close.
    # The backend instance is shared across all models in this fixture group.
    backend_to_close = AsyncUser.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_json_user_fixture(request):
    """
    A pytest fixture that provides async-configured AsyncJsonUser model class
    for testing JSON functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get AsyncJsonUser model for the test via fixture group
    (AsyncJsonUser,) = await provider.setup_async_json_user_fixtures(scenario)

    yield AsyncJsonUser

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = AsyncJsonUser.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_tree_fixtures(request):
    """
    A pytest fixture that provides async-configured AsyncNode model class
    for testing tree structure and recursive CTE functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get AsyncNode model for the test via fixture group
    result = await provider.setup_async_tree_fixtures(scenario)

    # Ensure we return a tuple for consistency with other fixtures
    if isinstance(result, tuple):
        yield result
    else:
        # If only a single model is returned, wrap it in a tuple
        yield (result,)

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = result.__backend__ if hasattr(result, '__backend__') else result[0].__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_combined_fixtures(request):
    """
    A pytest fixture that provides async-configured (AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment) model classes
    for testing complex queries with multiple related tables.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment = await provider.setup_async_combined_fixtures(scenario)

    yield AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment

    # Disconnect the backend to allow the event loop to close.
    # The backend instance is shared across all models in this fixture group.
    backend_to_close = AsyncUser.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_extended_order_fixtures(request):
    """
    A pytest fixture that provides async-configured extended (AsyncUser, AsyncExtendedOrder, AsyncExtendedOrderItem) model classes
    for testing advanced grouping functionality.
    It is parameterized to run for each available scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get all required models for the test via fixture group
    AsyncUser, AsyncExtendedOrder, AsyncExtendedOrderItem = await provider.setup_async_extended_order_fixtures(scenario)

    yield AsyncUser, AsyncExtendedOrder, AsyncExtendedOrderItem

    # Disconnect the backend to allow the event loop to close.
    # The backend instance is shared across all models in this fixture group.
    backend_to_close = AsyncUser.__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_annotated_query_fixtures(request):
    """
    A pytest fixture that provides the async-configured AsyncSearchableItem model class.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
    provider = provider_class()

    # Get the AsyncSearchableItem model for the test via fixture group
    result = await provider.setup_async_annotated_query_fixtures(scenario)

    yield result

    # Disconnect the backend to allow the event loop to close.
    backend_to_close = result.__backend__ if hasattr(result, '__backend__') else result[0].__backend__
    await backend_to_close.disconnect()

    # Cleanup after test
    await provider.cleanup_after_test_async(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
async def async_mapped_models_fixtures(request):
    """
    A pytest fixture that provides async-configured `AsyncMappedUser`, `AsyncMappedPost`,
    and `AsyncMappedComment` model classes for testing, parameterized by scenario.
    """
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider("feature.query.IQueryProvider")
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