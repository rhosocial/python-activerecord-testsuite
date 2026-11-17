# src/rhosocial/activerecord/testsuite/feature/basic/fields/conftest.py
"""L2 environment fixtures for the ``basic/fields`` minimal test set.

The directory owns one database (named after its path) and one fixture group:
the field round-trip table, the mapped and mixed annotation tables, and the
product table the derived-field models share.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: the tables this directory's files use, dropped and recreated for
  every test (function scope), so each test starts from empty tables and
  sequence/identity state is reset.
"""
from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

from rhosocial.activerecord.testsuite.feature.basic.fixtures.field_models import (
    FIELD_FIXTURES,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.type_rows_models import (
    TYPE_ROW_FIXTURES,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.user_models import (
    USER_FIXTURES,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration


DECLARATION = Declaration(
    parallel=True,
    purpose='Field mapping, derived fields and column-name/adapter declarations.',
    passes_means='Python field names and column names map without losing the value or its type',
    fails_means='a field is read from the wrong column or a derived value is not computed',
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)



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
    create_schema(database, USER_FIXTURES + FIELD_FIXTURES + TYPE_ROW_FIXTURES)
    yield
    drop_schema(database, USER_FIXTURES + FIELD_FIXTURES + TYPE_ROW_FIXTURES)