# src/rhosocial/activerecord/testsuite/feature/basic/ddl/conftest.py
"""
Pytest configuration for the ALTER TABLE ``IF [NOT] EXISTS`` subtopic of the
``basic`` feature group.

These tests are an *expression/dialect* contract: they build `AddColumn` /
`DropColumn` / `DropTableConstraint` actions and assert the emitted SQL
(sync & async). No live database connection is required, so the providers
hand over a bare dialect instance via ``get_dialect()``.

Unsupported backends are skipped declaratively with ``@requires_protocol``
markers against the ``AlterTableModifierSupport`` protocol; the autouse
fixture below reads those markers and skips when the backend dialect does not
implement (or does not advertise) the required switch.
"""
import pytest
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

# The 'basic' provider is shared: the ddl subtopic reuses its sync/async
# provider registration and only requires the extra ``get_dialect()`` hooks.
PROVIDER_KEY_SYNC = "feature.basic.IBasicSyncProvider"
PROVIDER_KEY_ASYNC = "feature.basic.IBasicAsyncProvider"


def get_scenarios_sync():
    """Discover basic sync scenarios; used to parameterize the dialect."""
    provider_class = get_provider_registry().get_provider(PROVIDER_KEY_SYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


def get_scenarios_async():
    """Discover basic async scenarios; used to parameterize the dialect."""
    provider_class = get_provider_registry().get_provider(PROVIDER_KEY_ASYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


scenarios_sync = get_scenarios_sync()
scenarios_async = get_scenarios_async()

SCENARIO_PARAMS_SYNC = scenarios_sync or [
    pytest.param("default", marks=pytest.mark.skip(reason="No sync basic ddl scenarios found"))
]
SCENARIO_PARAMS_ASYNC = scenarios_async or [
    pytest.param("default", marks=pytest.mark.skip(reason="No async basic ddl scenarios found"))
]


def _new_provider(provider_key):
    provider_class = get_provider_registry().get_provider(provider_key)
    assert provider_class is not None, f"No provider registered for {provider_key}"
    return provider_class()


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def ddl_dialect(request):
    """Provide a backend dialect instance for sync ALTER TABLE tests."""
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_SYNC)
    yield provider.get_dialect(scenario)
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_ddl_dialect(request):
    """Provide a backend dialect instance for async ALTER TABLE tests."""
    scenario = request.param
    provider = _new_provider(PROVIDER_KEY_ASYNC)
    yield await provider.get_dialect(scenario)
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", autouse=True)
def check_ddl_protocol_requirements(request):
    """
    Auto-use fixture: skip tests that require an unsupported ALTER TABLE
    modifier — or protocol capability.

    Reads the ``requires_protocol`` marker placed on the test and skips it
    when the current backend dialect either does not implement the protocol
    class or advertises ``False`` for the requested ``supports_*`` method.

    The dialect (and its capability switches) is identical for the sync and
    async providers of a given backend, so the check uses a freshly-built
    dialect instance rather than depending on the sync/async fixtures.
    """
    marker = request.node.get_closest_marker("requires_protocol")
    if not marker:
        return
    protocol_class, method_name = marker.args[0]

    # ``@requires_protocol`` may reference the protocol by dotted string.
    if isinstance(protocol_class, str):
        import importlib

        module_path, _, cls_name = protocol_class.rpartition(".")
        try:
            protocol_class = getattr(importlib.import_module(module_path), cls_name)
        except (ImportError, AttributeError) as exc:
            pytest.skip(f"Skipping test - unable to resolve protocol class: {exc}")
            return

    provider_class = get_provider_registry().get_provider(PROVIDER_KEY_SYNC)
    if provider_class is None:
        return
    try:
        dialect = provider_class().get_dialect("default")
    except Exception:
        return

    if not isinstance(dialect, protocol_class):
        pytest.skip(
            f"Skipping test - backend dialect does not implement {protocol_class.__name__} protocol"
        )
        return

    if method_name:
        method = getattr(dialect, method_name, None)
        if callable(method) and method() is not True:
            pytest.skip(
                f"Skipping test - backend dialect does not support {method_name.removeprefix('supports_')}"
            )