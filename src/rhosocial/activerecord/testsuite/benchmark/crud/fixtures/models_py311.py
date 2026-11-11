"""Python 3.11+ models for CRUD benchmark scenarios."""

from typing import ClassVar

from pydantic import EmailStr, Field

from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class BenchmarkUser(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    @classmethod
    def table_name(cls):
        return "benchmark_users"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: int | None = None
    username: str
    email: EmailStr
    age: int | None = Field(..., ge=0, le=120)
    balance: float = 0.0
    notes: str | None = None
    is_active: bool = True


class AsyncBenchmarkUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "benchmark_users"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: int | None = None
    username: str
    email: EmailStr
    age: int | None = Field(..., ge=0, le=120)
    balance: float = 0.0
    notes: str | None = None
    is_active: bool = True
