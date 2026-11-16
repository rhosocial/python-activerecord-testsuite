# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/user_models.py
"""The ``users`` table: its model, its twin, and its fixture registration.

The model bodies still live in ``models.py`` alongside the other 3.8-baseline
classes; this module owns the fixture registration that derives the table from
``User`` instead of a hand-written ``UserDefinition``. Moving the remaining
model bodies here is a later stage of the fixtures redesign.
"""

from .models import AsyncUser, User
from .operations import Operation, TableFixture

USER_FIXTURES = (
    TableFixture(
        table="users",
        source=User,
        operations=(Operation("create_table"), Operation("insert"), Operation("drop_table")),
    ),
)

__all__ = ["AsyncUser", "USER_FIXTURES", "User"]
