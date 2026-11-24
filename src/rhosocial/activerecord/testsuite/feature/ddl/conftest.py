# src/rhosocial/activerecord/testsuite/feature/ddl/conftest.py
"""L2 environment and model fixtures for the backend-independent ModelDDLDeclaration group.

These tests render statements and inspect declarations; they never create
tables.  They still own one database, because the dialect they render with has
to come from an adapted backend: a dialect nobody adapted cannot answer the
version-gated probes, and the old probe-and-throw-away connection is gone.

- ``database``: one database per directory (session scope), emptied at start;
- ``ddl_dialect``: the adapted dialect every statement is rendered with.
"""
from pathlib import Path

import pytest

from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

from .fixtures.models import (
    AsyncBareItem,
    AsyncCapabilityPost,
    AsyncSpecComment,
    AsyncSpecOrder,
    BareItem,
    CapabilityPost,
    SpecComment,
    SpecOrder,
)

DECLARATION = Declaration(
    # This scope opens a database; the plugin enforces this declaration.
    uses_database=True,
    parallel=True,
    purpose="ModelDDLDeclaration contracts: what a declaration may say and how it renders.",
    passes_means="the declaration surface renders and refuses as documented",
    fails_means="a declaration renders something the backend does not accept, "
    "or accepts something it should refuse",
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
    """Provide a backend dialect instance for statement rendering.

    A dialect is not sync/async; only the backend is.  Async models render with
    this same dialect instance.
    """
    return database.dialect


@pytest.fixture(name="bare_class")
def bare_class():
    return BareItem


@pytest.fixture(name="spec_order_class")
def spec_order_class():
    return SpecOrder


@pytest.fixture(name="capability_class")
def capability_class():
    return CapabilityPost


@pytest.fixture(name="spec_comment_class")
def spec_comment_class():
    return SpecComment


@pytest.fixture(name="async_bare_class")
def async_bare_class():
    return AsyncBareItem


@pytest.fixture(name="async_spec_order_class")
def async_spec_order_class():
    return AsyncSpecOrder


@pytest.fixture(name="async_capability_class")
def async_capability_class():
    return AsyncCapabilityPost


@pytest.fixture(name="async_spec_comment_class")
def async_spec_comment_class():
    return AsyncSpecComment
