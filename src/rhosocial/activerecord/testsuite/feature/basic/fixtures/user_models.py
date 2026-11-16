# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/user_models.py
"""The ``users`` table: its model, its twin, and its fixture registration.

The model bodies still live in ``models.py`` alongside the other 3.8-baseline
classes; this module owns the fixture registration that derives the table from
``User`` instead of a hand-written ``UserDefinition``. Moving the remaining
model bodies here is a later stage of the fixtures redesign.
"""

from .models import AsyncUser, BulkUser, User, ValidatedUser
from .operations import Operation, TableFixture

_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))

#: The model classes behind the tables the CLI feature borrows from basic.
#: This replaces ``BASIC_DEFINITIONS``: a table is named by the model that
#: derives it, not by a second hand-written column list.
BASIC_TABLES = (User, BulkUser, ValidatedUser)

USER_FIXTURES = (TableFixture(table="users", source=User, operations=_OPS),)

#: The CLI feature borrows three basic tables; it derives them from models too.
BASIC_FIXTURES = USER_FIXTURES + (
    TableFixture(table="bulk_users", source=BulkUser, operations=_OPS),
    TableFixture(table="validated_users", source=ValidatedUser, operations=_OPS),
)

__all__ = [
    "AsyncUser",
    "BASIC_FIXTURES",
    "BASIC_TABLES",
    "USER_FIXTURES",
    "User",
]
