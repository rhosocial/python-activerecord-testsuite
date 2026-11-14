# src/rhosocial/activerecord/testsuite/feature/basic/connection/fixtures.py
"""Models used by the connection-pool tests."""
from typing import Optional

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class TestUser(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "test_users"

    id: Optional[int] = None
    name: str
    email: str


class AsyncTestUser(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "test_users"

    id: Optional[int] = None
    name: str
    email: str
