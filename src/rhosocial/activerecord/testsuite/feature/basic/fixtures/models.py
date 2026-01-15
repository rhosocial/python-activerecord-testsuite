# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""
import re
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, Type, Literal, Union, Any, Dict, List
import json # Added import for json

from pydantic import EmailStr, Field, field_validator

from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter
from rhosocial.activerecord.base.fields import UseAdapter, UseColumn
from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.backend.errors import ValidationError
# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.
from rhosocial.activerecord.field import TimestampMixin, UUIDMixin, IntegerPKMixin

class TypeCase(UUIDMixin, ActiveRecord):
    """A model with a wide variety of data types to test database type handling."""
    __table_name__ = "type_cases"

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
    __table_name__ = "type_tests"

    # UUID primary key provided by UUIDMixin
    string_field: str = Field(default="test string")
    int_field: int = Field(default=42)
    float_field: float = Field(default=3.14)
    decimal_field: Decimal = Field(default=Decimal("10.99"))
    bool_field: bool = Field(default=True)
    datetime_field: datetime = Field(default_factory=datetime.now)
    json_field: Optional[dict] = None
    nullable_field: Optional[str] = Field(default=None)


class User(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """A standard User model for general CRUD operation testing."""
    __table_name__ = "users"

    # The IntegerPKMixin is expected to handle the `id` field.
    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

class ValidatedFieldUser(IntegerPKMixin, ActiveRecord):
    """
    A User model with specific, custom field validators to test the framework's
    validation handling.
    """
    __table_name__ = "validated_field_users"

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = None
    balance: Optional[float] = 0.0
    credit_score: int
    status: Literal['active', 'inactive', 'banned', 'pending', 'suspended'] = 'active'
    is_active: Optional[bool] = True

    @field_validator('username')
    def validate_username(cls, value):
        """A custom validator that rejects usernames containing '123'."""
        if re.search(r'123', value):
            # This test uses the framework's custom ValidationError, which is
            # distinct from pydantic.ValidationError.
            raise ValidationError("Username must not contain '123'.")
        return value

    @field_validator('credit_score')
    def validate_credit_score(cls, value):
        """A custom validator that ensures credit_score is within a specific range."""
        if not (0 <= value <= 800):
            raise ValidationError("Credit score must be between 0 and 800.")
        return value

class ValidatedUser(IntegerPKMixin, ActiveRecord):
    """User model for validation testing"""
    __table_name__ = "validated_users"

    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)

    @field_validator('username')
    def validate_username(cls, v: str) -> str:
        # Custom username validation rules
        if len(v.strip()) != len(v):
            raise ValidationError("Username cannot have leading or trailing spaces")
        if not v.isalnum():
            raise ValidationError("Username must be alphanumeric")
        return v

    @classmethod
    def validate_record(cls, instance: 'ValidatedUser') -> None:
        """Business rule validation"""
        if instance.age is not None and instance.age < 13:
            raise ValidationError("User must be at least 13 years old")



try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated


# --- Module-level definitions for TypeAdapterTest and YesOrNoBooleanAdapter ---
class YesOrNoBooleanAdapter(BaseSQLTypeAdapter):
    """Converts Python's True/False to 'yes'/'no' strings."""
    def _do_to_database(self, value: bool, target_type: Type, options: Optional[Dict[str, Any]] = None) -> str:
        return "yes" if value else "no"

    def _do_from_database(self, value: str, target_type: Type, options: Optional[Dict[str, Any]] = None) -> bool:
        return value == "yes"

class TypeAdapterTest(ActiveRecord):
    """Model for testing various type adapter scenarios."""
    __table_name__ = 'type_adapter_tests'
    __primary_key__ = 'id'


    id: Optional[int] = None
    name: str
    # Fields for testing implicit Optional[T] handling
    optional_name: Optional[str] = None
    optional_age: Optional[int] = None
    last_login: Optional[datetime] = None
    is_premium: Optional[bool] = None
    # Field for testing unsupported Union
    unsupported_union: Union[str, int] = 0
    # Fields for testing explicit adapter annotation
    custom_bool: Annotated[bool, UseAdapter(YesOrNoBooleanAdapter(), str)] = None
    optional_custom_bool: Annotated[Optional[bool], UseAdapter(YesOrNoBooleanAdapter(), str)] = None
# --- End of module-level definitions ---

class MappedUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with custom column name mappings for testing in basic feature."""

    __table_name__ = "users"
    __primary_key__ = "id"

    # Python field: user_id, Database column: id
    user_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: user_name, Database column: username
    user_name: Annotated[str, UseColumn("username")]

    # Python field: email_address, Database column: email
    email_address: Annotated[str, UseColumn("email")]

    # Python field: creation_date, which maps to the 'created_at' column.
    # This overrides the `created_at` field from TimestampMixin.
    creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None


class MappedPost(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Post model with custom column name mappings for testing in basic feature."""

    __table_name__ = "posts"
    __primary_key__ = "id"

    # Python field: post_id, Database column: id
    post_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: author_id, Database column: author
    author_id: Annotated[int, UseColumn("author")]

    # Python field: post_title: Annotated[str, UseColumn("title")]
    post_title: Annotated[str, UseColumn("title")]

    # Python field: post_content: Annotated[str, UseColumn("content")]
    post_content: Annotated[str, UseColumn("content")]

    # Python field: publication_time, maps to 'published_at' column
    publication_time: Annotated[Optional[datetime], UseColumn("published_at")] = None

    # Python field: is_published, Database column: published
    is_published: Annotated[bool, UseColumn("published")]


