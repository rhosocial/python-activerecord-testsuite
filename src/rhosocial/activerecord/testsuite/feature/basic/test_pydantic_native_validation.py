# src/rhosocial/activerecord/testsuite/feature/basic/test_pydantic_native_validation.py
"""Tests for Pydantic native validation behavior in ActiveRecord models."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from rhosocial.activerecord.backend.errors import ValidationError as DBValidationError


def valid_pydantic_data():
    start_at = datetime(2024, 1, 1, 10, 0, 0)
    return {
        "code": "ABC-123",
        "quantity": 5,
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


class TestAsyncPydanticNativeValidation:
    """Asynchronous Pydantic native validation tests."""

    @pytest.mark.asyncio
    async def test_field_constraints_fail_on_init(self, async_pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            async_pydantic_validated_model(**{**data, "code": "bad-code"})
        assert "code" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            async_pydantic_validated_model(**{**data, "quantity": 0})
        assert "quantity" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            async_pydantic_validated_model(**{**data, "price": Decimal("0.00")})
        assert "price" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_field_validator_transforms_value(self, async_pydantic_validated_model):
        model = async_pydantic_validated_model(**valid_pydantic_data())

        assert model.normalized_name == "alice"
        assert await model.save() == 1

        saved_model = await async_pydantic_validated_model.find_one(model.id)
        assert saved_model.normalized_name == "alice"

    @pytest.mark.asyncio
    async def test_model_validator_rejects_invalid_cross_field_state(self, async_pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            async_pydantic_validated_model(**{**data, "end_at": data["start_at"]})
        assert "end_at must be after start_at" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_runs_again_on_save_after_assignment(self, async_pydantic_validated_model):
        model = async_pydantic_validated_model(**valid_pydantic_data())
        await model.save()

        model.quantity = 0
        with pytest.raises(DBValidationError) as exc_info:
            await model.save()
        assert "quantity" in str(exc_info.value)

        saved_model = await async_pydantic_validated_model.find_one(model.id)
        assert saved_model.quantity == 5

    @pytest.mark.asyncio
    async def test_model_validator_runs_again_on_save_after_assignment(self, async_pydantic_validated_model):
        model = async_pydantic_validated_model(**valid_pydantic_data())
        await model.save()

        model.end_at = model.start_at
        with pytest.raises(DBValidationError) as exc_info:
            await model.save()
        assert "end_at must be after start_at" in str(exc_info.value)

        saved_model = await async_pydantic_validated_model.find_one(model.id)
        assert saved_model.end_at > saved_model.start_at

    @pytest.mark.asyncio
    async def test_pydantic_coercion_persists_and_loads(self, async_pydantic_validated_model):
        data = valid_pydantic_data()
        model = async_pydantic_validated_model(
            **{
                **data,
                "quantity": "7",
                "price": "19.95",
                "start_at": "2024-01-01T10:00:00",
                "end_at": "2024-01-01T11:00:00",
            }
        )
        await model.save()

        saved_model = await async_pydantic_validated_model.find_one(model.id)
        assert saved_model.quantity == 7
        assert isinstance(saved_model.quantity, int)
        assert saved_model.price == Decimal("19.95")
        assert isinstance(saved_model.price, Decimal)
        assert isinstance(saved_model.start_at, datetime)
        assert isinstance(saved_model.end_at, datetime)
        assert saved_model.created_token == "generated-token"

    @pytest.mark.asyncio
    async def test_literal_validation(self, async_pydantic_validated_model):
        data = valid_pydantic_data()

        with pytest.raises(ValidationError) as exc_info:
            async_pydantic_validated_model(**{**data, "status": "deleted"})
        assert "status" in str(exc_info.value)

        model = async_pydantic_validated_model(**{**data, "status": "active"})
        await model.save()

        saved_model = await async_pydantic_validated_model.find_one(model.id)
        assert saved_model.status == "active"
