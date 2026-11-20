# src/rhosocial/activerecord/testsuite/feature/basic/types_long_content/conftest.py
"""L2 environment fixtures for the ``basic/types_long_content`` directory.

The shape follows ``basic/crud/conftest.py``: one database per directory, the
``long_rows`` table recreated for every test. The one addition is a capability
gate in ``schema``: a dialect that cannot render one of the four content
concepts would fail while *building* the table, so the group skips before DDL
runs and names the column and concept that refused it.
"""

from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
    table_reason,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_long_content_models import (
    LONG_CONTENT_FIXTURES,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration
from rhosocial.activerecord.testsuite.pytest_plugin.requirements import (
    MissingRequirementError,
)

DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose="Long content in TEXT/BLOB/JSON/XML columns declared as a minimum capacity.",
    passes_means="a 16 000-character/byte value is written and read back in full",
    fails_means="a content column silently truncates or the wrong storage tier is chosen",
)


def _database_name() -> str:
    """Database name from this directory's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


def _unsupported_reason(dialect):
    """Why ``long_rows`` cannot be built on *dialect*, or ``None``.

    ``table_reason`` answers "no" through the dialect's concept table. A
    dialect that offers a *substitute* instead of a formatter (SQLite stores XML
    as text but refuses an ``XmlType`` declaration) never names the concept in
    either channel, so ``switch_answer`` raises. That answer is still a refusal
    of this declaration, so it becomes a skip reason rather than an error.
    """
    try:
        return table_reason(dialect, LONG_CONTENT_FIXTURES[0])
    except MissingRequirementError as error:
        return "{} cannot declare the requested content type ({})".format(
            getattr(dialect, "name", type(dialect).__name__), error
        )


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
    """Prepare ``long_rows`` for a DB test, unless the dialect refuses it.

    Deliberately not autouse: declaration-only assertions need no database and
    must still run on dialects that cannot render XML.
    """
    why = _unsupported_reason(database.dialect)
    if why is not None:
        pytest.skip(why)
    create_schema(database, LONG_CONTENT_FIXTURES)
    yield
    drop_schema(database, LONG_CONTENT_FIXTURES)


@pytest.fixture(name="long_row_class")
def long_row_class(database_config):
    """The configured synchronous model for ``long_rows``."""
    from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_long_content_models import (
        LongRow,
    )

    scenario, config, _name = database_config
    LongRow.configure(config, scenario.backend_class)
    yield LongRow
    _disconnect(LongRow)


@pytest.fixture(name="async_long_row_class")
async def async_long_row_class(database_config):
    """The configured asynchronous model for ``long_rows``."""
    from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_long_content_models import (
        AsyncLongRow,
    )

    scenario, config, _name = database_config
    await AsyncLongRow.configure(config, scenario.async_backend_class)
    yield AsyncLongRow
    await _disconnect_async(AsyncLongRow)
