# src/rhosocial/activerecord/testsuite/feature/cli/fixtures.py
"""CLI-specific models that do not need new database schemas."""
from rhosocial.activerecord.field import IntegerPKMixin

from typing import Optional

from rhosocial.activerecord.field import ReadOnlyMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class CLIReadOnlyUser(IntegerPKMixin, ActiveRecord, ReadOnlyMixin):
    """Read-only view of the standard ``users`` table."""

    @classmethod
    def table_name(cls):
        return "users"

    id: Optional[int] = None
    username: str = ""


class AsyncCLIReadOnlyUser(IntegerPKMixin, AsyncActiveRecord, ReadOnlyMixin):
    """Async read-only view of the standard ``users`` table."""

    @classmethod
    def table_name(cls):
        return "users"

    id: Optional[int] = None
    username: str = ""
