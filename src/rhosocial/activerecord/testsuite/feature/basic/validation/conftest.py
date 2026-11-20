# src/rhosocial/activerecord/testsuite/feature/basic/validation/conftest.py
"""L2 environment fixtures for the ``basic/validation`` directory.

Mirrors ``basic/types/conftest.py``: one database per directory, and a table
whose required storage concept a dialect refuses is left out of
``create_schema`` instead of blowing up in setup.  Tests ask the same registry
through ``table_reason`` / ``operation_reason`` and skip with the named reason.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.validation_models import (
    VALIDATION_FIXTURES,
    VALIDATION_VARIANT_FIXTURES,
    AsyncPlainValidatedRow,
    AsyncValidatedRow,
    PlainValidatedRow,
    ValidatedRow,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose="Pydantic field/model validators and native validation boundaries.",
    passes_means="validation runs on assignment and on save, and invalid values are refused",
    fails_means="an invalid value is persisted or a valid one is rejected",
)

_ALL_FIXTURES = VALIDATION_FIXTURES + VALIDATION_VARIANT_FIXTURES


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


@pytest.fixture(name="plain_validated_row_class")
def plain_validated_row_class(database_config):
    """The bare validation model, configured against the directory database."""
    scenario, config, _name = database_config
    PlainValidatedRow.configure(config, scenario.backend_class)
    yield PlainValidatedRow
    _disconnect(PlainValidatedRow)


@pytest.fixture(name="validated_row_class")
def validated_row_class(database_config):
    """The Pydantic-annotated validation model, configured against the directory database."""
    scenario, config, _name = database_config
    ValidatedRow.configure(config, scenario.backend_class)
    yield ValidatedRow
    _disconnect(ValidatedRow)


@pytest.fixture(name="async_plain_validated_row_class")
async def async_plain_validated_row_class(database_config):
    """Async twin of the bare validation model."""
    scenario, config, _name = database_config
    await AsyncPlainValidatedRow.configure(config, scenario.async_backend_class)
    yield AsyncPlainValidatedRow
    await _disconnect_async(AsyncPlainValidatedRow)


@pytest.fixture(name="async_validated_row_class")
async def async_validated_row_class(database_config):
    """Async twin of the Pydantic-annotated validation model."""
    scenario, config, _name = database_config
    await AsyncValidatedRow.configure(config, scenario.async_backend_class)
    yield AsyncValidatedRow
    await _disconnect_async(AsyncValidatedRow)
