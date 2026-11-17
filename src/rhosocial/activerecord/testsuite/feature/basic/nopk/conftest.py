# src/rhosocial/activerecord/testsuite/feature/basic/nopk/conftest.py
"""L2 environment fixtures for the ``basic/nopk`` directory."""

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration
from rhosocial.activerecord.testsuite.feature.basic.fixtures.user_models import (
    USER_FIXTURES,
)


DECLARATION = Declaration(
    parallel=True,
    purpose='Keyless models: identity-based access must be refused.',
    passes_means='models with primary_key() -> None reject identity lookups by name',
    fails_means='a keyless model is addressed by identity as if it had a key',
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_nopk"
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
    create_schema(database, USER_FIXTURES)
    yield
    drop_schema(database, USER_FIXTURES)