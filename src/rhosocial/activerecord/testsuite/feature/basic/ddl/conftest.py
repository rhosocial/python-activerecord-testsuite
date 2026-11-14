# src/rhosocial/activerecord/testsuite/feature/basic/ddl/conftest.py
"""The ``basic/ddl`` minimal test set.

The ALTER TABLE contracts render expressions only, so the fixture group is
empty: nothing is created and nothing is dropped.  The dialect fixtures come
straight from the scenario and need no connection.
"""
import pytest

from rhosocial.activerecord.testsuite.core.capabilities import dialect_for

GROUP_TABLES = ()


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test (none for this directory)."""


def teardown(environment):
    """Drop the group's tables after every test (none for this directory)."""


@pytest.fixture(name="ddl_dialect")
def ddl_dialect(backend_scenario):
    """Provide the backend dialect for sync ALTER TABLE tests."""
    return dialect_for(backend_scenario)


@pytest.fixture(name="async_ddl_dialect")
def async_ddl_dialect(backend_scenario):
    """Provide the backend dialect for async ALTER TABLE tests."""
    return dialect_for(backend_scenario)
