# src/rhosocial/activerecord/testsuite/feature/basic/test_pydantic_native_validation.py
"""Tests for Pydantic native validation behavior in ActiveRecord models."""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

import pytest
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError, computed_field, field_serializer, field_validator, model_validator

from rhosocial.activerecord.backend.errors import ValidationError as DBValidationError
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseColumn
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
class MutableDefaultModel(ActiveRecord):
    """Model for Pydantic mutable default isolation tests."""

    __table_name__ = "mutable_default_models"

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AsyncMutableDefaultModel(AsyncActiveRecord):
    """Async model for Pydantic mutable default isolation tests."""

    __table_name__ = "mutable_default_models"

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LifecycleModel(ActiveRecord):
    """Model for Pydantic lifecycle and unset/None tests."""

    __table_name__ = "lifecycle_models"

    required_name: str
    optional_note: Optional[str] = None
    derived_name: Optional[str] = None
    _post_init_seen: bool = PrivateAttr(default=False)

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

class AsyncLifecycleModel(AsyncActiveRecord):
    """Async model for Pydantic lifecycle and unset/None tests."""

    __table_name__ = "lifecycle_models"

    required_name: str
    optional_note: Optional[str] = None
    derived_name: Optional[str] = None
    _post_init_seen: bool = PrivateAttr(default=False)

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

class PydanticV2BoundaryModel(ActiveRecord):
    """Model for Pydantic v2 serialization and Annotated metadata boundary tests."""

    __table_name__ = "pydantic_v2_boundary_models"

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

class AsyncPydanticV2BoundaryModel(AsyncActiveRecord):
    """Async model for Pydantic v2 serialization and Annotated metadata boundary tests."""

    __table_name__ = "pydantic_v2_boundary_models"

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

class AliasBoundaryFieldsMixin:
    model_config = ConfigDict(populate_by_name=True)

    external_id: Annotated[int, UseColumn("external_id_col")] = Field(alias="externalId")
    display_name: str = Field(validation_alias="inputName")
    public_name: str = Field(serialization_alias="outputName")

class AliasBoundaryModel(AliasBoundaryFieldsMixin, ActiveRecord):
    """Model for alias and UseColumn boundary tests."""

    __table_name__ = "alias_boundary_models"

class AsyncAliasBoundaryModel(AliasBoundaryFieldsMixin, AsyncActiveRecord):
    """Async model for alias and UseColumn boundary tests."""

    __table_name__ = "alias_boundary_models"

class ExtraForbidModel(ActiveRecord):
    """Model that rejects unknown Pydantic input fields."""

    __table_name__ = "extra_forbid_models"
    model_config = ConfigDict(extra="forbid")

    name: str

class AsyncExtraForbidModel(AsyncActiveRecord):
    """Async model that rejects unknown Pydantic input fields."""

    __table_name__ = "extra_forbid_models"
    model_config = ConfigDict(extra="forbid")

    name: str

class ExtraIgnoreModel(ActiveRecord):
    """Model that ignores unknown Pydantic input fields."""

    __table_name__ = "extra_ignore_models"
    model_config = ConfigDict(extra="ignore")

    name: str

class AsyncExtraIgnoreModel(AsyncActiveRecord):
    """Async model that ignores unknown Pydantic input fields."""

    __table_name__ = "extra_ignore_models"
    model_config = ConfigDict(extra="ignore")

    name: str

class ExtraAllowModel(ActiveRecord):
    """Model that keeps unknown Pydantic input fields as model extras."""

    __table_name__ = "extra_allow_models"
    model_config = ConfigDict(extra="allow")

    name: str

class AsyncExtraAllowModel(AsyncActiveRecord):
    """Async model that keeps unknown Pydantic input fields as model extras."""

    __table_name__ = "extra_allow_models"
    model_config = ConfigDict(extra="allow")

    name: str

class StrictFieldsMixin:
    count: int = Field(strict=True)
    enabled: bool = Field(strict=True)

class StrictModel(StrictFieldsMixin, ActiveRecord):
    """Model for strict Pydantic validation tests."""

    __table_name__ = "strict_models"

class AsyncStrictModel(StrictFieldsMixin, AsyncActiveRecord):
    """Async model for strict Pydantic validation tests."""

    __table_name__ = "strict_models"

class ValidateDefaultFieldsMixin:
    positive_count: int = Field(default=0, gt=0, validate_default=True)

