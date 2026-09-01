"""Python 3.8-compatible models for CRUD benchmark scenarios."""

from typing import ClassVar, Optional

from pydantic import EmailStr, Field

from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class BenchmarkUser(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    __table_name__ = "benchmark_users"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=120)
    balance: float = 0.0
    notes: Optional[str] = None
    is_active: bool = True


class AsyncBenchmarkUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    __table_name__ = "benchmark_users"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=120)
    balance: float = 0.0
    notes: Optional[str] = None
    is_active: bool = True
