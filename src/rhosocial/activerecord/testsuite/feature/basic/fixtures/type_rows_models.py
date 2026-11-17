# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""

from .operations import Operation, TableFixture
import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    BigIntType,
    BlobType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    SmallIntType,
    TextType,
    TimeType,
    TimestampType,
    TinyIntType,
    VarCharType,
)
from rhosocial.activerecord.base.fields import UseSqlType
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

    # UUID primary key stored as a 64-char string, matching the
    # adapter and the original Definition's VarChar(64).
    id: Annotated[uuid.UUID, UseSqlType(VarCharType(length=64))] = Field(default_factory=uuid.uuid4)
    username: str
    email: str
    tiny_int: Annotated[Optional[int], UseSqlType(TinyIntType())]
    small_int: Annotated[Optional[int], UseSqlType(SmallIntType())]
    big_int: Annotated[Optional[int], UseSqlType(BigIntType())]
    float_val: Annotated[Optional[float], UseSqlType(FloatType())]
    double_val: Annotated[Optional[float], UseSqlType(DoubleType())]
    decimal_val: Annotated[Optional[Decimal], UseSqlType(DecimalType(precision=10, scale=4))]
    char_val: Annotated[Optional[str], UseSqlType(VarCharType(length=64))]
    varchar_val: Annotated[Optional[str], UseSqlType(VarCharType(length=64))]
    text_val: Annotated[Optional[str], UseSqlType(TextType())]
    date_val: Annotated[Optional[date], UseSqlType(DateType())]
    time_val: Annotated[Optional[time], UseSqlType(TimeType())]
    timestamp_val: Annotated[Optional[datetime], UseSqlType(TimestampType())]
    blob_val: Annotated[Optional[bytes], UseSqlType(BlobType())]
    json_val: Optional[dict]
    # Native array with integer elements on servers that render ARRAY;
    # on servers without it, fall back to the JSON/text carrier (the
    # adapter keeps the list type). This mirrors the original Definition's
    # dialect-aware array_type(Int) factory.
    array_val: Annotated[
        Optional[list],
        UseSqlType(ArrayType(element_type=IntegerType()), TextType()),
    ]
    is_active: bool = True


class AsyncTypeCase(UUIDMixin, AsyncActiveRecord):
    """A model with a wide variety of data types to test database type handling."""

    @classmethod
    def table_name(cls):
        return "type_cases"

    c: ClassVar[FieldProxy] = FieldProxy()

    # UUID primary key stored as a 64-char string, matching the
    # adapter and the original Definition's VarChar(64).
    id: Annotated[uuid.UUID, UseSqlType(VarCharType(length=64))] = Field(default_factory=uuid.uuid4)
    username: str
    email: str
    tiny_int: Annotated[Optional[int], UseSqlType(TinyIntType())]
    small_int: Annotated[Optional[int], UseSqlType(SmallIntType())]
    big_int: Annotated[Optional[int], UseSqlType(BigIntType())]
    float_val: Annotated[Optional[float], UseSqlType(FloatType())]
    double_val: Annotated[Optional[float], UseSqlType(DoubleType())]
    decimal_val: Annotated[Optional[Decimal], UseSqlType(DecimalType(precision=10, scale=4))]
    char_val: Annotated[Optional[str], UseSqlType(VarCharType(length=64))]
    varchar_val: Annotated[Optional[str], UseSqlType(VarCharType(length=64))]
    text_val: Annotated[Optional[str], UseSqlType(TextType())]
    date_val: Annotated[Optional[date], UseSqlType(DateType())]
    time_val: Annotated[Optional[time], UseSqlType(TimeType())]
    timestamp_val: Annotated[Optional[datetime], UseSqlType(TimestampType())]
    blob_val: Annotated[Optional[bytes], UseSqlType(BlobType())]
    json_val: Optional[dict]
    # Native array with integer elements on servers that render ARRAY;
    # on servers without it, fall back to the JSON/text carrier (the
    # adapter keeps the list type). This mirrors the original Definition's
    # dialect-aware array_type(Int) factory.
    array_val: Annotated[
        Optional[list],
        UseSqlType(ArrayType(element_type=IntegerType()), TextType()),
    ]
    is_active: bool = True


class TypeTestModel(UUIDMixin, ActiveRecord):
    """Model class for testing various field types"""

    @classmethod
    def table_name(cls):
        return "type_tests"

    # UUID primary key provided by UUIDMixin
    # UUID primary key stored as a 64-char string, matching the
    # adapter and the original Definition's VarChar(64).
    id: Annotated[uuid.UUID, UseSqlType(VarCharType(length=64))] = Field(default_factory=uuid.uuid4)
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
    # UUID primary key stored as a 64-char string, matching the
    # adapter and the original Definition's VarChar(64).
    id: Annotated[uuid.UUID, UseSqlType(VarCharType(length=64))] = Field(default_factory=uuid.uuid4)
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
