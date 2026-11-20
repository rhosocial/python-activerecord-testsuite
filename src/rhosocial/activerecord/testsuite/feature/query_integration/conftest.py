# src/rhosocial/activerecord/testsuite/feature/query_integration/conftest.py
"""L2 environment + combination fixtures for the ``query_integration`` topic.

This topic is self-contained: it owns one database and declares it with a
``DECLARATION(uses_database=True)``.  The four tables the combinations need
(``users`` / ``orders`` / ``order_items`` and ``nodes``) are created in that one
shared database by the ``schema`` fixture, and every model is imported from
this topic's own ``fixtures`` package.

Two combinations of fixture groups are exposed:

* ``tree_fixtures`` / ``async_tree_fixtures`` -- the ``Node`` tree group used by
  the CTE + ActiveQuery cases;
* ``order_fixtures`` / ``async_order_fixtures`` -- the User/Order/OrderItem
  group used by the CTE + SetOperation and ActiveQuery + SetOperation cases.

A fixture group is one unit of work: tests count queries on one model's
backend and expect the relation queries of the rest to go through that same
connection, so the group shares one backend instance (``BackendGroup``).
"""

import importlib
import sys
from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.connection import AsyncBackendGroup, BackendGroup
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.async_cte_models import (
    AsyncNode,
)
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.cte_models import Node
from rhosocial.activerecord.testsuite.feature.query_integration.fixtures.definitions import (
    NodesDefinition,
    OrderItemsDefinition,
    OrdersDefinition,
    UsersDefinition,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    uses_database=True,
    parallel=True,
    purpose="Directory-owned database for query_integration combination fixtures.",
    passes_means="the directory's combination tests run on one worker per scenario",
    fails_means="two workers share the same database file",
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

# All four tables live in one shared database: Node + the order group.
DEFINITIONS = (
    UsersDefinition,
    OrdersDefinition,
    OrderItemsDefinition,
    NodesDefinition,
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


# --- model resolution -------------------------------------------------------

FIXTURES_PACKAGE = "rhosocial.activerecord.testsuite.feature.query_integration.fixtures"

VERSION_MODULES = (("312", (3, 12)), ("311", (3, 11)), ("310", (3, 10)))


def resolve(name: str):
    """Return the newest versioned model class available, or the baseline one."""
    for suffix, required in VERSION_MODULES:
        if sys.version_info < required:
            continue
        module_path = f"{FIXTURES_PACKAGE}.models_py{suffix}"
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            continue
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    return getattr(importlib.import_module(f"{FIXTURES_PACKAGE}.models"), name)


User = resolve("User")
Order = resolve("Order")
OrderItem = resolve("OrderItem")


# --- the order group --------------------------------------------------------

ORDER_MODELS = (User, Order, OrderItem)
ASYNC_ORDER_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem)


@pytest.fixture(name="order_fixtures")
def order_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="query_integration_order",
        models=list(ORDER_MODELS),
        config=config,
        backend_class=scenario.backend_class,
    )
    group.configure()
    group.get_backend().introspect_and_adapt()
    yield ORDER_MODELS
    group.get_backend().disconnect()


@pytest.fixture(name="async_order_fixtures")
async def async_order_fixtures(database_config):
    scenario, config, _name = database_config
    group = AsyncBackendGroup(
        name="query_integration_order",
        models=list(ASYNC_ORDER_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_ORDER_MODELS
    await group.get_backend().disconnect()


# --- the tree group ---------------------------------------------------------


@pytest.fixture(name="tree_fixtures")
def tree_fixtures(database_config):
    scenario, config, _name = database_config
    Node.configure(config, scenario.backend_class)
    yield (Node,)
    Node.backend().disconnect()


@pytest.fixture(name="async_tree_fixtures")
async def async_tree_fixtures(database_config):
    scenario, config, _name = database_config
    await AsyncNode.configure(config, scenario.async_backend_class)
    yield (AsyncNode,)
    await AsyncNode.backend().disconnect()
