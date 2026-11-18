# src/rhosocial/activerecord/testsuite/feature/basic/type_adapter/conftest.py
"""L2 environment fixtures for the ``basic/type_adapter`` directory.

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
from rhosocial.activerecord.testsuite.feature.basic.fixtures.type_adapter_models import (
    TYPE_ADAPTER_FIXTURES,
    TYPE_ADAPTER_VARIANT_FIXTURES,
    AdapterRow,
    AdapterRowAnnotated,
    AsyncAdapterRow,
    AsyncAdapterRowAnnotated,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose="Optional and custom type adapters, including boolean raw storage.",
    passes_means="values survive the adapter round-trip with the documented database shape",
    fails_means="an adapter writes a value the backend cannot read back faithfully",
)

_ALL_FIXTURES = TYPE_ADAPTER_FIXTURES + TYPE_ADAPTER_VARIANT_FIXTURES


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


@pytest.fixture(name="adapter_row_class")
def adapter_row_class(database_config):
    """The bare adapter model, configured against the directory database."""
    scenario, config, _name = database_config
    AdapterRow.configure(config, scenario.backend_class)
    yield AdapterRow
    _disconnect(AdapterRow)


@pytest.fixture(name="adapter_row_annotated_class")
def adapter_row_annotated_class(database_config):
    """The annotated adapter model, configured against the directory database."""
    scenario, config, _name = database_config
    AdapterRowAnnotated.configure(config, scenario.backend_class)
    yield AdapterRowAnnotated
    _disconnect(AdapterRowAnnotated)


@pytest.fixture(name="async_adapter_row_class")
async def async_adapter_row_class(database_config):
    """Async twin of the bare adapter model."""
    scenario, config, _name = database_config
    await AsyncAdapterRow.configure(config, scenario.async_backend_class)
    yield AsyncAdapterRow
    await _disconnect_async(AsyncAdapterRow)


@pytest.fixture(name="async_adapter_row_annotated_class")
async def async_adapter_row_annotated_class(database_config):
    """Async twin of the annotated adapter model."""
    scenario, config, _name = database_config
    await AsyncAdapterRowAnnotated.configure(config, scenario.async_backend_class)
    yield AsyncAdapterRowAnnotated
    await _disconnect_async(AsyncAdapterRowAnnotated)