class MappedComment(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Comment model with custom column name mappings for testing in basic feature."""

    __table_name__ = "comments"
    __primary_key__ = "id"

    # Python field: comment_id, Database column: id
    comment_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: post_id, Database column: post_ref
    post_id: Annotated[int, UseColumn("post_ref")]

    # Python field: author_id: Annotated[int, UseColumn("author")]
    author_id: Annotated[int, UseColumn("author")]

    # Python field: comment_text, Database column: text
    comment_text: Annotated[str, UseColumn("text")]

    # Python field: comment_creation_date, maps to 'created_at' column.
    # This overrides the `created_at` field from TimestampMixin.
    comment_creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None

    # Python field: is_approved, Database column: approved
    is_approved: Annotated[bool, UseColumn("approved")]


class IntToStringAdapter(BaseSQLTypeAdapter):
    """A simple type adapter that converts an integer for the DB to a string for Python."""

    def __init__(self):
        super().__init__()
        self._register_type(str, int)  # Python 'str' can be converted to DB 'int'

    def _do_to_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        # The 'notes' attribute on the model is a str, which we convert to an int for the DB.
        return int(value)

    def _do_from_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        # The 'remarks' column in the DB is an int, which we convert to a str for the model attribute.
        return str(value)


class ColumnMappingModel(ActiveRecord):
    """
    A model demonstrating various valid uses of UseColumn and UseAdapter,
    including mapping the primary key attribute.
    """
    __table_name__ = 'column_mapping_items'
    __primary_key__ = 'id'

    # Primary key defaults to 'id'. item_id attribute maps to this 'id' column.
    item_id: Annotated[Optional[int], UseColumn("id")] = Field(default=None)
    name: str  # Default mapping
    item_count: Annotated[int, UseColumn("item_total")]  # Mapped to 'item_total'
    notes: Annotated[str, UseAdapter(IntToStringAdapter(), target_db_type=int), UseColumn("remarks")] # Mapped to 'remarks' with an adapter


class ListToStringAdapter(BaseSQLTypeAdapter):
    """Converts a Python list of strings to a single comma-separated string for the DB."""

    def __init__(self):
        super().__init__()
        self._register_type(list, str)

    def _do_to_database(self, value: List[str], target_type: Type, options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if value is None:
            return None
        # Join the list elements with commas
        return ",".join(value)

    def _do_from_database(self, value: str, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
        if value is None:
            return None

        # Handle different string representations of lists
        if isinstance(value, str):
            # Check if it looks like a Python list representation (with brackets)
            if value.startswith('[') and value.endswith(']'):
                # It's a string representation of a list, try to parse it
                import ast
                try:
                    parsed_value = ast.literal_eval(value)
                    if isinstance(parsed_value, list):
                        return parsed_value
                    else:
                        # If it's not a list after parsing, return as single-item list
                        return [parsed_value] if parsed_value is not None else []
                except (ValueError, SyntaxError):
                    # If parsing fails, fall back to comma splitting
                    pass

            # Also handle if it looks like a Python list representation but with quotes around the whole thing
            # For example: "['tag1', 'tag2']" might become "'['tag1', 'tag2']'" after some processing
            # So we try to strip outer quotes first
            stripped_value = value.strip().strip('"\'')
            if stripped_value.startswith('[') and stripped_value.endswith(']'):
                import ast
                try:
                    parsed_value = ast.literal_eval(stripped_value)
                    if isinstance(parsed_value, list):
                        return parsed_value
                except (ValueError, SyntaxError):
                    pass

            # If not a list representation or parsing failed, split by comma
            if value:
                return [item.strip().strip('"\'') for item in value.split(',')]
            else:
                return []

        # If value is not a string, return as is (though this shouldn't happen with proper DB integration)
        return [value] if value is not None else []

# New adapter for JSON string conversion
class JsonToStringAdapter(BaseSQLTypeAdapter):
    """Converts a Python dictionary to a JSON string for the DB."""

    def __init__(self):
        super().__init__()
        self._register_type(dict, str)

    def _do_to_database(self, value: Dict, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    def _do_from_database(self, value: str, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        if value is None:
            return None
        return json.loads(value)

class MixedAnnotationModel(ActiveRecord):
    """A model with various combinations of annotations to test field mapping and adapters."""
    __table_name__ = "mixed_annotation_items"
    __primary_key__ = "id" # Corrected from "item_id"

    # 1. Standard Python type
    name: str

    # 2. Field with a different column name
    item_id: Annotated[int, UseColumn("id")]

    # 3. Field using a type adapter
    tags: Annotated[List[str], UseAdapter(ListToStringAdapter(), str)]

    # 4. Field with both a different column name and a type adapter
    #    Now uses the correct JsonToStringAdapter for dictionary serialization
    metadata: Annotated[Optional[Dict], UseColumn("meta"), UseAdapter(JsonToStringAdapter(), str)] = None

    # 5. Field that is nullable
    description: Optional[str] = None

    # 6. Field with a default value
    status: str = "active"