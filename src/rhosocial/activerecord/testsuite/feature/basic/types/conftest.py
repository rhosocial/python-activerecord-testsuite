# src/rhosocial/activerecord/testsuite/feature/basic/types/conftest.py
"""L2 environment fixtures for the ``basic/types`` scalar-type variant set.

Mirrors ``basic/crud/conftest.py``:

* ``database`` -- one database per directory (session scope, reset at start);
* ``schema`` -- the two variant tables this directory owns, dropped and
  recreated for every test so each one starts from empty tables and sequence
  state.

The difference is step one of README section 9: a table whose required storage
concept a dialect refuses is left out of ``create_schema`` instead of blowing
up in setup.  The tests ask the same registry through ``table_reason`` /
``operation_reason`` and skip with the returned, named reason.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_models import (
    TYPES_FIXTURES,
    AsyncTypedUser,
    AsyncTypedUserAnnotated,
    TypedUser,
    TypedUserAnnotated,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    parallel=True,
    purpose="Scalar types in bare and fully annotated variants, side by side.",
    passes_means="both variants derive a table and round-trip every Python type in the set",
    fails_means="a variant silently changes storage, loses a value, or drifts from its async twin",
)


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
    usable = tuple(fixture for fixture in TYPES_FIXTURES if table_reason(dialect, fixture) is None)
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


@pytest.fixture(name="typed_user_class")
def typed_user_class(database_config):
    """The bare scalar-type model, configured against the directory database."""
    scenario, config, _name = database_config
    TypedUser.configure(config, scenario.backend_class)
    yield TypedUser
    _disconnect(TypedUser)


@pytest.fixture(name="typed_user_annotated_class")
def typed_user_annotated_class(database_config):
    """The annotated scalar-type model, configured against the directory database."""
    scenario, config, _name = database_config
    TypedUserAnnotated.configure(config, scenario.backend_class)
    yield TypedUserAnnotated
    _disconnect(TypedUserAnnotated)


@pytest.fixture(name="async_typed_user_class")
async def async_typed_user_class(database_config):
    """Async twin of the bare scalar-type model."""
    scenario, config, _name = database_config
    await AsyncTypedUser.configure(config, scenario.async_backend_class)
    yield AsyncTypedUser
    await _disconnect_async(AsyncTypedUser)


@pytest.fixture(name="async_typed_user_annotated_class")
async def async_typed_user_annotated_class(database_config):
    """Async twin of the annotated scalar-type model."""
    scenario, config, _name = database_config
    await AsyncTypedUserAnnotated.configure(config, scenario.async_backend_class)
    yield AsyncTypedUserAnnotated
    await _disconnect_async(AsyncTypedUserAnnotated)
