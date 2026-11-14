# src/rhosocial/activerecord/testsuite/feature/basic/worker/conftest.py
"""The ``basic/worker`` minimal test set.

Worker processes need serializable connection information: the module and
class names plus the configuration kwargs.  The environment builds it from
the scenario, so no backend declaration has to be written down here.
"""
import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures import resolve, tables

User = resolve("User")
AsyncUser = resolve("AsyncUser")

GROUP_TABLES = ("users",)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.BASIC_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


def connection_parameters(environment, is_async=False):
    """Return serializable connection information for a Worker process."""
    config = environment.make_config()
    backend_class = (
        environment.scenario.async_backend_class
        if is_async
        else environment.scenario.backend_class
    )
    return {
        "backend_module": backend_class.__module__,
        "backend_class_name": backend_class.__name__,
        "config_class_module": type(config).__module__,
        "config_class_name": type(config).__name__,
        "config_kwargs": config.to_dict(),
        "schema_sql": "",
    }


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


@pytest.fixture(name="worker_connection_params")
def worker_connection_params(environment):
    yield connection_parameters(environment)


@pytest.fixture(name="user_class_for_worker")
def user_class_for_worker(environment):
    model = environment.configure(User)
    params = connection_parameters(environment)
    yield {"model": model, "conn_params": params}
    _disconnect(model)


@pytest.fixture(name="async_user_class_for_worker")
async def async_user_class_for_worker(environment):
    model = await environment.configure_async(AsyncUser)
    params = connection_parameters(environment, is_async=True)
    yield {"model": model, "conn_params": params}
    await _disconnect_async(model)
