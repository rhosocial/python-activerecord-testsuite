# src/rhosocial/activerecord/testsuite/feature/adapters/conftest.py
"""L2 environment fixtures for the neutral-type contract.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: drop and recreate the tables for every test (function scope);
- model fixtures use ``ActiveRecord.configure`` with this directory's config
  and backend class.
"""
from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.adapters.fixtures import (
    NeutralTypesFixture,
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory database name."""
    name = "test_adapters"
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
    fixture = NeutralTypesFixture(database.dialect)
    database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    database.execute(*fixture.drop_table.to_sql(), options=DDL)


@pytest.fixture
def neutral_types(database_config):
    """The sync model class, configured against the directory's database."""
    scenario, config, _name = database_config
    NeutralTypesFixture.model.configure(config, scenario.backend_class)
    yield NeutralTypesFixture.model
    NeutralTypesFixture.model.backend().disconnect()


@pytest.fixture
async def async_neutral_types(database_config):
    """The async model class, configured for the test's event loop."""
    scenario, config, _name = database_config
    await NeutralTypesFixture.async_model.configure(
        config, scenario.async_backend_class
    )
    yield NeutralTypesFixture.async_model
    await NeutralTypesFixture.async_model.backend().disconnect()
