# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/connection_models.py
"""The ``test_users`` table: the connection-pool group's model and fixture.

The model previously lived in ``feature/basic/connection/fixtures.py`` while
its DDL lived in ``fixtures/models.py``. Both halves are here now, and the
old module re-exports the names so the public fixture surface is unchanged.
"""

from typing import Optional

try:  # Python 3.8
    from typing import Annotated
except ImportError:  # pragma: no cover
    from typing_extensions import Annotated

from rhosocial.activerecord.base.fields import UseSqlType
from rhosocial.activerecord.backend.expression.types import IntegerType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from .operations import Operation, TableFixture


class TestUser(ActiveRecord):
    __primary_key__ = "id"
    @classmethod
    def table_name(cls):
        return "test_users"

    id: Annotated[
        Optional[int], UseSqlType(IntegerType())
    ] = None
    name: str
    email: str


class AsyncTestUser(AsyncActiveRecord):
    __primary_key__ = "id"
    @classmethod
    def table_name(cls):
        return "test_users"

    id: Annotated[
        Optional[int], UseSqlType(IntegerType())
    ] = None
    name: str
    email: str


TEST_USER_FIXTURES = (
    TableFixture(
        table="test_users",
        source=TestUser,
        operations=(Operation("create_table"), Operation("insert"), Operation("drop_table")),
    ),
)

__all__ = ["AsyncTestUser", "TEST_USER_FIXTURES", "TestUser"]
