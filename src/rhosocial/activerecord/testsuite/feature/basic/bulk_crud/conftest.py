# src/rhosocial/activerecord/testsuite/feature/basic/bulk_crud/conftest.py
"""L2 environment fixtures for the ``basic/bulk_crud`` directory."""

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

from rhosocial.activerecord.testsuite.feature.basic.fixtures.user_models import BULK_FIXTURES
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration


DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose='Bulk insert, batch update/delete and chunked operations.',
    passes_means='batch operations affect exactly the selected rows in one round',
    fails_means='a batch touches rows it should not or leaves stale rows behind',
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)



@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_bulk_crud"
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
    create_schema(database, BULK_FIXTURES)
    yield
    drop_schema(database, BULK_FIXTURES)