class ValidateDefaultModel(ValidateDefaultFieldsMixin, ActiveRecord):
    """Model for validate_default pipeline tests."""

    __table_name__ = "validate_default_models"

class AsyncValidateDefaultModel(ValidateDefaultFieldsMixin, AsyncActiveRecord):
    """Async model for validate_default pipeline tests."""

    __table_name__ = "validate_default_models"

class ValidatorModesFieldsMixin:
    raw_code: str
    normalized_code: str
    wrapped_code: str
    combined: Optional[str] = None

    @model_validator(mode="before")
    def derive_combined(cls, data: Any) -> Any:
        if isinstance(data, dict) and "combined" not in data:
            data = {**data, "combined": f"{data.get('raw_code', '')}:{data.get('normalized_code', '')}"}
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

    __table_name__ = "validator_modes_models"

class AsyncValidatorModesModel(ValidatorModesFieldsMixin, AsyncActiveRecord):
    """Async model for Pydantic validator pipeline mode tests."""

    __table_name__ = "validator_modes_models"

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

    __table_name__ = "json_container_nested_models"

class AsyncJsonContainerNestedModel(JsonContainerNestedFieldsMixin, AsyncActiveRecord):
    """Async model for JSON dump, enum, container, and nested model tests."""

    __table_name__ = "json_container_nested_models"

class FromAttributesFieldsMixin:
    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: int

class FromAttributesModel(FromAttributesFieldsMixin, ActiveRecord):
    """Model for from_attributes construction tests."""

    __table_name__ = "from_attributes_models"

class AsyncFromAttributesModel(FromAttributesFieldsMixin, AsyncActiveRecord):
    """Async model for from_attributes construction tests."""

    __table_name__ = "from_attributes_models"

class AnnotatedMetadataOrderFieldsMixin:
    field_first: Annotated[str, Field(min_length=2), UseColumn("field_first_col")]
    column_first: Annotated[str, UseColumn("column_first_col"), Field(min_length=2)]

class AnnotatedMetadataOrderModel(AnnotatedMetadataOrderFieldsMixin, ActiveRecord):
    """Model for Annotated metadata ordering tests."""

    __table_name__ = "annotated_metadata_order_models"

class AsyncAnnotatedMetadataOrderModel(AnnotatedMetadataOrderFieldsMixin, AsyncActiveRecord):
    """Async model for Annotated metadata ordering tests."""

    __table_name__ = "annotated_metadata_order_models"

class AliasUseColumnConflictFieldsMixin:
    model_config = ConfigDict(populate_by_name=True)

    c: ClassVar[FieldProxy] = FieldProxy()
    same_name: Annotated[str, UseColumn("externalName")] = Field(alias="externalName")
    different_name: Annotated[str, UseColumn("db_different_name")] = Field(alias="apiDifferentName")

class AliasUseColumnConflictModel(AliasUseColumnConflictFieldsMixin, ActiveRecord):
    """Model for alias and UseColumn conflict boundary tests."""

    __table_name__ = "alias_use_column_conflict_models"

class AsyncAliasUseColumnConflictModel(AliasUseColumnConflictFieldsMixin, AsyncActiveRecord):
    """Async model for alias and UseColumn conflict boundary tests."""

    __table_name__ = "alias_use_column_conflict_models"

class AssignmentValidationFieldsMixin:
    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(min_length=2)
    quantity: int = Field(ge=1)

class AssignmentValidationModel(AssignmentValidationFieldsMixin, ActiveRecord):
    """Model for assignment validation and dirty tracking tests."""

    __table_name__ = "assignment_validation_models"

class AsyncAssignmentValidationModel(AssignmentValidationFieldsMixin, AsyncActiveRecord):
    """Async model for assignment validation and dirty tracking tests."""

    __table_name__ = "assignment_validation_models"


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


