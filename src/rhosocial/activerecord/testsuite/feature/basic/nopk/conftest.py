# src/rhosocial/activerecord/testsuite/feature/basic/nopk/conftest.py
"""The ``basic/nopk`` minimal test set.

Keyless models are projected onto the shared ``users`` table, so this
directory prepares that one table and adds no keyless DDL of its own.
"""
from rhosocial.activerecord.testsuite.feature.basic.fixtures import tables

GROUP_TABLES = ("users",)


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
