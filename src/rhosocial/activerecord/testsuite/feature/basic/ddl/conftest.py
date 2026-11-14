# src/rhosocial/activerecord/testsuite/feature/basic/ddl/conftest.py
"""L2 environment fixtures for ``basic/ddl``.

The ALTER TABLE contracts only render expressions, so this directory creates
no tables; it still owns one database so the dialect comes from a fully
adapted backend rather than a probe connection.
"""

import pytest


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_ddl"
    return backend_scenario, backend_scenario.make_config(name), name


@pytest.fixture(scope="session")
def database(database_config):
    """The directory's database, prepared once; no tables belong to it."""
    scenario, config, name = database_config
    scenario.reset_database(name)
    backend = scenario.backend_class(connection_config=config)
    backend.connect()
    backend.introspect_and_adapt()
    yield backend
    backend.disconnect()


@pytest.fixture(name="ddl_dialect")
def ddl_dialect(database):
    """The adapted dialect for ALTER TABLE tests.

    A dialect is not sync/async; only the backend is, so sync and async models
    render with this same dialect instance.
    """
    return database.dialect
