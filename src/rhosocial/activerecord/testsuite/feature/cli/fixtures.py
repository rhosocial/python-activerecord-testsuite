# src/rhosocial/activerecord/testsuite/feature/cli/fixtures.py
"""CLI-specific models that do not need new database schemas."""

from typing import Optional

from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class CLIReadOnlyUser(ActiveRecord, ReadOnlyMixin):
    """Read-only view of the standard ``users`` table."""

    __table_name__ = "users"
    id: Optional[int] = None
    username: str = ""


class AsyncCLIReadOnlyUser(AsyncActiveRecord, ReadOnlyMixin):
    """Async read-only view of the standard ``users`` table."""

    __table_name__ = "users"
    id: Optional[int] = None
    username: str = ""
