# src/rhosocial/activerecord/testsuite/feature/basic/transaction/conftest.py
"""L2 environment fixtures for ``basic/transaction``.

The transaction tests reuse the pool fixtures from ``basic/connection``; this
directory owns its own database and prepares its own table group.
"""
import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.connection.conftest import (  # noqa: F401
    async_pool_and_model,
    sync_pool_and_model,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import TestUserDefinition

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    TestUserDefinition,
)


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_transaction"
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
    """Drop and recreate this directory's tables before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)
