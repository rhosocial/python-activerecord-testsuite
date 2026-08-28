# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/conftest.py
"""Fixtures for cross-schema query tests.

Provisioning is delegated to the backend provider through the OPTIONAL
``setup_schema_fixtures`` method. Providers that do not implement it (or do
not declare schema support) cause a clean skip — the testsuite itself makes
no judgment about backend capabilities; that is declared by each backend's
dialect (``supports_schema``) and consumed via ``@requires_protocol``.
"""

import pytest

from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
from rhosocial.activerecord.testsuite.feature.query.conftest import (
    PROVIDER_KEY_ASYNC,
    PROVIDER_KEY_SYNC,
    SCENARIO_PARAMS_ASYNC,
    SCENARIO_PARAMS_SYNC,
)


def _provider_for(key):
    registry = get_provider_registry()
    provider_class = registry.get_provider(key)
    return provider_class() if provider_class else None


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def schema_fixtures(request):
    """(SchemaCustomer, SchemaOrder) bound to two distinct schemas."""
    provider = _provider_for(PROVIDER_KEY_SYNC)
    if provider is None:
        pytest.skip("No testsuite scenarios found")
    setup = getattr(provider, "setup_schema_fixtures", None)
    if setup is None:
        pytest.skip("Provider does not provide cross-schema fixtures")

    scenario = request.param
    models = setup(scenario)
    try:
        yield models
    finally:
        cleanup = getattr(provider, "cleanup_after_test", None)
        if cleanup:
            cleanup(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_schema_fixtures(request):
    """(AsyncSchemaCustomer, AsyncSchemaOrder) bound to two distinct schemas."""
    provider = _provider_for(PROVIDER_KEY_ASYNC)
    if provider is None:
        pytest.skip("No async testsuite scenarios found")
    setup = getattr(provider, "setup_schema_fixtures", None)
    if setup is None:
        pytest.skip("Provider does not provide cross-schema fixtures")

    scenario = request.param
    models = await setup(scenario)
    try:
        yield models
    finally:
        cleanup = getattr(provider, "cleanup_after_test", None)
        if cleanup:
            await cleanup(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def mixed_schema_fixtures(request):
    """(User, Order, MixedSchemaOrder): default users/orders plus orders in SCHEMA_A."""
    provider = _provider_for(PROVIDER_KEY_SYNC)
    if provider is None:
        pytest.skip("No testsuite scenarios found")
    setup = getattr(provider, "setup_mixed_schema_fixtures", None)
    if setup is None:
        pytest.skip("Provider does not provide mixed-schema fixtures")

    scenario = request.param
    models = setup(scenario)
    try:
        yield models
    finally:
        cleanup = getattr(provider, "cleanup_after_test", None)
        if cleanup:
            cleanup(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_mixed_schema_fixtures(request):
    """(AsyncUser, AsyncOrder, AsyncMixedSchemaOrder) with orders also in SCHEMA_A."""
    provider = _provider_for(PROVIDER_KEY_ASYNC)
    if provider is None:
        pytest.skip("No async testsuite scenarios found")
    setup = getattr(provider, "setup_mixed_schema_fixtures", None)
    if setup is None:
        pytest.skip("Provider does not provide mixed-schema fixtures")

    scenario = request.param
    models = await setup(scenario)
    try:
        yield models
    finally:
        cleanup = getattr(provider, "cleanup_after_test", None)
        if cleanup:
            await cleanup(scenario)
