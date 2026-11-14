# src/rhosocial/activerecord/testsuite/feature/query/worker/conftest.py
"""Fixtures for the query feature's WorkerPool tests.

A worker process cannot inherit the test's open connections, so the fixtures
hand it the scenario's connection parameters instead.  The parameters are
derived from the environment's own configuration, which keeps the worker on
the directory's database.
"""
import pytest

from rhosocial.activerecord.testsuite.feature.query.fixtures import tables
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import (
    Order,
    OrderItem,
    User,
)

GROUP_TABLES = ("users", "orders", "order_items")


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.QUERY_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


def connection_parameters(environment, is_async=False):
    """Return serializable connection information for a worker process."""
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


def disconnect(models) -> None:
    for model in models:
        backend = getattr(model, "__backend__", None)
        if backend is not None:
            backend.disconnect()


async def disconnect_async(models) -> None:
    for model in models:
        backend = getattr(model, "__backend__", None)
        if backend is not None:
            await backend.disconnect()


@pytest.fixture(name="worker_connection_params")
def worker_connection_params(environment):
    yield connection_parameters(environment)


@pytest.fixture(name="order_fixtures_for_worker")
def order_fixtures_for_worker(environment):
    models = tuple(
        environment.configure(model) for model in (User, Order, OrderItem)
    )
    params = connection_parameters(environment)
    yield {"models": models, "conn_params": params}
    disconnect(models)


@pytest.fixture(name="async_order_fixtures_for_worker")
async def async_order_fixtures_for_worker(environment):
    models = tuple(
        [
            await environment.configure_async(model)
            for model in (AsyncUser, AsyncOrder, AsyncOrderItem)
        ]
    )
    params = connection_parameters(environment, is_async=True)
    yield {"models": models, "conn_params": params}
    await disconnect_async(models)
