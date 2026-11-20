# src/rhosocial/activerecord/testsuite/feature/basic/fields/conftest.py
"""L2 environment fixtures for the ``basic/fields`` directory.

Mirrors ``basic/types/conftest.py``:

* ``database`` -- one database per directory (session scope, reset at start);
* ``schema`` -- the tables this directory owns, dropped and recreated for every
  test so each one starts from empty tables and sequence state.

A table whose required storage concept a dialect refuses is left out of
``create_schema`` rather than blowing up in setup.  The tests ask the same
registry through ``table_reason`` / ``operation_reason`` and skip with the
returned, named reason.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.field_models import (
    FIELD_FIXTURES,
    FIELD_VARIANT_FIXTURES,
    AsyncFieldRow,
    AsyncFieldRowAnnotated,
    FieldRow,
    FieldRowAnnotated,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.user_models import (
    USER_FIXTURES,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose="Field mapping, derived fields and column-name/adapter declarations.",
    passes_means="Python field names and column names map without losing the value or its type",
    fails_means="a field is read from the wrong column or a derived value is not computed",
)

_ALL_FIXTURES = USER_FIXTURES + FIELD_FIXTURES + FIELD_VARIANT_FIXTURES


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
    """Create only the tables this dialect can render, before every test."""
    dialect = database.dialect
    usable = tuple(fixture for fixture in _ALL_FIXTURES if table_reason(dialect, fixture) is None)
    create_schema(database, usable)
    yield
    drop_schema(database, usable)


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


@pytest.fixture(name="field_row_class")
def field_row_class(database_config):
    """The bare field-mapping model, configured against the directory database."""
    scenario, config, _name = database_config
    FieldRow.configure(config, scenario.backend_class)
    yield FieldRow
    _disconnect(FieldRow)


@pytest.fixture(name="field_row_annotated_class")
def field_row_annotated_class(database_config):
    """The annotated field-mapping model, configured against the directory database."""
    scenario, config, _name = database_config
    FieldRowAnnotated.configure(config, scenario.backend_class)
    yield FieldRowAnnotated
    _disconnect(FieldRowAnnotated)


@pytest.fixture(name="async_field_row_class")
async def async_field_row_class(database_config):
    """Async twin of the bare field-mapping model."""
    scenario, config, _name = database_config
    await AsyncFieldRow.configure(config, scenario.async_backend_class)
    yield AsyncFieldRow
    await _disconnect_async(AsyncFieldRow)


@pytest.fixture(name="async_field_row_annotated_class")
async def async_field_row_annotated_class(database_config):
    """Async twin of the annotated field-mapping model."""
    scenario, config, _name = database_config
    await AsyncFieldRowAnnotated.configure(config, scenario.async_backend_class)
    yield AsyncFieldRowAnnotated
    await _disconnect_async(AsyncFieldRowAnnotated)
