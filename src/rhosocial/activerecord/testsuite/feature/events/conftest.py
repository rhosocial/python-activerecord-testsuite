# src/rhosocial/activerecord/testsuite/feature/events/conftest.py
"""L2 environment and model fixtures for the events topic.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: both event tables, dropped and recreated for every test
  (function scope), so each test starts from empty tables;
- ``database_config``: the scenario, its connection configuration, and the
  directory database name, which the model fixtures configure against.

The directory owns one fixture group: every test prepares both event tables,
even when it only uses one of the models.  Which versioned model file supplies
the class is decided here, so tests only see fixture names.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.events.fixtures.definitions import (
    EventTestDefinition,
    EventTrackingDefinition,
)

from .fixtures import resolve

EventTestModel = resolve("EventTestModel")
AsyncEventTestModel = resolve("AsyncEventTestModel")
EventTrackingModel = resolve("EventTrackingModel")
AsyncEventTrackingModel = resolve("AsyncEventTrackingModel")

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (EventTestDefinition, EventTrackingDefinition)


def _database_name() -> str:
    """Database name from this conftest's namespace (below ``feature``)."""
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


@pytest.fixture(name="event_model")
def event_model(database_config):
    scenario, config, _name = database_config
    EventTestModel.configure(config, scenario.backend_class)
    yield EventTestModel
    EventTestModel.backend().disconnect()


@pytest.fixture(name="async_event_model")
async def async_event_model(database_config):
    scenario, config, _name = database_config
    await AsyncEventTestModel.configure(config, scenario.async_backend_class)
    yield AsyncEventTestModel
    await AsyncEventTestModel.backend().disconnect()


@pytest.fixture(name="event_tracking_model")
def event_tracking_model(database_config):
    scenario, config, _name = database_config
    EventTrackingModel.configure(config, scenario.backend_class)
    yield EventTrackingModel
    EventTrackingModel.backend().disconnect()


@pytest.fixture(name="async_event_tracking_model")
async def async_event_tracking_model(database_config):
    scenario, config, _name = database_config
    await AsyncEventTrackingModel.configure(config, scenario.async_backend_class)
    yield AsyncEventTrackingModel
    await AsyncEventTrackingModel.backend().disconnect()
