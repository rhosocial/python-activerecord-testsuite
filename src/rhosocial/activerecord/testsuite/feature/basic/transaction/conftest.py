# src/rhosocial/activerecord/testsuite/feature/basic/transaction/conftest.py
"""The ``basic/transaction`` minimal test set.

The transaction tests use the same pool and model shape as the connection
tests, so this module reuses that fixture declaration and prepares the same
table group.
"""
from rhosocial.activerecord.testsuite.feature.basic.connection.conftest import (  # noqa: F401
    async_pool_and_model,
    sync_pool_and_model,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures import tables

GROUP_TABLES = ("test_users",)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.BASIC_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))
