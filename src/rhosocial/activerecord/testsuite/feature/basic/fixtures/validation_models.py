# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""

from rhosocial.activerecord.backend.expression.types import TextType

from .operations import Operation, TableFixture
from .user_models import ValidatedUser
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator


from rhosocial.activerecord.base.fields import UseSqlType
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.
from rhosocial.activerecord.field import IntegerPKMixin

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
    price: Decimal = Field(..., ge=Decimal("0.01"))
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

    id: Optional[int] = None


class AsyncPydanticValidatedModel(PydanticValidatedFieldsMixin, IntegerPKMixin, AsyncActiveRecord):
    """Async model for Pydantic native validation contract tests."""

    @classmethod
    def table_name(cls):
        return "pydantic_validated_models"

    id: Optional[int] = None


# --- Module-level definitions for TypeAdapterTest and YesOrNoBooleanAdapter ---

_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
VALIDATION_FIXTURES = (
    TableFixture(table="validated_users", source=ValidatedUser, operations=_OPS),
    TableFixture(table="pydantic_validated_models", source=PydanticValidatedModel, operations=_OPS),
)
