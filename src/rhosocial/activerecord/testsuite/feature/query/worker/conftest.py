# src/rhosocial/activerecord/testsuite/feature/query/worker/conftest.py
"""L2 environment fixtures for ``query/worker``.

A worker process cannot inherit the test's open connections, so the fixtures
hand it the scenario's connection parameters instead.  The parameters are
derived from this directory's configuration, which keeps the worker on the
directory's database.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.definitions import (
    OrderItemsDefinition,
    OrdersDefinition,
    UsersDefinition,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import (
    Order,
    OrderItem,
    User,
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    UsersDefinition,
    OrdersDefinition,
    OrderItemsDefinition,
)


def _database_name() -> str:
    """Database name from this directory's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory database name."""
    name = _database_name()
    return backend_scenario, backend_scenario.make_config(name), name


@pytest.fixture(scope="session")
def database(database_config):
    """The directory's database, prepared once and left for later files."""
    scenario, config, name = database_config
    scenario.reset_database(name)
    backend = scenario.backend_class(connection_config=config)
    backend.connect()
    backend.introspect_and_adapt()
    yield backend
    backend.disconnect()


@pytest.fixture(scope="function", autouse=True)
def schema(database):
    """Drop and recreate the tables this directory uses, before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


class WorkerConnection:
    """Serializable connection payload for a worker process."""

    def __init__(self, scenario, config):
        self.scenario = scenario
        self.config = config

    def params(self, is_async=False):
        backend_class = (
            self.scenario.async_backend_class if is_async else self.scenario.backend_class
        )
        return {
            "backend_module": backend_class.__module__,
            "backend_class_name": backend_class.__name__,
            "config_class_module": type(self.config).__module__,
            "config_class_name": type(self.config).__name__,
            "config_kwargs": self.config.to_dict(),
            "schema_sql": "",
        }


@pytest.fixture(name="worker_connection_params")
def worker_connection_params(database_config):
    scenario, config, _name = database_config
    yield WorkerConnection(scenario, config).params()


@pytest.fixture(name="order_fixtures_for_worker")
def order_fixtures_for_worker(database_config):
    scenario, config, _name = database_config
    models = (User, Order, OrderItem)
    for model in models:
        model.configure(config, scenario.backend_class)
    payload = {
        "models": models,
        "conn_params": WorkerConnection(scenario, config).params(),
    }
    yield payload
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="async_order_fixtures_for_worker")
async def async_order_fixtures_for_worker(database_config):
    scenario, config, _name = database_config
    models = (AsyncUser, AsyncOrder, AsyncOrderItem)
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    payload = {
        "models": models,
        "conn_params": WorkerConnection(scenario, config).params(is_async=True),
    }
    yield payload
    for model in models:
        await model.backend().disconnect()
