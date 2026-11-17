# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/validation_models.py
"""Validation fixtures for the ``basic/validation`` group.

The group has one bare/annotated pair sharing a single table (``validated_rows``):

* ``PlainValidatedRow`` / ``AsyncPlainValidatedRow`` write only Python type
  annotations -- a control that accepts any value of the right Python type.
* ``ValidatedRow`` / ``AsyncValidatedRow`` add Pydantic ``Field`` constraints,
  a ``field_validator`` and a ``model_validator``.  Those are validation
  semantics, not storage declarations (README section 2 P2), so both models
  derive the very same table and the tests compare behavior, not DDL.

Identity is not a variant axis (F11).  Sync and async twins share one mixin
per variant (P4).  The legacy ``PydanticValidatedModel`` stays on its own
``pydantic_validated_models`` table for the existing DB validation contracts.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional, Tuple

from pydantic import Field, field_validator, model_validator
from rhosocial.activerecord.backend.expression.types import (
    DecimalType,
    IntegerType,
    TextType,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseSqlType
from rhosocial.activerecord.field import IntegerPKMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .operations import Operation, TableFixture
from .user_models import ValidatedUser

try:
    from typing import Annotated, ClassVar  # noqa: F401
except ImportError:
    from typing_extensions import Annotated  # noqa: F401


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


class PydanticValidatedFieldsMixin:
    """Shared Pydantic fields and validators for sync/async contract tests."""

    c: ClassVar[FieldProxy] = FieldProxy()
    code: str = Field(
        ...,
        pattern=r"^[A-Z]{3}-\d{3}$",
        title="Validation code",
        description="Business code used by Pydantic compatibility tests.",
        json_schema_extra={"active_record_test": "pydantic-native"},
    )
    quantity: int = Field(..., ge=1, le=999)
    step_count: int = Field(..., gt=0, lt=100, multiple_of=5)
    price: Annotated[Decimal, UseSqlType(DecimalType(precision=12, scale=4))] = Field(
        ..., ge=Decimal("0.01")
    )
    start_at: datetime
    end_at: datetime
    status: Annotated[
        Literal["draft", "active", "archived"],
        UseSqlType(TextType()),
    ] = "draft"
    normalized_name: str = Field(..., min_length=1, max_length=50)
    created_token: str = Field(default_factory=lambda: "generated-token")

    @field_validator("normalized_name")
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class PydanticValidatedModel(PydanticValidatedFieldsMixin, IntegerPKMixin, ActiveRecord):
    """Model for Pydantic native validation contract tests."""

    @classmethod
    def table_name(cls):
        return "pydantic_validated_models"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None


class AsyncPydanticValidatedModel(PydanticValidatedFieldsMixin, IntegerPKMixin, AsyncActiveRecord):
    """Async model for Pydantic native validation contract tests."""

    @classmethod
    def table_name(cls):
        return "pydantic_validated_models"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None


# --- bare / annotated validation variants (shared table) ---------------------


class PlainValidatedRowFields:
    """Bare fields: Python annotations only, zero validation markers."""

    id: Optional[int] = None
    code: str
    quantity: int
    price: Decimal
    label: str


class ValidatedRowFields:
    """Annotated fields: Pydantic constraints and validators.

    No storage declaration is added, so this model derives the very same
    ``validated_rows`` table as :class:`PlainValidatedRowFields`.  The test
    compares what each model accepts, not how it stores the value.
    """

    id: Optional[int] = None
    code: str = Field(..., pattern=r"^[A-Z]{3}-\d{3}$")
    quantity: int = Field(..., ge=1, le=999)
    price: Decimal = Field(..., ge=Decimal("0.01"))
    label: str = Field(..., min_length=1, max_length=50)

    @field_validator("label")
    def normalize_label(cls, value: str) -> str:
        return value.strip().lower()


class PlainValidatedRow(PlainValidatedRowFields, ActiveRecord):
    """Bare validation variant, bound to ``validated_rows``."""

    @classmethod
    def table_name(cls):
        return "validated_rows"


class AsyncPlainValidatedRow(PlainValidatedRowFields, AsyncActiveRecord):
    """Async twin of :class:`PlainValidatedRow` (P4: same fields, same table)."""

    @classmethod
    def table_name(cls):
        return "validated_rows"


class ValidatedRow(ValidatedRowFields, ActiveRecord):
    """Pydantic-annotated validation variant, bound to ``validated_rows``."""

    @classmethod
    def table_name(cls):
        return "validated_rows"


class AsyncValidatedRow(ValidatedRowFields, AsyncActiveRecord):
    """Async twin of :class:`ValidatedRow` (P4)."""

    @classmethod
    def table_name(cls):
        return "validated_rows"


# --- Module-level definitions for TypeAdapterTest and YesOrNoBooleanAdapter ---

_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
VALIDATION_FIXTURES = (
    TableFixture(table="validated_users", source=ValidatedUser, operations=_OPS),
    TableFixture(table="pydantic_validated_models", source=PydanticValidatedModel, operations=_OPS),
)

_VALIDATION_COLUMN_SWITCHES = (
    ("id", "integer"),
    ("code", "varchar"),
    ("quantity", "integer"),
    ("price", "decimal"),
    ("label", "varchar"),
)
_VALIDATION_COLUMN_OPS = tuple(
    Operation("create_table", requires_on=(switch,), column=column)
    for column, switch in _VALIDATION_COLUMN_SWITCHES
)
VALIDATION_VARIANT_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(
        table="validated_rows",
        source=PlainValidatedRow,
        operations=_OPS + _VALIDATION_COLUMN_OPS,
    ),
)

__all__ = [
    "VALIDATION_FIXTURES",
    "VALIDATION_VARIANT_FIXTURES",
    "AsyncPlainValidatedRow",
    "AsyncPydanticValidatedModel",
    "AsyncValidatedRow",
    "PydanticValidatedFieldsMixin",
    "PydanticValidatedModel",
    "PlainValidatedRow",
    "ValidatedRow",
]
