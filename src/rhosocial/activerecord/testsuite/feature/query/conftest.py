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

    yield (User, Order, OrderItem)

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

    yield (User, Post, Comment)

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

    yield (User, Order, OrderItem, Post, Comment)

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

    yield (User, ExtendedOrder, ExtendedOrderItem)

    # Cleanup after test
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", autouse=True)
def check_capability_requirements(request):
    """
    Auto-used fixture that checks if the current backend supports required capabilities.
    
    This fixture runs automatically for each test and checks if the test has
    a 'requires_capability' marker. If so, it verifies that the current backend
    supports the required capabilities, skipping the test if not.
    """
    # Check if the test has a requires_capability marker
    requires_capability_marker = request.node.get_closest_marker("requires_capability")
    if requires_capability_marker:
        required_capabilities = requires_capability_marker.args[0]
        
        # At this point, the parametrized fixtures have already been set up
        # Look for any of the model fixtures that contain the models we need
        model_to_check = None
        
        # Check for common fixture names that contain models
        fixture_options = ['extended_order_fixtures', 'order_fixtures', 'blog_fixtures', 
                          'json_user_fixture', 'tree_fixtures', 'combined_fixtures']
        
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
            # Use the model to check capabilities
            from ..utils import skip_test_if_capability_unsupported
            try:
                skip_test_if_capability_unsupported(model_to_check, required_capabilities)
            except Exception:
                # If capability checking fails for any reason, continue with the test
                # This ensures tests don't break due to capability checking issues
                pass
        # If no appropriate model was found, the test will continue normally
        # This might happen if the capability decorator is used inappropriately


