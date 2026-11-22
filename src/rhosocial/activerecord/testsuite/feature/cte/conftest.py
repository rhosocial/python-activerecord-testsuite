# src/rhosocial/activerecord/testsuite/feature/cte/conftest.py
"""L2 environment fixtures for the standalone ``cte`` topic.

The topic owns its database and brings two L1 model groups together:

- ``tree_fixtures`` / ``async_tree_fixtures`` configured from this topic's own
  ``Node`` / ``AsyncNode`` models (the ``nodes`` table only);
- ``order_item_class`` / ``async_order_item_class`` configured from the public
  composite-key ``OrderItem`` of ``basic.fixtures`` — the composite-PK CTE self
  tests run against it.

``database`` is session-scoped and emptied at start; ``schema`` drops and
recreates both tables for every test so identity state is reset as well.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.expression import ColumnConstraint as Constraint
from rhosocial.activerecord.backend.expression import ColumnDefinition as Column
from rhosocial.activerecord.backend.expression import CreateTableStatement as CreateTable
from rhosocial.activerecord.backend.expression import DropTableStatement as DropTable
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.suggestion import IntegerAutoIncrementSuggestionRenderer
from rhosocial.activerecord.backend.expression.types import DecimalType as Numeric
from rhosocial.activerecord.backend.expression.types import IntegerType as Int
from rhosocial.activerecord.backend.expression.types import TimestampType
from rhosocial.activerecord.backend.expression.types import VarCharType as VarChar
from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncOrderItem as AsyncBasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    OrderItem as BasicOrderItem,
)
from rhosocial.activerecord.testsuite.feature.cte.fixtures.async_cte_models import AsyncNode
from rhosocial.activerecord.testsuite.feature.cte.fixtures.cte_models import Node
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration


DECLARATION = Declaration(
    # This scope opens a database; the plugin enforces this declaration.
    uses_database=True,
    parallel=True,
    purpose="Directory-owned database for the standalone CTEQuery tests.",
    passes_means="the directory's CTE tests run on one worker per scenario",
    fails_means="two workers share the same database file",
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)


# --- table definitions (local to this topic) --------------------------------


def _supports_drop_if_exists(dialect) -> bool:
    probe = getattr(dialect, "supports_if_exists_table", None)
    return True if probe is None else bool(probe())


class Definition:
    """Base class for this topic's table definitions."""

    table_name = ""

    def __init__(self, dialect, table_name=None):
        self.dialect = dialect
        self.name = table_name or type(self).table_name
        self.create_table = CreateTable(
            dialect,
            table=Table(dialect, self.name),
            columns=self.columns(),
            table_constraints=[],
        )
        self.drop_table = DropTable(
            dialect,
            table=Table(dialect, self.name),
            if_exists=_supports_drop_if_exists(dialect),
        )

    def columns(self):
        raise NotImplementedError

    def column(self, name, sql_type, constraints=None):
        return Column(self.dialect, name, sql_type, constraints=constraints or [])

    def auto_pk(self, name="id"):
        data_type, attributes = IntegerAutoIncrementSuggestionRenderer().parts(self.dialect, Int(self.dialect))
        return Column(
            self.dialect,
            name,
            data_type,
            constraints=[Constraint(self.dialect, branch=PrimaryKey(self.dialect))],
            attributes=attributes,
        )

    def timestamp(self, name):
        probe = getattr(self.dialect, "supports_microsecond_timestamp", None)
        keeps_microseconds = bool(probe()) if callable(probe) else bool(probe)
        return self.column(
            name,
            TimestampType(self.dialect, precision=6 if keeps_microseconds else None),
        )


class OrderItemsDefinition(Definition):
    """The composite-key ``order_items`` table used by the CTE-self tests."""

    table_name = "order_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("order_id", Int(self.dialect)),
            self.column("product_id", Int(self.dialect)),
            self.column("quantity", Int(self.dialect)),
            self.column("unit_price", Numeric(self.dialect, 12, 4)),
        ]


class NodesDefinition(Definition):
    """The ``nodes`` table used by ``tree_fixtures``."""

    table_name = "nodes"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("name", VarChar(self.dialect, 255)),
            self.column("parent_id", Int(self.dialect)),
            self.column("value", Numeric(self.dialect, 12, 4)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


DEFINITIONS = (OrderItemsDefinition, NodesDefinition)


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


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


# --- composite-key order item (borrowed from basic.fixtures) ----------------


@pytest.fixture(name="order_item_class")
def order_item_class(database_config):
    scenario, config, _name = database_config
    BasicOrderItem.configure(config, scenario.backend_class)
    yield BasicOrderItem
    _disconnect(BasicOrderItem)


@pytest.fixture(name="async_order_item_class")
async def async_order_item_class(database_config):
    scenario, config, _name = database_config
    await AsyncBasicOrderItem.configure(config, scenario.async_backend_class)
    yield AsyncBasicOrderItem
    await _disconnect_async(AsyncBasicOrderItem)


# --- the tree group (this topic's own Node models) --------------------------


@pytest.fixture(name="tree_fixtures")
def tree_fixtures(database_config):
    scenario, config, _name = database_config
    Node.configure(config, scenario.backend_class)
    yield (Node,)
    _disconnect(Node)


@pytest.fixture(name="async_tree_fixtures")
async def async_tree_fixtures(database_config):
    scenario, config, _name = database_config
    await AsyncNode.configure(config, scenario.async_backend_class)
    yield (AsyncNode,)
    await _disconnect_async(AsyncNode)
