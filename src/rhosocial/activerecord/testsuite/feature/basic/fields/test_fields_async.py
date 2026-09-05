# src/rhosocial/activerecord/testsuite/feature/basic/fields/test_fields_async.py
"""Basic Fields Test Module

This module tests the basic field processing functionality of the ActiveRecord class.
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID


# Fixtures are now injected by the conftest.py in this package

from rhosocial.activerecord.testsuite.utils import requires_json_operations
class TestAsyncFields:
    """Asynchronous tests for field processing functionality."""

    async def test_string_field(self, async_type_test_model):
        """Test string field processing"""
        # Basic string test
        model = async_type_test_model(string_field="test string")
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)
        assert saved_model.string_field == "test string", "Expected string_field to round-trip"

        # Special characters test
        special_string = "Special chars: !@#$%^&*()"
        model.string_field = special_string
        await model.save()

        await saved_model.refresh()
        assert saved_model.string_field == special_string, \
            "Expected special-character string_field to round-trip"

        # Unicode test
        unicode_string = "Unicode: 浣犲ソ涓栫晫 馃實"
        model.string_field = unicode_string
        await model.save()

        await saved_model.refresh()
        assert saved_model.string_field == unicode_string, \
            "Expected unicode string_field to round-trip"

    async def test_numeric_fields(self, async_type_test_model):
        """Test numeric type fields"""
        model = async_type_test_model(
            int_field=42,
            float_field=3.14159,
            decimal_field=Decimal("10.99")
        )
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)

        # Integer test
        assert saved_model.int_field == 42, "Expected int_field to be 42"
        assert isinstance(saved_model.int_field, int), "Expected int_field to be an int"

        # Float test
        assert abs(saved_model.float_field - 3.14159) < 1e-6, \
            "Expected float_field to round-trip to ~3.14159"
        assert isinstance(saved_model.float_field, float), "Expected float_field to be a float"

        # Decimal test
        assert saved_model.decimal_field == Decimal("10.99"), \
            "Expected decimal_field to be 10.99"
        assert isinstance(saved_model.decimal_field, Decimal), \
            "Expected decimal_field to be a Decimal"

        # Large number test
        model.int_field = 2 ** 31 - 1
        model.float_field = 1.23456789
        model.decimal_field = Decimal("9999999.99")
        await model.save()

        await saved_model.refresh()
        assert saved_model.int_field == 2 ** 31 - 1, \
            "Expected large int_field to round-trip"
        assert abs(saved_model.float_field - 1.23456789) < 1e-5, \
            "Expected updated float_field to round-trip"
        assert saved_model.decimal_field == Decimal("9999999.99"), \
            "Expected updated decimal_field to round-trip"

    async def test_boolean_field(self, async_type_test_model):
        """Test boolean field processing"""
        model = async_type_test_model(bool_field=True)
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)
        assert saved_model.bool_field is True, "Expected bool_field to be True after save"
        assert isinstance(saved_model.bool_field, bool), "Expected bool_field to be a bool"

        # Toggle value test
        model.bool_field = False
        await model.save()

        await saved_model.refresh()
        assert saved_model.bool_field is False, "Expected bool_field to be False after toggle"

    async def test_datetime_field(self, async_type_test_model):
        """Test datetime field processing"""
        from datetime import timedelta
        test_datetime = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)
        if not async_type_test_model.backend().dialect.supports_microsecond_timestamp():
            test_datetime = test_datetime.replace(microsecond=(test_datetime.microsecond // 10000) * 10000)
        model = async_type_test_model(datetime_field=test_datetime)
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)
        assert saved_model.datetime_field == test_datetime, "Expected datetime_field to round-trip"
        assert isinstance(saved_model.datetime_field, datetime), \
            "Expected datetime_field to be a datetime"
        utc_plus_8 = timezone(timedelta(hours=8))
        assert saved_model.datetime_field.astimezone(utc_plus_8).isoformat() == test_datetime.astimezone(utc_plus_8).isoformat(), \
            "Expected datetime_field to round-trip with timezone conversion"

    @requires_json_operations()
    async def test_json_field(self, async_type_test_model):
        """Test JSON field processing"""
        test_json = {
            "string": "value",
            "number": 42,
            "array": [1, 2, 3],
            "nested": {
                "key": "value"
            }
        }
        model = async_type_test_model(json_field=test_json)
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)
        assert saved_model.json_field == test_json, "Expected json_field to round-trip"

        # JSON serialization/deserialization test
        json_str = json.dumps(saved_model.json_field)
        parsed_json = json.loads(json_str)
        assert parsed_json == test_json, "Expected JSON round-trip to preserve the value"

    async def test_nullable_field(self, async_type_test_model):
        """Test nullable field processing"""
        model = async_type_test_model()  # Use default value None
        assert model.nullable_field is None, "Expected default nullable_field to be None"
        await model.save()

        saved_model = await async_type_test_model.find_one(model.id)
        assert saved_model.nullable_field is None, "Expected saved nullable_field to be None"

        # Set and clear value test
        model.nullable_field = "some value"
        await model.save()

        await saved_model.refresh()
        assert saved_model.nullable_field == "some value", \
            "Expected nullable_field to be 'some value'"

        model.nullable_field = None
        await model.save()

        await saved_model.refresh()
        assert saved_model.nullable_field is None, "Expected nullable_field to be cleared to None"

    async def test_uuid_primary_key(self, async_type_test_model):
        """Test UUID primary key processing"""
        model = async_type_test_model()
        await model.save()

        assert isinstance(model.id, UUID), "Expected the primary key to be a UUID"

        # UUID lookup test
        found_model = await async_type_test_model.find_one(model.id)
        assert found_model is not None, "Expected to find the model by UUID"
        assert found_model.id == model.id, "Expected the found id to match the saved id"

        # UUID generation uniqueness test
        another_model = async_type_test_model()
        await another_model.save()
        assert another_model.id != model.id, "Expected two generated UUIDs to be distinct"

    async def test_numeric_edge_cases(self, async_type_test_model):
        """Test numeric field edge cases: zero, negative, large int."""
        model = async_type_test_model(int_field=0, float_field=-1.5, decimal_field=Decimal("0.00"))
        await model.save()
        saved = await async_type_test_model.find_one(model.id)
        assert saved.int_field == 0, "Expected int_field to be 0"
        assert saved.float_field == -1.5, "Expected float_field to be -1.5"
        assert saved.decimal_field == Decimal("0.00"), "Expected decimal_field to be 0.00"

    async def test_boolean_serialization_cycle(self, async_type_test_model):
        """Test boolean toggling through multiple cycles."""
        model = async_type_test_model(bool_field=True)
        await model.save()
        model.bool_field = False
        await model.save()
        saved = await async_type_test_model.find_one(model.id)
        assert saved.bool_field is False, "Expected bool_field to be False after first toggle"
        model.bool_field = True
        await model.save()
        saved = await async_type_test_model.find_one(model.id)
        assert saved.bool_field is True, "Expected bool_field to be True after second toggle"