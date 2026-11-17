# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/pydantic_native_models.py
"""DB-free Pydantic-native contract models for the ``basic/validation`` group.

This module is the single declaration site for the models used by
``test_pydantic_native_validation.py`` and its async twin.  Before this file
existed, both test modules carried the same ~400-line model block verbatim;
the sync file then instantiated the ``*Model`` names and the async file the
``Async*Model`` names.  Keeping the two declaration sets here (P4: one field
mixin per concept, a sync and an async concrete class sharing it) removes that
duplication while preserving every name the two test bodies use.

These models are pure contract probes: they are never configured with a
backend and no DDL is derived from them, so they carry no primary key and no
storage annotations beyond the ``UseColumn`` markers the tests explicitly
assert.  ``valid_pydantic_data()`` is shared for the same reason.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseColumn
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

try:
    from typing import Annotated
except ImportError:  # pragma: no cover - Python 3.8 baseline
    from typing_extensions import Annotated


# --- mutable default isolation -------------------------------------------


class MutableDefaultFieldsMixin:
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MutableDefaultModel(MutableDefaultFieldsMixin, ActiveRecord):
    """Model for Pydantic mutable default isolation tests."""

    @classmethod
    def table_name(cls):
        return "mutable_default_models"


class AsyncMutableDefaultModel(MutableDefaultFieldsMixin, AsyncActiveRecord):
    """Async model for Pydantic mutable default isolation tests."""

    @classmethod
    def table_name(cls):
        return "mutable_default_models"


# --- lifecycle / unset-vs-None -------------------------------------------


class LifecycleFieldsMixin:
    required_name: str
    optional_note: Optional[str] = None
    derived_name: Optional[str] = None

    @model_validator(mode="after")
    def derive_name(self):
        self.derived_name = self.required_name.upper()
        return self

    @property
    def post_init_seen(self) -> bool:
        return self._post_init_seen

    def model_post_init(self, __context: object) -> None:
        _ = __context
        self._post_init_seen = True


class LifecycleModel(LifecycleFieldsMixin, ActiveRecord):
    """Model for Pydantic lifecycle and unset/None tests."""

    # PrivateAttr must be declared on the concrete model: Pydantic only
    # collects private attributes from the class being built, not from a
    # plain (non-BaseModel) mixin.
    _post_init_seen: bool = PrivateAttr(default=False)

    @classmethod
    def table_name(cls):
        return "lifecycle_models"


class AsyncLifecycleModel(LifecycleFieldsMixin, AsyncActiveRecord):
    """Async model for Pydantic lifecycle and unset/None tests."""

    _post_init_seen: bool = PrivateAttr(default=False)

    @classmethod
    def table_name(cls):
        return "lifecycle_models"


# --- Pydantic v2 serialization / Annotated metadata boundary -------------


class PydanticV2BoundaryFieldsMixin:
    first_name: str
    last_name: str
    score: Decimal
    annotated_code: Annotated[str, Field(min_length=2), UseColumn("annotated_code_col")]

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @field_serializer("score")
    def serialize_score(self, value: Decimal) -> str:
        return f"score:{value}"


class PydanticV2BoundaryModel(PydanticV2BoundaryFieldsMixin, ActiveRecord):
    """Model for Pydantic v2 serialization and Annotated metadata boundary tests."""

    @classmethod
    def table_name(cls):
        return "pydantic_v2_boundary_models"


class AsyncPydanticV2BoundaryModel(PydanticV2BoundaryFieldsMixin, AsyncActiveRecord):
    """Async model for Pydantic v2 serialization and Annotated metadata boundary tests."""

    @classmethod
    def table_name(cls):
        return "pydantic_v2_boundary_models"


# --- alias boundaries -----------------------------------------------------


class AliasBoundaryFieldsMixin:
    model_config = ConfigDict(populate_by_name=True)

    external_id: Annotated[int, UseColumn("external_id_col")] = Field(alias="externalId")
    display_name: str = Field(validation_alias="inputName")
    public_name: str = Field(serialization_alias="outputName")


class AliasBoundaryModel(AliasBoundaryFieldsMixin, ActiveRecord):
    """Model for alias and UseColumn boundary tests."""

    @classmethod
    def table_name(cls):
        return "alias_boundary_models"


class AsyncAliasBoundaryModel(AliasBoundaryFieldsMixin, AsyncActiveRecord):
    """Async model for alias and UseColumn boundary tests."""

    @classmethod
    def table_name(cls):
        return "alias_boundary_models"


# --- extra config modes ---------------------------------------------------


class ExtraForbidFieldsMixin:
    model_config = ConfigDict(extra="forbid")

    name: str


class ExtraForbidModel(ExtraForbidFieldsMixin, ActiveRecord):
    """Model that rejects unknown Pydantic input fields."""

    @classmethod
    def table_name(cls):
        return "extra_forbid_models"


class AsyncExtraForbidModel(ExtraForbidFieldsMixin, AsyncActiveRecord):
    """Async model that rejects unknown Pydantic input fields."""

    @classmethod
    def table_name(cls):
        return "extra_forbid_models"


class ExtraIgnoreFieldsMixin:
    model_config = ConfigDict(extra="ignore")

    name: str


class ExtraIgnoreModel(ExtraIgnoreFieldsMixin, ActiveRecord):
    """Model that ignores unknown Pydantic input fields."""

    @classmethod
    def table_name(cls):
        return "extra_ignore_models"


class AsyncExtraIgnoreModel(ExtraIgnoreFieldsMixin, AsyncActiveRecord):
    """Async model that ignores unknown Pydantic input fields."""

    @classmethod
    def table_name(cls):
        return "extra_ignore_models"


class ExtraAllowFieldsMixin:
    model_config = ConfigDict(extra="allow")

    name: str


class ExtraAllowModel(ExtraAllowFieldsMixin, ActiveRecord):
    """Model that keeps unknown Pydantic input fields as model extras."""

    @classmethod
    def table_name(cls):
        return "extra_allow_models"


class AsyncExtraAllowModel(ExtraAllowFieldsMixin, AsyncActiveRecord):
    """Async model that keeps unknown Pydantic input fields as model extras."""

    @classmethod
    def table_name(cls):
        return "extra_allow_models"


# --- strict / validate_default -------------------------------------------


class StrictFieldsMixin:
    count: int = Field(strict=True)
    enabled: bool = Field(strict=True)


class StrictModel(StrictFieldsMixin, ActiveRecord):
    """Model for strict Pydantic validation tests."""

    @classmethod
    def table_name(cls):
        return "strict_models"


class AsyncStrictModel(StrictFieldsMixin, AsyncActiveRecord):
    """Async model for strict Pydantic validation tests."""

    @classmethod
    def table_name(cls):
        return "strict_models"


class ValidateDefaultFieldsMixin:
    positive_count: int = Field(default=0, gt=0, validate_default=True)


class ValidateDefaultModel(ValidateDefaultFieldsMixin, ActiveRecord):
    """Model for validate_default pipeline tests."""

    @classmethod
    def table_name(cls):
        return "validate_default_models"


class AsyncValidateDefaultModel(ValidateDefaultFieldsMixin, AsyncActiveRecord):
    """Async model for validate_default pipeline tests."""

    @classmethod
    def table_name(cls):
        return "validate_default_models"


# --- validator pipeline modes --------------------------------------------


class ValidatorModesFieldsMixin:
    raw_code: str
    normalized_code: str
    wrapped_code: str
    combined: Optional[str] = None

    @model_validator(mode="before")
    def derive_combined(cls, data: Any) -> Any:
        if isinstance(data, dict) and "combined" not in data:
            data = {
                **data,
                "combined": f"{data.get('raw_code', '')}:{data.get('normalized_code', '')}",
            }
        return data

    @field_validator("raw_code", mode="before")
    def strip_raw_code(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("normalized_code", mode="after")
    def normalize_after_type_conversion(cls, value: str) -> str:
        return value.lower()

    @field_validator("wrapped_code", mode="wrap")
    def wrap_code(cls, value: Any, handler):
        handled = handler(value)
        return f"wrapped:{handled.strip().lower()}"


class ValidatorModesModel(ValidatorModesFieldsMixin, ActiveRecord):
    """Model for Pydantic validator pipeline mode tests."""

    @classmethod
    def table_name(cls):
        return "validator_modes_models"


class AsyncValidatorModesModel(ValidatorModesFieldsMixin, AsyncActiveRecord):
    """Async model for Pydantic validator pipeline mode tests."""

    @classmethod
    def table_name(cls):
        return "validator_modes_models"


# --- JSON / enum / nested containers -------------------------------------


class RecordStatus(str, Enum):
    draft = "draft"
    active = "active"


class AddressPayload(BaseModel):
    city: str = Field(min_length=2)
    zip_code: str = Field(pattern=r"^\d{5}$")


class JsonContainerNestedFieldsMixin:
    status: RecordStatus
    created_at: datetime
    address: AddressPayload
    labels: List[Annotated[str, Field(min_length=2)]]
    scores: Dict[str, Annotated[int, Field(ge=0, le=100)]]


class JsonContainerNestedModel(JsonContainerNestedFieldsMixin, ActiveRecord):
    """Model for JSON dump, enum, container, and nested model tests."""

    @classmethod
    def table_name(cls):
        return "json_container_nested_models"


class AsyncJsonContainerNestedModel(JsonContainerNestedFieldsMixin, AsyncActiveRecord):
    """Async model for JSON dump, enum, container, and nested model tests."""

    @classmethod
    def table_name(cls):
        return "json_container_nested_models"


# --- from_attributes ------------------------------------------------------


class FromAttributesFieldsMixin:
    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: int


class FromAttributesModel(FromAttributesFieldsMixin, ActiveRecord):
    """Model for from_attributes construction tests."""

    @classmethod
    def table_name(cls):
        return "from_attributes_models"


class AsyncFromAttributesModel(FromAttributesFieldsMixin, AsyncActiveRecord):
    """Async model for from_attributes construction tests."""

    @classmethod
    def table_name(cls):
        return "from_attributes_models"


# --- Annotated metadata order --------------------------------------------


class AnnotatedMetadataOrderFieldsMixin:
    field_first: Annotated[str, Field(min_length=2), UseColumn("field_first_col")]
    column_first: Annotated[str, UseColumn("column_first_col"), Field(min_length=2)]


class AnnotatedMetadataOrderModel(AnnotatedMetadataOrderFieldsMixin, ActiveRecord):
    """Model for Annotated metadata ordering tests."""

    @classmethod
    def table_name(cls):
        return "annotated_metadata_order_models"


class AsyncAnnotatedMetadataOrderModel(AnnotatedMetadataOrderFieldsMixin, AsyncActiveRecord):
    """Async model for Annotated metadata ordering tests."""

    @classmethod
    def table_name(cls):
        return "annotated_metadata_order_models"


# --- alias / UseColumn conflict ------------------------------------------


class AliasUseColumnConflictFieldsMixin:
    model_config = ConfigDict(populate_by_name=True)

    c: ClassVar[FieldProxy] = FieldProxy()
    same_name: Annotated[str, UseColumn("externalName")] = Field(alias="externalName")
    different_name: Annotated[str, UseColumn("db_different_name")] = Field(alias="apiDifferentName")


class AliasUseColumnConflictModel(AliasUseColumnConflictFieldsMixin, ActiveRecord):
    """Model for alias and UseColumn conflict boundary tests."""

    @classmethod
    def table_name(cls):
        return "alias_use_column_conflict_models"


class AsyncAliasUseColumnConflictModel(AliasUseColumnConflictFieldsMixin, AsyncActiveRecord):
    """Async model for alias and UseColumn conflict boundary tests."""

    @classmethod
    def table_name(cls):
        return "alias_use_column_conflict_models"


# --- validate_assignment / dirty tracking --------------------------------


class AssignmentValidationFieldsMixin:
    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(min_length=2)
    quantity: int = Field(ge=1)


class AssignmentValidationModel(AssignmentValidationFieldsMixin, ActiveRecord):
    """Model for assignment validation and dirty tracking tests."""

    @classmethod
    def table_name(cls):
        return "assignment_validation_models"


class AsyncAssignmentValidationModel(AssignmentValidationFieldsMixin, AsyncActiveRecord):
    """Async model for assignment validation and dirty tracking tests."""

    @classmethod
    def table_name(cls):
        return "assignment_validation_models"


# --- shared data ----------------------------------------------------------


def valid_pydantic_data():
    start_at = datetime(2024, 1, 1, 10, 0, 0)
    return {
        "code": "ABC-123",
        "quantity": 5,
        "step_count": 10,
        "price": Decimal("12.50"),
        "start_at": start_at,
        "end_at": start_at + timedelta(hours=1),
        "status": "draft",
        "normalized_name": "  Alice  ",
    }


__all__ = [
    "AddressPayload",
    "AliasBoundaryFieldsMixin",
    "AliasBoundaryModel",
    "AliasUseColumnConflictFieldsMixin",
    "AliasUseColumnConflictModel",
    "AnnotatedMetadataOrderFieldsMixin",
    "AnnotatedMetadataOrderModel",
    "AssignmentValidationFieldsMixin",
    "AssignmentValidationModel",
    "AsyncAliasBoundaryModel",
    "AsyncAliasUseColumnConflictModel",
    "AsyncAnnotatedMetadataOrderModel",
    "AsyncAssignmentValidationModel",
    "AsyncExtraAllowModel",
    "AsyncExtraForbidModel",
    "AsyncExtraIgnoreModel",
    "AsyncFromAttributesModel",
    "AsyncJsonContainerNestedModel",
    "AsyncLifecycleModel",
    "AsyncMutableDefaultModel",
    "AsyncPydanticV2BoundaryModel",
    "AsyncStrictModel",
    "AsyncValidateDefaultModel",
    "AsyncValidatorModesModel",
    "ExtraAllowModel",
    "ExtraForbidModel",
    "ExtraIgnoreModel",
    "FromAttributesModel",
    "JsonContainerNestedModel",
    "LifecycleModel",
    "MutableDefaultModel",
    "PydanticV2BoundaryModel",
    "RecordStatus",
    "StrictModel",
    "ValidateDefaultModel",
    "ValidatorModesModel",
    "valid_pydantic_data",
]