class TestSyncPydanticNativeValidation:
    """Synchronous Pydantic native validation tests."""

    def test_field_constraints_fail_on_init(self, pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "code": "bad-code"})
        assert "code" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "quantity": 0})
        assert "quantity" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "price": Decimal("0.00")})
        assert "price" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "step_count": 0})
        assert "step_count" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "step_count": 100})
        assert "step_count" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "step_count": 12})
        assert "step_count" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "normalized_name": ""})
        assert "normalized_name" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "normalized_name": "a" * 51})
        assert "normalized_name" in str(exc_info.value)

    def test_field_validator_transforms_value(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())

        assert model.normalized_name == "alice"
        assert model.save() == 1

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.normalized_name == "alice"

    def test_model_validator_rejects_invalid_cross_field_state(self, pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "end_at": data["start_at"]})
        assert "end_at must be after start_at" in str(exc_info.value)

    def test_validation_runs_again_on_save_after_assignment(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())
        model.save()

        model.quantity = 0
        with pytest.raises(DBValidationError) as exc_info:
            model.save()
        assert "quantity" in str(exc_info.value)

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.quantity == 5

    def test_model_validator_runs_again_on_save_after_assignment(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())
        model.save()

        model.end_at = model.start_at
        with pytest.raises(DBValidationError) as exc_info:
            model.save()
        assert "end_at must be after start_at" in str(exc_info.value)

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.end_at > saved_model.start_at

    def test_pydantic_coercion_persists_and_loads(self, pydantic_validated_model):
        data = valid_pydantic_data()
        model = pydantic_validated_model(
            **{
                **data,
                "quantity": "7",
                "price": "19.95",
                "start_at": "2024-01-01T10:00:00",
                "end_at": "2024-01-01T11:00:00",
            }
        )
        model.save()

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.quantity == 7
        assert isinstance(saved_model.quantity, int)
        assert saved_model.price == Decimal("19.95")
        assert isinstance(saved_model.price, Decimal)
        assert isinstance(saved_model.start_at, datetime)
        assert isinstance(saved_model.end_at, datetime)
        assert saved_model.created_token == "generated-token"

    def test_literal_validation(self, pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            pydantic_validated_model(**{**data, "status": "deleted"})
        assert "status" in str(exc_info.value)

        model = pydantic_validated_model(**{**data, "status": "active"})
        model.save()

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.status == "active"

    def test_model_dump_preserves_pydantic_state(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())
        dumped = model.model_dump()

        assert dumped["normalized_name"] == "alice"
        assert dumped["created_token"] == "generated-token"
        assert dumped["status"] == "draft"
        assert dumped["step_count"] == 10
        assert "c" not in dumped

    def test_model_validate_applies_pydantic_rules(self, pydantic_validated_model):
        data = valid_pydantic_data()
        model = pydantic_validated_model.model_validate(
            {
                **data,
                "quantity": "7",
                "step_count": "15",
                "price": "19.95",
                "start_at": "2024-01-01T10:00:00",
                "end_at": "2024-01-01T11:00:00",
            }
        )

        assert model.quantity == 7
        assert model.step_count == 15
        assert model.price == Decimal("19.95")
        assert model.normalized_name == "alice"
        assert isinstance(model.start_at, datetime)
        assert isinstance(model.end_at, datetime)

    def test_field_metadata_is_preserved(self, pydantic_validated_model):
        code_field = pydantic_validated_model.model_fields["code"]
        schema = pydantic_validated_model.model_json_schema()

        assert code_field.title == "Validation code"
        assert code_field.description == "Business code used by Pydantic compatibility tests."
        assert code_field.json_schema_extra == {"active_record_test": "pydantic-native"}
        assert schema["properties"]["code"]["title"] == "Validation code"
        assert schema["properties"]["code"]["active_record_test"] == "pydantic-native"

    def test_field_proxy_queries_pydantic_fields(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())
        model.save()

        code_matches = pydantic_validated_model.query().where(pydantic_validated_model.c.code == "ABC-123").all()
        assert [record.id for record in code_matches] == [model.id]

        quantity_matches = pydantic_validated_model.query().where(pydantic_validated_model.c.quantity >= 1).all()
        assert [record.id for record in quantity_matches] == [model.id]

        name_matches = pydantic_validated_model.query().where(pydantic_validated_model.c.normalized_name == "alice").all()
        assert [record.id for record in name_matches] == [model.id]

    def test_save_succeeds_after_fixing_invalid_assignment(self, pydantic_validated_model):
        model = pydantic_validated_model(**valid_pydantic_data())
        model.save()

        model.quantity = 0
        with pytest.raises(DBValidationError):
            model.save()

        model.quantity = 8
        assert model.save() == 1

        saved_model = pydantic_validated_model.find_one(model.id)
        assert saved_model.quantity == 8

    def test_mutable_default_factory_values_are_instance_isolated(self):
        # This verifies model-layer default isolation only; JSON/list persistence is covered by backend tests.
        first = MutableDefaultModel()
        second = MutableDefaultModel()

        first.tags.append("changed")
        first.metadata["changed"] = True

        assert first.tags == ["changed"]
        assert first.metadata == {"changed": True}
        assert second.tags == []
        assert second.metadata == {}
        assert first.tags is not second.tags
        assert first.metadata is not second.metadata

    def test_lifecycle_hooks_and_unset_none_are_preserved(self):
        omitted = LifecycleModel(required_name="alice")
        explicit_none = LifecycleModel(required_name="alice", optional_note=None)

        assert omitted.derived_name == "ALICE"
        assert explicit_none.derived_name == "ALICE"
        assert omitted.post_init_seen is True
        assert explicit_none.post_init_seen is True
        assert "optional_note" not in omitted.model_fields_set
        assert "optional_note" in explicit_none.model_fields_set
        assert omitted.model_dump(exclude_unset=True) == {"required_name": "alice", "derived_name": "ALICE"}
        assert explicit_none.model_dump(exclude_unset=True) == {
            "required_name": "alice",
            "optional_note": None,
            "derived_name": "ALICE",
        }

    def test_computed_field_and_serializer_are_dump_only_boundaries(self):
        model = PydanticV2BoundaryModel(
            first_name="Ada",
            last_name="Lovelace",
            score=Decimal("9.5"),
            annotated_code="AR",
        )
        dumped = model.model_dump()

        assert dumped["full_name"] == "Ada Lovelace"
        assert dumped["score"] == "score:9.5"
        assert "full_name" not in PydanticV2BoundaryModel.model_fields
        assert "score" in PydanticV2BoundaryModel.model_fields

    def test_annotated_field_and_use_column_metadata_coexist(self):
        model = PydanticV2BoundaryModel(
            first_name="Ada",
            last_name="Lovelace",
            score=Decimal("9.5"),
            annotated_code="AR",
        )

        assert model.annotated_code == "AR"
        assert PydanticV2BoundaryModel._get_column_name("annotated_code") == "annotated_code_col"
        assert PydanticV2BoundaryModel.model_fields["annotated_code"].metadata

        with pytest.raises(ValidationError) as exc_info:
            PydanticV2BoundaryModel(
                first_name="Ada",
                last_name="Lovelace",
                score=Decimal("9.5"),
                annotated_code="A",
            )
        assert "annotated_code" in str(exc_info.value)

    def test_aliases_are_independent_from_column_mapping(self):
        from_alias = AliasBoundaryModel(externalId=7, inputName="Ada", public_name="Lovelace")
        from_name = AliasBoundaryModel(external_id=8, inputName="Grace", public_name="Hopper")

        assert from_alias.external_id == 7
        assert from_name.external_id == 8
        assert from_alias.display_name == "Ada"
        assert from_alias.model_dump() == {"external_id": 7, "display_name": "Ada", "public_name": "Lovelace"}
        assert from_alias.model_dump(by_alias=True) == {
            "externalId": 7,
            "display_name": "Ada",
            "outputName": "Lovelace",
        }
        assert set(AliasBoundaryModel.model_fields) == {"external_id", "display_name", "public_name"}
        assert AliasBoundaryModel._get_column_name("external_id") == "external_id_col"

    def test_extra_config_modes_preserve_pydantic_behavior(self):
        with pytest.raises(ValidationError) as exc_info:
            ExtraForbidModel(name="Ada", unknown="rejected")
        assert "unknown" in str(exc_info.value)

        ignored = ExtraIgnoreModel(name="Ada", unknown="ignored")
        assert ignored.model_dump() == {"name": "Ada"}
        assert not hasattr(ignored, "unknown")

        allowed = ExtraAllowModel(name="Ada", unknown="kept")
        assert allowed.model_dump() == {"name": "Ada", "unknown": "kept"}
        assert allowed.unknown == "kept"

    def test_strict_fields_reject_coercion(self):
        model = StrictModel(count=3, enabled=True)
        assert model.count == 3
        assert model.enabled is True

        with pytest.raises(ValidationError) as exc_info:
            StrictModel(count="3", enabled=True)
        assert "count" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            StrictModel(count=3, enabled="true")
        assert "enabled" in str(exc_info.value)

    def test_validate_default_runs_on_model_construction(self):
        with pytest.raises(ValidationError) as exc_info:
            ValidateDefaultModel()
        assert "positive_count" in str(exc_info.value)

        model = ValidateDefaultModel(positive_count=1)
        assert model.positive_count == 1

    def test_validator_pipeline_modes_are_preserved(self):
        model = ValidatorModesModel(raw_code="  RAW  ", normalized_code="MiXeD", wrapped_code="  WRAPPED  ")

        assert model.raw_code == "RAW"
        assert model.normalized_code == "mixed"
        assert model.wrapped_code == "wrapped:wrapped"
        assert model.combined == "  RAW  :MiXeD"
        assert model.model_dump() == {
            "raw_code": "RAW",
            "normalized_code": "mixed",
            "wrapped_code": "wrapped:wrapped",
            "combined": "  RAW  :MiXeD",
        }

    def test_json_enum_container_and_nested_model_contracts(self):
        model = JsonContainerNestedModel(
            status="active",
            created_at="2024-01-01T10:00:00",
            address={"city": "Paris", "zip_code": "75001"},
            labels=["ok", "valid"],
            scores={"quality": 95},
        )
        json_dump = model.model_dump(mode="json")
        parsed = json.loads(model.model_dump_json())

        assert model.status is RecordStatus.active
        assert json_dump["status"] == "active"
        assert json_dump["created_at"] == "2024-01-01T10:00:00"
        assert json_dump["address"] == {"city": "Paris", "zip_code": "75001"}
        assert parsed == json_dump

        with pytest.raises(ValidationError) as exc_info:
            JsonContainerNestedModel(
                status="active",
                created_at="2024-01-01T10:00:00",
                address={"city": "P", "zip_code": "bad"},
                labels=["x"],
                scores={"quality": 101},
            )
        error_text = str(exc_info.value)
        assert "address" in error_text
        assert "labels" in error_text
        assert "scores" in error_text

    def test_from_attributes_constructs_from_plain_objects(self):
        class SourceObject:
            name = "Ada"
            quantity = 3

        model = FromAttributesModel.model_validate(SourceObject())
        assert model.name == "Ada"
        assert model.quantity == 3

        class IncompleteSourceObject:
            name = "Ada"

        with pytest.raises(ValidationError) as exc_info:
            FromAttributesModel.model_validate(IncompleteSourceObject())
        assert "quantity" in str(exc_info.value)

    def test_annotated_metadata_order_is_not_significant(self):
        model = AnnotatedMetadataOrderModel(field_first="AB", column_first="CD")

        assert model.field_first == "AB"
        assert model.column_first == "CD"
        assert AnnotatedMetadataOrderModel._get_column_name("field_first") == "field_first_col"
        assert AnnotatedMetadataOrderModel._get_column_name("column_first") == "column_first_col"

        with pytest.raises(ValidationError) as exc_info:
            AnnotatedMetadataOrderModel(field_first="A", column_first="C")
        assert "field_first" in str(exc_info.value)
        assert "column_first" in str(exc_info.value)

    def test_alias_use_column_conflicts_keep_separate_meanings(self):
        model = AliasUseColumnConflictModel(externalName="same", apiDifferentName="different")
        alias_dump = model.model_dump(by_alias=True)

        assert model.same_name == "same"
        assert model.different_name == "different"
        assert alias_dump == {"externalName": "same", "apiDifferentName": "different"}
        assert set(AliasUseColumnConflictModel.model_fields) == {"same_name", "different_name"}
        assert AliasUseColumnConflictModel._get_column_name("same_name") == "externalName"
        assert AliasUseColumnConflictModel._get_column_name("different_name") == "db_different_name"

        with pytest.raises(AttributeError):
            _ = AliasUseColumnConflictModel.c.externalName
        with pytest.raises(AttributeError):
            _ = AliasUseColumnConflictModel.c.apiDifferentName

    def test_validate_assignment_updates_dirty_tracking_only_after_success(self):
        model = AssignmentValidationModel(name="Ada", quantity=1)
        model.reset_tracking()

        model.quantity = 2
        assert model.quantity == 2
        assert model.dirty_fields == {"quantity"}

        with pytest.raises(ValidationError) as exc_info:
            model.name = "A"
        assert "name" in str(exc_info.value)
        assert model.name == "Ada"
        assert model.dirty_fields == {"quantity"}