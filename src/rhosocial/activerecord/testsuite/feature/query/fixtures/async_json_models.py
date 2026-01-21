from decimal import Decimal
from typing import Optional, ClassVar, Dict, Any, List

from pydantic import Field

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin


class AsyncJsonUser(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async User model specialized for JSON testing."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "json_users"

    id: Optional[int] = None
    username: str
    email: str
    age: Optional[int] = Field(..., ge=0, le=100)
    # JSON fields
    settings: Optional[Dict[str, Any]] = Field(default={})
    tags: Optional[List[str]] = Field(default=[])
    profile: Optional[Dict[str, Any]] = Field(default={})
    roles: Optional[List[str]] = Field(default=[])
    scores: Optional[List[int]] = Field(default=[])
    subscription: Optional[Dict[str, Any]] = Field(default={})
    preferences: Optional[Dict[str, Any]] = Field(default={})