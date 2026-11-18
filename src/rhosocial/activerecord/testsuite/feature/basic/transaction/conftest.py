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

from rhosocial.activerecord.testsuite.feature.basic.fixtures.connection_models import TEST_USER_FIXTURES
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration


DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose='Savepoint API and cross-task transaction ownership.',
    passes_means='savepoints nest and roll back to the right owner task',
    fails_means='a rollback escapes its owner or a savepoint leaves partial state',
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)



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
    create_schema(database, TEST_USER_FIXTURES)
    yield
    drop_schema(database, TEST_USER_FIXTURES)