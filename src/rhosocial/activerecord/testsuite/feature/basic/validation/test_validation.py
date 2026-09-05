# src/rhosocial/activerecord/testsuite/feature/basic/validation/test_validation.py
"""Basic Validation Test Module

This module tests the validation functionality of the ActiveRecord class.
"""
import pytest
from pydantic import ValidationError
from rhosocial.activerecord.backend.errors import ValidationError as DBValidationError

# Fixtures are now injected by the conftest.py in this package


@pytest.fixture
def validated_user_data():
    """Provide valid user testing data"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'age': 25
    }
class TestSyncValidation:
    """Synchronous validation test class that wraps all the sync test functions."""
    
    def test_field_validation(self, validated_user):
        """Test Pydantic field validation"""
        # Test username validation
        with pytest.raises(ValidationError) as exc_info:
            validated_user(username="ab", email="valid@example.com")  # Too short
        assert "username" in str(exc_info.value), "Expected ValidationError to mention 'username' (too short)"

        with pytest.raises(ValidationError) as exc_info:
            validated_user(username="x" * 51, email="valid@example.com")  # Too long
        assert "username" in str(exc_info.value), "Expected ValidationError to mention 'username' (too long)"

        # Test email validation
        with pytest.raises(ValidationError) as exc_info:
            validated_user(username="validuser", email="invalid-email")
        assert "email" in str(exc_info.value), "Expected ValidationError to mention 'email' (bad format)"

        # Test age validation
        with pytest.raises(ValidationError) as exc_info:
            validated_user(username="validuser", email="valid@example.com", age=-1)
        assert "age" in str(exc_info.value), "Expected ValidationError to mention 'age' (negative)"

        with pytest.raises(ValidationError) as exc_info:
            validated_user(username="validuser", email="valid@example.com", age=151)
        assert "age" in str(exc_info.value), "Expected ValidationError to mention 'age' (too high)"

    def test_business_rule_validation(self, validated_user):
        """Test custom business rule validation"""
        # Test age restriction rule
        user = validated_user(
            username="younguser",  # Changed to comply with alphanumeric requirement
            email="young@example.com",
            age=12
        )

        with pytest.raises(DBValidationError) as exc_info:
            user.save()
        assert "at least 13 years old" in str(exc_info.value), \
            "Expected the minimum-age business rule message"

        # Test valid age
        user.age = 13
        assert user.save() == 1, "Expected save() to affect 1 row at age 13"

    def test_validation_on_update(self, validated_user, validated_user_data):
        """Test validation during record updates"""
        # Create valid user
        user = validated_user(**validated_user_data)
        user.save()

        # Test invalid update
        user.email = "invalid-email-format"
        with pytest.raises(DBValidationError):
            user.save()

        # Verify record remains unchanged
        fresh_user = validated_user.find_one(user.id)
        assert fresh_user.email == validated_user_data['email'], \
            "Expected the email to remain unchanged after rejected update"

        # Test valid update
        user.email = "new-valid@example.com"
        assert user.save() == 1, "Expected the corrected save() to affect 1 row"

    def test_null_field_validation(self, validated_user):
        """Test validation of nullable fields"""
        # Test with null age (should be valid as age is optional)
        user = validated_user(
            username="testuser",  # Changed to comply with alphanumeric requirement
            email="test@example.com"
        )
        assert user.save() == 1, "Expected save() with optional age=None to succeed"

        # Verify null field was saved correctly
        saved_user = validated_user.find_one(user.id)
        assert saved_user.age is None, "Expected the persisted age to be None"

    def test_multiple_validation_errors(self, validated_user):
        """Test handling of multiple validation errors"""
        with pytest.raises(ValidationError) as exc_info:
            validated_user(
                username="a",  # Too short
                email="invalid-email",  # Invalid format
                age=200  # Too high
            )

        error_str = str(exc_info.value)
        assert "username" in error_str, "Expected ValidationError to mention 'username'"
        assert "email" in error_str, "Expected ValidationError to mention 'email'"
        assert "age" in error_str, "Expected ValidationError to mention 'age'"