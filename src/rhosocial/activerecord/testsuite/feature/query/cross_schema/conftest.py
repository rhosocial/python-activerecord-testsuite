# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/conftest.py
"""Fixtures for cross-schema tests.

A backend opts in by declaring a ``schema_setup`` callable on its scenario
object.  It is called with the environment and a suffix, and returns the
configured models the tests use.  Backends without it skip these tests instead
of emulating schemas they do not have.
"""
import pytest

from rhosocial.activerecord.testsuite.feature.query.fixtures import tables

# No tables belong to this group: only capability-gated tests live here, and
# they provision their cross-schema models themselves.
GROUP_TABLES = ()


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.QUERY_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


def schema_setup(environment):
    """Return the backend's cross-schema setup callable, or skip."""
    setup = getattr(environment.scenario, "schema_setup", None)
    if setup is None:
        pytest.skip("backend does not declare cross-schema fixtures")
    return setup


@pytest.fixture(name="schema_fixtures")
def schema_fixtures(environment):
    return schema_setup(environment)(environment, "schema")


@pytest.fixture(name="async_schema_fixtures")
async def async_schema_fixtures(environment):
    return schema_setup(environment)(environment, "async_schema")


@pytest.fixture(name="mixed_schema_fixtures")
def mixed_schema_fixtures(environment):
    return schema_setup(environment)(environment, "mixed_schema")


@pytest.fixture(name="async_mixed_schema_fixtures")
async def async_mixed_schema_fixtures(environment):
    return schema_setup(environment)(environment, "async_mixed_schema")
