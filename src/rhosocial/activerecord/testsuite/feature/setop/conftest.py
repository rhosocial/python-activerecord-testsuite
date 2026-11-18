# src/rhosocial/activerecord/testsuite/feature/setop/conftest.py
"""L1/L2 environment fixtures for the ``setop`` topic.

Self-contained: owns its database declaration, its DDL environment and the
order model group used by every set-operation test.  The composite-primary-key
tests borrow the basic topic's public ``OrderItem`` / ``AsyncOrderItem`` name
for ``order_item_class`` / ``async_order_item_class`` rather than redefining it.
"""

import importlib
import sys
from pathlib import Path

import pytest

from rhosocial.activerecord.connection import AsyncBackendGroup, BackendGroup
from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncOrderItem as AsyncBasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    OrderItem as BasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.setop.fixtures.async_models import (
    AsyncOrder,
    AsyncOrderItem,
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.setop.fixtures.definitions import (
    OrderItemsDefinition,
    OrdersDefinition,
    UsersDefinition,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration


DECLARATION = Declaration(
    # This scope opens a database; the plugin enforces this declaration.
    uses_database=True,
    parallel=True,
    purpose="Directory-owned database for the setop topic.",
    passes_means="the directory's tests run on one worker per scenario",
    fails_means="two workers share the same database file",
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    UsersDefinition,
    OrdersDefinition,
    OrderItemsDefinition,
)

FIXTURES_PACKAGE = "rhosocial.activerecord.testsuite.feature.setop.fixtures"

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


# --- the order group -------------------------------------------------------

ORDER_MODELS = (User, Order, OrderItem)
ASYNC_ORDER_MODELS = (AsyncUser, AsyncOrder, AsyncOrderItem)


@pytest.fixture(name="order_fixtures")
def order_fixtures(database_config):
    scenario, config, _name = database_config
    group = BackendGroup(
        name="setop_order",
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
        name="setop_order",
        models=list(ASYNC_ORDER_MODELS),
        config=config,
        backend_class=scenario.async_backend_class,
    )
    await group.configure()
    await group.get_backend().introspect_and_adapt()
    yield ASYNC_ORDER_MODELS
    await group.get_backend().disconnect()


# --- the basic composite-key order item ------------------------------------


@pytest.fixture(name="order_item_class")
def order_item_class(database_config):
    scenario, config, _name = database_config
    BasicOrderItem.configure(config, scenario.backend_class)
    yield BasicOrderItem
    BasicOrderItem.backend().disconnect()


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(database_config):
    scenario, config, _name = database_config
    await AsyncBasicOrderItem.configure(config, scenario.async_backend_class)
    yield AsyncBasicOrderItem
    await AsyncBasicOrderItem.backend().disconnect()
