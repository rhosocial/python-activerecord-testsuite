# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""

from .operations import Operation, TableFixture
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy

# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.
from rhosocial.activerecord.field import UUIDMixin

try:
    from typing import Annotated, ClassVar  # noqa: F401
except ImportError:
    from typing_extensions import ClassVar


# The composite-key models moved to their own group module; re-export them so
# existing importers of ``fixtures.models`` keep working.
from .composite_pk_models import (  # noqa: F401
    AsyncMappedOrderItem,
    AsyncOrder,
    AsyncOrderItem,
    AsyncStoreInventory,
    MappedOrderItem,
    Order,
    OrderItem,
    StoreInventory,
)

# --- model bodies (moved from models.py) -------------------------------


class TypeCase(UUIDMixin, ActiveRecord):
    """A model with a wide variety of data types to test database type handling."""

    @classmethod
    def table_name(cls):
        return "type_cases"

    username: str
    email: str
    tiny_int: Optional[int]
    small_int: Optional[int]
    big_int: Optional[int]
    float_val: Optional[float]
    double_val: Optional[float]
    decimal_val: Optional[Decimal]
    char_val: Optional[str]
    varchar_val: Optional[str]
    text_val: Optional[str]
    date_val: Optional[date]
    time_val: Optional[time]
    timestamp_val: Optional[datetime]
    blob_val: Optional[bytes]
    json_val: Optional[dict]
    array_val: Optional[list]
    is_active: bool = True


class AsyncTypeCase(UUIDMixin, AsyncActiveRecord):
    """A model with a wide variety of data types to test database type handling."""

    @classmethod
    def table_name(cls):
        return "type_cases"

    c: ClassVar[FieldProxy] = FieldProxy()

    username: str
    email: str
    tiny_int: Optional[int]
    small_int: Optional[int]
    big_int: Optional[int]
    float_val: Optional[float]
    double_val: Optional[float]
    decimal_val: Optional[Decimal]
    char_val: Optional[str]
    varchar_val: Optional[str]
    text_val: Optional[str]
    date_val: Optional[date]
    time_val: Optional[time]
    timestamp_val: Optional[datetime]
    blob_val: Optional[bytes]
    json_val: Optional[dict]
    array_val: Optional[list]
    is_active: bool = True


class TypeTestModel(UUIDMixin, ActiveRecord):
    """Model class for testing various field types"""

    @classmethod
    def table_name(cls):
        return "type_tests"

    # UUID primary key provided by UUIDMixin
    string_field: str = Field(default="test string")
    int_field: int = Field(default=42)
    float_field: float = Field(default=3.14)
    decimal_field: Decimal = Field(default=Decimal("10.99"))
    bool_field: bool = Field(default=True)
    datetime_field: datetime = Field(default_factory=datetime.now)
    json_field: Optional[dict] = None
    nullable_field: Optional[str] = Field(default=None)


class AsyncTypeTestModel(UUIDMixin, AsyncActiveRecord):
    """Model class for testing various field types"""

    @classmethod
    def table_name(cls):
        return "type_tests"

    c: ClassVar[FieldProxy] = FieldProxy()

    # UUID primary key provided by UUIDMixin
    string_field: str = Field(default="test string")
    int_field: int = Field(default=42)
    float_field: float = Field(default=3.14)
    decimal_field: Decimal = Field(default=Decimal("10.99"))
    bool_field: bool = Field(default=True)
    datetime_field: datetime = Field(default_factory=datetime.now)
    json_field: Optional[dict] = None
    nullable_field: Optional[str] = Field(default=None)


_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
TYPE_ROW_FIXTURES = (
    TableFixture(table="type_cases", source=TypeCase, operations=_OPS),
    TableFixture(table="type_tests", source=TypeTestModel, operations=_OPS),
)
