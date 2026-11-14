# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/conftest.py
"""L2 environment fixtures for ``query/cross_schema``.

The directory's own database is created and emptied like every other query
directory, but no table belongs to its default namespace: the tests only
provision schema-qualified tables.  A backend opts in by declaring an optional
``schema_setup`` callable on its scenario object.  It receives this directory's
``database_config`` triple and a suffix, and returns the configured models the
tests use.  Backends without it skip these tests instead of emulating schemas
they do not have.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

# No tables belong to this group: only capability-gated tests live here, and
# they provision their cross-schema models themselves.
DEFINITIONS = ()


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
    """The default namespace declares no tables; the tests provision their own."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


@pytest.fixture(name="schema_fixtures")
def schema_fixtures(database_config):
    scenario, _config, _name = database_config
    setup = getattr(scenario, "schema_setup", None)
    if setup is None:
        pytest.skip("backend does not declare cross-schema fixtures")
    yield setup(database_config, "schema")


@pytest.fixture(name="async_schema_fixtures")
async def async_schema_fixtures(database_config):
    scenario, _config, _name = database_config
    setup = getattr(scenario, "schema_setup", None)
    if setup is None:
        pytest.skip("backend does not declare cross-schema fixtures")
    yield setup(database_config, "async_schema")


@pytest.fixture(name="mixed_schema_fixtures")
def mixed_schema_fixtures(database_config):
    scenario, _config, _name = database_config
    setup = getattr(scenario, "schema_setup", None)
    if setup is None:
        pytest.skip("backend does not declare cross-schema fixtures")
    yield setup(database_config, "mixed_schema")


@pytest.fixture(name="async_mixed_schema_fixtures")
async def async_mixed_schema_fixtures(database_config):
    scenario, _config, _name = database_config
    setup = getattr(scenario, "schema_setup", None)
    if setup is None:
        pytest.skip("backend does not declare cross-schema fixtures")
    yield setup(database_config, "async_mixed_schema")
