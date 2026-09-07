# src/rhosocial/activerecord/testsuite/feature/ddl/conftest.py
"""
Pytest fixtures for the ``feature.ddl`` test group.

Fixtures provide configured model classes whose declarations are the single
source of truth; every test derives DDL via ``generate_create_table`` and the
provider executes it — verifying the model -> DDL -> database round trip on
each backend scenario. Sync and async variants are parameterized alike.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

PROVIDER_KEY_SYNC = "feature.ddl.IDDLSyncProvider"
PROVIDER_KEY_ASYNC = "feature.ddl.IDDLAsyncProvider"


def get_scenarios_sync():
    provider_class = get_provider_registry().get_provider(PROVIDER_KEY_SYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


def get_scenarios_async():
    provider_class = get_provider_registry().get_provider(PROVIDER_KEY_ASYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios_sync = get_scenarios_sync()
scenarios_async = get_scenarios_async()

SCENARIO_PARAMS_SYNC = scenarios_sync if scenarios_sync else [
    pytest.param("default", marks=pytest.mark.skip(reason="No sync ddl testsuite scenarios found"))
]
SCENARIO_PARAMS_ASYNC = scenarios_async if scenarios_async else [
    pytest.param("default", marks=pytest.mark.skip(reason="No async ddl testsuite scenarios found"))
]


def _new_provider(key):
    provider_class = get_provider_registry().get_provider(key)
    if not provider_class:
        raise RuntimeError(f"Provider '{key}' not registered")
    return provider_class()


# --- sync fixtures -------------------------------------------------------
@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def bare_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    model = provider.setup_bare_item_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def spec_order_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    model = provider.setup_spec_order_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def capability_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    model = provider.setup_capability_post_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def spec_comment_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    model = provider.setup_spec_comment_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def spec_comment_with_parent(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    comment, order = provider.setup_spec_comment_with_parent_models(scenario)
    yield comment, order
    provider.cleanup_after_test(scenario)


# --- async fixtures ------------------------------------------------------
@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_bare_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    model = await provider.setup_bare_item_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_spec_order_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    model = await provider.setup_spec_order_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_capability_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    model = await provider.setup_capability_post_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_spec_comment_with_parent(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    comment, order = await provider.setup_spec_comment_with_parent_models(scenario)
    yield comment, order
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_spec_comment_class(request):
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    model = await provider.setup_spec_comment_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)
