# src/rhosocial/activerecord/testsuite/feature/basic/fields/conftest.py
"""The ``basic/fields`` minimal test set.

The directory owns one database (named after its path) and one fixture group:
the field round-trip table, the mapped and mixed annotation tables, and the
product table the derived-field models share.
"""
from rhosocial.activerecord.testsuite.feature.basic.fixtures import tables

GROUP_TABLES = (
    "users",
    "posts",
    "comments",
    "column_mapping_items",
    "mixed_annotation_items",
    "type_tests",
    "product",
)


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
