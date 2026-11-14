# src/rhosocial/activerecord/testsuite/feature/relation/ordering/conftest.py
"""The ``relation/ordering`` minimal test set.

The directory owns one database (named after its path) and one fixture group.
Every test prepares the whole group, even when it only uses part of it.
"""
from rhosocial.activerecord.testsuite.feature.relation.fixtures import tables

GROUP_TABLES = (
    "users",
    "posts",
    "comments",
)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.RELATION_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))
