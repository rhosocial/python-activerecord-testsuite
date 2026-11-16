# src/rhosocial/activerecord/testsuite/feature/basic/crud_composite_pk/conftest.py
"""L2 environment fixtures for the ``basic/crud_composite_pk`` test set.

A composite primary key is a different declaration set from the single-key
``basic/crud`` tables, and on some engines a composite key cannot be expressed
at all.  Keeping it in its own directory means that gap skips this set alone
and leaves the single-key CRUD contract running.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: the tables this directory's files use, dropped and recreated for
  every test (function scope), so each test starts from empty tables.

``Order`` (single key) is part of the group because the set asserts the
backward-compatibility path beside the composite one.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.fixtures import resolve
from rhosocial.activerecord.testsuite.feature.basic.fixtures.composite_pk_models import (
    COMPOSITE_PK_FIXTURES,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)

OrderItem = resolve("OrderItem")
AsyncOrderItem = resolve("AsyncOrderItem")
Order = resolve("Order")
AsyncOrder = resolve("AsyncOrder")
MappedOrderItem = resolve("MappedOrderItem")
AsyncMappedOrderItem = resolve("AsyncMappedOrderItem")

DDL = ExecutionOptions(stmt_type=StatementType.DDL)


def _database_name() -> str:
    """Database name from this directory's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


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
    create_schema(database, COMPOSITE_PK_FIXTURES)
    yield
    drop_schema(database, COMPOSITE_PK_FIXTURES)


@pytest.fixture(name="order_item_class")
def order_item_class(database_config):
    scenario, config, _name = database_config
    OrderItem.configure(config, scenario.backend_class)
    model = OrderItem
    yield model
    _disconnect(model)


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(database_config):
    scenario, config, _name = database_config
    await AsyncOrderItem.configure(config, scenario.async_backend_class)
    model = AsyncOrderItem
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="order_class")
def order_class(database_config):
    scenario, config, _name = database_config
    Order.configure(config, scenario.backend_class)
    model = Order
    yield model
    _disconnect(model)


@pytest.fixture(name="async_order_class")
async def async_order_class(database_config):
    scenario, config, _name = database_config
    await AsyncOrder.configure(config, scenario.async_backend_class)
    model = AsyncOrder
    yield model
    await _disconnect_async(model)


@pytest.fixture(name="mapped_order_item_class")
def mapped_order_item_class(database_config):
    scenario, config, _name = database_config
    MappedOrderItem.configure(config, scenario.backend_class)
    model = MappedOrderItem
    yield model
    _disconnect(model)


@pytest.fixture(name="async_mapped_order_item_class")
async def async_mapped_order_item_class(database_config):
    scenario, config, _name = database_config
    await AsyncMappedOrderItem.configure(config, scenario.async_backend_class)
    model = AsyncMappedOrderItem
    yield model
    await _disconnect_async(model)
