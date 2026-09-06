# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_json_models.py
"""Async JSON-field model fixtures for query feature tests."""

from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin


class AsyncJsonUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async User model specialized for JSON testing."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "json_users"

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=100)

    # JSON fields
    settings: Optional[str] = None
    tags: Optional[str] = None
    profile: Optional[str] = None
    roles: Optional[str] = None
    scores: Optional[str] = None
    subscription: Optional[str] = None
    preferences: Optional[str] = None
