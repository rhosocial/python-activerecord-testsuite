# src/rhosocial/activerecord/testsuite/feature/query/typed_column/conftest.py
"""L2 environment fixtures for ``query/typed_column``.

- ``database`` / ``schema``: the directory's database and its ``json_users``
  table;
- ``dialect``: the directory's adapted dialect, shared by the contract files
  that do not define their own.  Module-level fixtures in the existing contract
  files still shadow this one, so nothing changes for them.

The contracts assert on expression trees and rendered SQL, never on data, so
they read the dialect from the directory's adapted backend rather than from a
model's class backend.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.query.fixtures.definitions import (
    JsonUsersDefinition,
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (JsonUsersDefinition,)


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
    """Drop and recreate the table this directory uses, before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


@pytest.fixture
def dialect(database):
    """The dialect under test, taken from the directory's adapted backend."""
    return database.dialect
