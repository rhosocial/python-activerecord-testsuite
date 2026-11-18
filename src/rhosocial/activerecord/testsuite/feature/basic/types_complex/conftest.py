# src/rhosocial/activerecord/testsuite/feature/basic/types_complex/conftest.py
"""L2 environment fixtures for the ``basic/types_complex`` group.

- ``database``: one database per directory (session scope, emptied at start);
- ``schema``: both complex-type tables are created and dropped for every test,
  so each test starts from empty tables and identity state is reset.

The directory owns two fixture tables (bare and annotated).  Every test
prepares the whole pair, even when it only looks at one of them.
"""

from pathlib import Path

import pytest
from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

from rhosocial.activerecord.base.derivation import build_create_table_statement
from rhosocial.activerecord.testsuite.feature.basic.fixtures.operations import (
    create_schema,
    drop_schema,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.types_complex_models import (
    COMPLEX_FIXTURES,
    AsyncComplexRow,
    AsyncComplexRowAnnotated,
    ComplexRow,
    ComplexRowAnnotated,
)
from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    # This scope needs a prepared database; the L1 gate requests `schema`.
    uses_database=True,
    parallel=True,
    purpose=(
        "Bare and fully annotated complex-type tables: declared storage, "
        "indexes/comments and value round-trips."
    ),
    passes_means=(
        "both variants build and round-trip their declared values, and a "
        "missing dialect capability is named per column"
    ),
    fails_means=("a declared type cannot be built or a round-trip loses/changes a value"),
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)


def _database_name() -> str:
    """Database name from this directory's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory name."""
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


def _unsupported_reason(dialect):
    """Why the complex tables cannot be declared on *dialect*, or ``None``.

    Ask the real question -- can the DDL be built? -- rather than the declared
    ``requires_on`` switches: a backend may store a complex value through a
    substitute (SQLite keeps UUID as text) yet never name the concept in its
    ``supports_data_types()`` table. A dialect that refuses a declaration raises
    during derivation; turn that refusal into a named skip reason.
    """
    for fixture in COMPLEX_FIXTURES:
        if fixture.source is None:
            continue
        try:
            build_create_table_statement(fixture.source, dialect).to_sql()
        except (ValueError, TypeError) as error:
            return "{} cannot declare the complex-type tables ({})".format(
                getattr(dialect, "name", type(dialect).__name__), error
            )
    return None


@pytest.fixture(scope="function", autouse=True)
def schema(database):
    """Drop and recreate the two complex tables when the dialect can build them.

    Deliberately not autouse: declaration-only assertions need no database and
    must still run on dialects that cannot render a complex concept.
    """
    why = _unsupported_reason(database.dialect)
    if why is not None:
        pytest.skip(why)
    create_schema(database, COMPLEX_FIXTURES)
    yield
    drop_schema(database, COMPLEX_FIXTURES)


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


@pytest.fixture(name="complex_bare_class")
def complex_bare_class(schema, database_config):
    """The bare sync model, configured against the directory database."""
    scenario, config, _name = database_config
    ComplexRow.configure(config, scenario.backend_class)
    yield ComplexRow
    _disconnect(ComplexRow)


@pytest.fixture(name="async_complex_bare_class")
async def async_complex_bare_class(schema, database_config):
    """The bare async twin of ``complex_bare_class``."""
    scenario, config, _name = database_config
    await AsyncComplexRow.configure(config, scenario.async_backend_class)
    yield AsyncComplexRow
    await _disconnect_async(AsyncComplexRow)


@pytest.fixture(name="complex_annotated_class")
def complex_annotated_class(schema, database_config):
    """The fully annotated sync model."""
    scenario, config, _name = database_config
    ComplexRowAnnotated.configure(config, scenario.backend_class)
    yield ComplexRowAnnotated
    _disconnect(ComplexRowAnnotated)


@pytest.fixture(name="async_complex_annotated_class")
async def async_complex_annotated_class(schema, database_config):
    """The fully annotated async twin of ``complex_annotated_class``."""
    scenario, config, _name = database_config
    await AsyncComplexRowAnnotated.configure(config, scenario.async_backend_class)
    yield AsyncComplexRowAnnotated
    await _disconnect_async(AsyncComplexRowAnnotated)
