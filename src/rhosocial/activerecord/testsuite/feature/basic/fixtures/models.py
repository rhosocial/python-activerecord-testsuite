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
from typing import Optional, Type, Literal, Union, Any, Dict, List, Set
import json # Added import for json

from pydantic import EmailStr, Field, field_validator, model_validator

from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter
from rhosocial.activerecord.base.fields import UseAdapter, UseColumn
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.backend.errors import ValidationError
# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.
from rhosocial.activerecord.field import DefaultTimestampMixin, UUIDMixin, IntegerPKMixin, CompositePKMixin

try:
    from typing import Annotated, ClassVar
except ImportError:
    from typing_extensions import Annotated, ClassVar

from . import resolve

from rhosocial.activerecord.backend.expression import (
    ColumnConstraint as Constraint,
    ColumnDefinition as Column,
    CreateTableStatement as CreateTable,
    DropTableStatement as DropTable,
    TableConstraint,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnDefaultConstraint as Default,
    ColumnNotNullConstraint as NotNull,
    ColumnPrimaryKeyConstraint as PrimaryKey,
    TablePrimaryKeyConstraint as TablePrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import (
    BigIntType as BigInt,
    BlobType as Blob,
    BooleanType as Bool,
    DecimalType as Numeric,
    DoubleType as Double,
    FloatType as Float,
    IntegerType as Int,
    SmallIntType as SmallInt,
    TinyIntType as TinyInt,
    VarCharType as VarChar,
)
from rhosocial.activerecord.testsuite.core.fixture_types import (
    array_type,
    date_type,
    json_text,
    long_text,
    short_text,
    time_type,
    timestamp_type,
)

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


class User(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """A standard User model for general CRUD operation testing."""
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()

    # The IntegerPKMixin is expected to handle the `id` field.
    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

class AsyncUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """A standard User model for general CRUD operation testing."""
    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()

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
    @classmethod
    def table_name(cls):
        return "validated_field_users"

    c: ClassVar[FieldProxy] = FieldProxy()

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

class AsyncValidatedFieldUser(IntegerPKMixin, AsyncActiveRecord):
    """
    A User model with specific, custom field validators to test the framework's
    validation handling.
    """
    @classmethod
    def table_name(cls):
        return "validated_field_users"

    c: ClassVar[FieldProxy] = FieldProxy()

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
    @classmethod
    def table_name(cls):
        return "validated_users"

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

class AsyncValidatedUser(IntegerPKMixin, AsyncActiveRecord):
    """User model for validation testing"""
    @classmethod
    def table_name(cls):
        return "validated_users"

    c: ClassVar[FieldProxy] = FieldProxy()

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
    def validate_record(cls, instance) -> None:
        """Business rule validation"""
        if instance.age is not None and instance.age < 13:
            raise ValidationError("User must be at least 13 years old")


# Keep this mixin I/O-free: fields, validators, and the FieldProxy descriptor are shared by sync/async models.
# FieldProxy builds expressions from configured model metadata; concrete models still own table metadata and I/O bases.
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
    status: Literal["draft", "active", "archived"] = "draft"
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
    @classmethod
    def table_name(cls):
        return 'type_adapter_tests'

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

class AsyncTypeAdapterTest(AsyncActiveRecord):
    """Model for testing various type adapter scenarios."""
    @classmethod
    def table_name(cls):
        return 'type_adapter_tests'

    c: ClassVar[FieldProxy] = FieldProxy()

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

class MappedUser(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """User model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "users"

    # Python field: user_id, Database column: id
    user_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: user_name, Database column: username
    user_name: Annotated[str, UseColumn("username")]

    # Python field: email_address, Database column: email
    email_address: Annotated[str, UseColumn("email")]

    # Python field: creation_date, which maps to the 'created_at' column.
    # This overrides the `created_at` field from DefaultTimestampMixin.
    creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None

class AsyncMappedUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """User model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()

    # Python field: user_id, Database column: id
    user_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: user_name, Database column: username
    user_name: Annotated[str, UseColumn("username")]

    # Python field: email_address, Database column: email
    email_address: Annotated[str, UseColumn("email")]

    # Python field: creation_date, which maps to the 'created_at' column.
    # This overrides the `created_at` field from DefaultTimestampMixin.
    creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None


class MappedPost(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Post model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "posts"

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

class AsyncMappedPost(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Post model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "posts"

    c: ClassVar[FieldProxy] = FieldProxy()

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


class MappedComment(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Comment model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "comments"

    # Python field: comment_id, Database column: id
    comment_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: post_id, Database column: post_ref
    post_id: Annotated[int, UseColumn("post_ref")]

    # Python field: author_id: Annotated[int, UseColumn("author")]
    author_id: Annotated[int, UseColumn("author")]

    # Python field: comment_text, Database column: text
    comment_text: Annotated[str, UseColumn("text")]

    # Python field: comment_creation_date, maps to 'created_at' column.
    # This overrides the `created_at` field from DefaultTimestampMixin.
    comment_creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None

    # Python field: is_approved, Database column: approved
    is_approved: Annotated[bool, UseColumn("approved")]

class AsyncMappedComment(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Comment model with custom column name mappings for testing in basic feature."""

    @classmethod
    def table_name(cls):
        return "comments"

    c: ClassVar[FieldProxy] = FieldProxy()

    # Python field: comment_id, Database column: id
    comment_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: post_id, Database column: post_ref
    post_id: Annotated[int, UseColumn("post_ref")]

    # Python field: author_id: Annotated[int, UseColumn("author")]
    author_id: Annotated[int, UseColumn("author")]

    # Python field: comment_text, Database column: text
    comment_text: Annotated[str, UseColumn("text")]

    # Python field: comment_creation_date, maps to 'created_at' column.
    # This overrides the `created_at` field from DefaultTimestampMixin.
    comment_creation_date: Annotated[Optional[datetime], UseColumn("created_at")] = None

    # Python field: is_approved, Database column: approved
    is_approved: Annotated[bool, UseColumn("approved")]


class IntToStringAdapter(BaseSQLTypeAdapter):
    """A simple type adapter that converts an integer for the DB to a string for Python."""

    def __init__(self):
        super().__init__()
        self.register_type(str, int)  # Python 'str' can be converted to DB 'int'

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
    @classmethod
    def table_name(cls):
        return 'column_mapping_items'

    # Primary key defaults to 'id'. item_id attribute maps to this 'id' column.
    item_id: Annotated[Optional[int], UseColumn("id")] = Field(default=None)
    name: str  # Default mapping
    item_count: Annotated[int, UseColumn("item_total")]  # Mapped to 'item_total'
    notes: Annotated[str, UseAdapter(IntToStringAdapter(), target_db_type=int), UseColumn("remarks")] # Mapped to 'remarks' with an adapter

class AsyncColumnMappingModel(AsyncActiveRecord):
    """
    A model demonstrating various valid uses of UseColumn and UseAdapter,
    including mapping the primary key attribute.
    """
    @classmethod
    def table_name(cls):
        return 'column_mapping_items'

    c: ClassVar[FieldProxy] = FieldProxy()

    # Primary key defaults to 'id'. item_id attribute maps to this 'id' column.
    item_id: Annotated[Optional[int], UseColumn("id")] = Field(default=None)
    name: str  # Default mapping
    item_count: Annotated[int, UseColumn("item_total")]  # Mapped to 'item_total'
    notes: Annotated[str, UseAdapter(IntToStringAdapter(), target_db_type=int), UseColumn("remarks")] # Mapped to 'remarks' with an adapter


class ListToStringAdapter(BaseSQLTypeAdapter):
    """Converts a Python list of strings to a single comma-separated string for the DB."""

    def __init__(self):
        super().__init__()
        self.register_type(list, str)

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

        # A backend with a native array column returns a list/tuple as-is.
        if isinstance(value, (list, tuple)):
            return list(value)
        # If value is not a string, return as is (though this shouldn't happen with proper DB integration)
        return [value] if value is not None else []

# New adapter for JSON string conversion
class JsonToStringAdapter(BaseSQLTypeAdapter):
    """Converts a Python dictionary to a JSON string for the DB."""

    def __init__(self):
        super().__init__()
        self.register_type(dict, str)

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
    @classmethod
    def table_name(cls):
        return "mixed_annotation_items"

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

class AsyncMixedAnnotationModel(AsyncActiveRecord):
    """A model with various combinations of annotations to test field mapping and adapters."""
    @classmethod
    def table_name(cls):
        return "mixed_annotation_items"

    c: ClassVar[FieldProxy] = FieldProxy()

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


class BulkUser(IntegerPKMixin, ActiveRecord):
    @classmethod
    def table_name(cls):
        return "bulk_users"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    age: int = 0
    email: Optional[str] = None


class AsyncBulkUser(IntegerPKMixin, AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "bulk_users"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    age: int = 0
    email: Optional[str] = None


# =============================================================================
# Composite Primary Key Models
# =============================================================================

class OrderItem(CompositePKMixin, ActiveRecord):
    """Composite PK (order_id, product_id), PK provided by application."""
    @classmethod
    def table_name(cls):
        return "order_items"

    @classmethod
    def primary_key(cls):
        return ("order_id", "product_id")

    c: ClassVar[FieldProxy] = FieldProxy()

    order_id: int
    product_id: int
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class AsyncOrderItem(CompositePKMixin, AsyncActiveRecord):
    """Async variant of OrderItem."""
    @classmethod
    def table_name(cls):
        return "order_items"

    @classmethod
    def primary_key(cls):
        return ("order_id", "product_id")

    c: ClassVar[FieldProxy] = FieldProxy()

    order_id: int
    product_id: int
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class StoreInventory(CompositePKMixin, ActiveRecord):
    """Triple-column composite PK."""
    @classmethod
    def table_name(cls):
        return "store_inventory"

    @classmethod
    def primary_key(cls):
        return ("store_id", "product_id", "batch_id")

    c: ClassVar[FieldProxy] = FieldProxy()

    store_id: int
    product_id: int
    batch_id: str
    stock: int = 0


class AsyncStoreInventory(CompositePKMixin, AsyncActiveRecord):
    """Async variant of StoreInventory."""
    @classmethod
    def table_name(cls):
        return "store_inventory"

    @classmethod
    def primary_key(cls):
        return ("store_id", "product_id", "batch_id")

    c: ClassVar[FieldProxy] = FieldProxy()

    store_id: int
    product_id: int
    batch_id: str
    stock: int = 0


class Order(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Single-column auto-increment PK — backward compatibility control group."""
    @classmethod
    def table_name(cls):
        return "orders"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    total: Decimal = Decimal("0.00")


class AsyncOrder(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async variant of Order."""
    @classmethod
    def table_name(cls):
        return "orders"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    total: Decimal = Decimal("0.00")


class MappedOrderItem(CompositePKMixin, ActiveRecord):
    """Composite PK with UseColumn mapping — Python field names differ from DB column names."""
    @classmethod
    def table_name(cls):
        return "order_items"

    @classmethod
    def primary_key(cls):
        return ("order_id", "product_id")

    order_ref: Annotated[int, UseColumn("order_id")]
    product_ref: Annotated[int, UseColumn("product_id")]
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class AsyncMappedOrderItem(CompositePKMixin, AsyncActiveRecord):
    """Async variant of MappedOrderItem."""
    @classmethod
    def table_name(cls):
        return "order_items"

    @classmethod
    def primary_key(cls):
        return ("order_id", "product_id")

    c: ClassVar[FieldProxy] = FieldProxy()

    order_ref: Annotated[int, UseColumn("order_id")]
    product_ref: Annotated[int, UseColumn("product_id")]
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


# =============================================================================
# Derived Field Models
# =============================================================================

from rhosocial.activerecord.base import DerivedField
from rhosocial.activerecord.backend.expression import NumericColumn, Literal


class Product(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )]]


class AsyncProduct(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )]]


class ProductFormA(ActiveRecord):
    """Form A declaration: ClassVar[DerivedField] = DerivedField(...)."""
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    )

    total_value: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )


class AsyncProductFormA(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    )

    total_value: ClassVar[DerivedField] = DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    )


class PriceToIntAdapter:
    """Adapter that rounds float price to int for from_database."""

    def to_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        return float(value)

    def from_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]] = None) -> Any:
        return int(round(value))

    @property
    def supported_types(self) -> Dict[Type, Set[Type]]:
        return {int: {float}}


class ProductWithProxy(ActiveRecord):
    """Product model using FieldProxy in DerivedField expressions."""
    @classmethod
    def table_name(cls):
        return "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: ProductWithProxy.c.price * Literal(d, 0.9),
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: ProductWithProxy.c.price * ProductWithProxy.c.quantity,
    )]]


class AsyncProductWithProxy(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    c: ClassVar[FieldProxy] = FieldProxy()
    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: AsyncProductWithProxy.c.price * Literal(d, 0.9),
    )]]

    total_value: ClassVar[Annotated[float, DerivedField(
        lambda d: AsyncProductWithProxy.c.price * AsyncProductWithProxy.c.quantity,
    )]]


class ProductWithColumnAndAdapter(ActiveRecord):
    """Product model with UseColumn and UseAdapter on derived fields."""
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    ), UseColumn("disc")]]

    total_int: ClassVar[Annotated[int, DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    ), UseAdapter(PriceToIntAdapter(), int)]]


class AsyncProductWithColumnAndAdapter(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "product"

    id: Optional[int] = None
    name: str
    price: float
    quantity: int

    discounted_price: ClassVar[Annotated[float, DerivedField(
        lambda d: NumericColumn(d, "price") * Literal(d, 0.9),
    ), UseColumn("disc")]]

    total_int: ClassVar[Annotated[int, DerivedField(
        lambda d: NumericColumn(d, "price") * NumericColumn(d, "quantity"),
    ), UseAdapter(PriceToIntAdapter(), int)]]


# --- L1 fixture definitions ---------------------------------------------------
# A definition class receives only a ``dialect``: it builds the DDL expressions
# its model needs and knows nothing about backends, databases, or execution.
# Which definitions an environment uses, and in what order, is decided by the
# L2 fixtures in each test directory.
#
# The shared suite names only generic concepts; a backend name, or a
# backend-specific assumption, must never appear here.


class Definition:
    """Base class for this topic's table definitions."""

    model = None
    async_model = None
    table_name = ""

    def __init__(self, dialect, table_name=None):
        self.dialect = dialect
        self.name = table_name or type(self).table_name
        self.create_table = CreateTable(
            dialect,
            table=Table(dialect, self.name),
            columns=self.columns(),
            table_constraints=self.table_constraints(),
        )
        self.drop_table = DropTable(dialect, table=Table(dialect, self.name))

    def columns(self):
        raise NotImplementedError

    def table_constraints(self):
        return []

    def column(self, name, sql_type, constraints=None):
        return Column(self.dialect, name, sql_type, constraints=constraints or [])

    def auto_pk(self, name="id"):
        return self.column(
            name,
            Int(self.dialect),
            [
                Constraint(
                    self.dialect,
                    branch=PrimaryKey(self.dialect, is_auto_increment=True),
                )
            ],
        )

    def pk(self, name, sql_type):
        return self.column(
            name,
            sql_type,
            [Constraint(self.dialect, branch=PrimaryKey(self.dialect))],
        )

    def text(self, name):
        return self.column(name, short_text(self.dialect))

    def longtext(self, name):
        return self.column(name, long_text(self.dialect))

    def timestamp(self, name):
        return self.column(name, timestamp_type(self.dialect))

    def default(self, name, sql_type, value):
        return self.column(
            name,
            sql_type,
            [Constraint(self.dialect, branch=Default(self.dialect, value))],
        )

    def not_null(self, name, sql_type):
        return self.column(
            name,
            sql_type,
            [Constraint(self.dialect, branch=NotNull(self.dialect))],
        )


class UserDefinition(Definition):
    """The users table; it carries the union of the basic and mapped models."""

    model = resolve("User")
    async_model = resolve("AsyncUser")
    table_name = "users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.text("email"),
            self.column("age", Int(self.dialect)),
            self.column("balance", Float(self.dialect)),
            self.column("is_active", Bool(self.dialect)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class PostDefinition(Definition):
    model = resolve("MappedPost")
    async_model = resolve("AsyncMappedPost")
    table_name = "posts"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("author", Int(self.dialect)),
            self.text("title"),
            self.longtext("content"),
            self.timestamp("published_at"),
            self.column("published", Bool(self.dialect)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class CommentDefinition(Definition):
    model = resolve("MappedComment")
    async_model = resolve("AsyncMappedComment")
    table_name = "comments"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("post_ref", Int(self.dialect)),
            self.column("author", Int(self.dialect)),
            self.text("text"),
            self.timestamp("created_at"),
            self.column("approved", Bool(self.dialect)),
            self.timestamp("updated_at"),
        ]


class TypeCaseDefinition(Definition):
    model = resolve("TypeCase")
    async_model = resolve("AsyncTypeCase")
    table_name = "type_cases"

    def columns(self):
        return [
            self.pk("id", VarChar(self.dialect, 64)),
            self.text("username"),
            self.text("email"),
            self.column("tiny_int", TinyInt(self.dialect)),
            self.column("small_int", SmallInt(self.dialect)),
            self.column("big_int", BigInt(self.dialect)),
            self.column("float_val", Float(self.dialect)),
            self.column("double_val", Double(self.dialect)),
            self.column("decimal_val", Numeric(self.dialect, 10, 4)),
            self.text("char_val"),
            self.text("varchar_val"),
            self.longtext("text_val"),
            self.column("date_val", date_type(self.dialect)),
            self.column("time_val", time_type(self.dialect)),
            self.column("timestamp_val", timestamp_type(self.dialect)),
            self.column("blob_val", Blob(self.dialect)),
            self.column("json_val", json_text(self.dialect)),
            self.column("array_val", array_type(self.dialect, Int(self.dialect))),
            self.column("is_active", Bool(self.dialect)),
        ]


class TypeTestDefinition(Definition):
    model = resolve("TypeTestModel")
    async_model = resolve("AsyncTypeTestModel")
    table_name = "type_tests"

    def columns(self):
        return [
            self.pk("id", VarChar(self.dialect, 64)),
            self.text("string_field"),
            self.column("int_field", Int(self.dialect)),
            self.column("float_field", Float(self.dialect)),
            self.column("decimal_field", Numeric(self.dialect, 12, 4)),
            self.column("bool_field", Bool(self.dialect)),
            self.column("datetime_field", timestamp_type(self.dialect)),
            self.text("json_field"),
            self.text("nullable_field"),
        ]


class ValidatedFieldUserDefinition(Definition):
    model = resolve("ValidatedFieldUser")
    async_model = resolve("AsyncValidatedFieldUser")
    table_name = "validated_field_users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.text("email"),
            self.column("age", Int(self.dialect)),
            self.column("balance", Float(self.dialect)),
            self.column("credit_score", Int(self.dialect)),
            self.default("status", VarChar(self.dialect, 32), "active"),
            self.column("is_active", Bool(self.dialect)),
        ]


class ValidatedUserDefinition(Definition):
    model = resolve("ValidatedUser")
    async_model = resolve("AsyncValidatedUser")
    table_name = "validated_users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.text("email"),
            self.column("age", Int(self.dialect)),
        ]


class PydanticValidatedModelDefinition(Definition):
    model = resolve("PydanticValidatedModel")
    async_model = resolve("AsyncPydanticValidatedModel")
    table_name = "pydantic_validated_models"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("code"),
            self.column("quantity", Int(self.dialect)),
            self.column("step_count", Int(self.dialect)),
            self.column("price", Numeric(self.dialect, 12, 4)),
            self.timestamp("start_at"),
            self.timestamp("end_at"),
            self.default("status", VarChar(self.dialect, 32), "draft"),
            self.text("normalized_name"),
            self.default("created_token", VarChar(self.dialect, 128), "generated-token"),
        ]


class TypeAdapterTestDefinition(Definition):
    model = resolve("TypeAdapterTest")
    async_model = resolve("AsyncTypeAdapterTest")
    table_name = "type_adapter_tests"

    def columns(self):
        return [
            self.auto_pk(),
            self.not_null("name", short_text(self.dialect)),
            self.text("optional_name"),
            self.column("optional_age", Int(self.dialect)),
            self.text("last_login"),
            self.column("is_premium", Bool(self.dialect)),
            self.text("unsupported_union"),
            self.text("custom_bool"),
            self.text("optional_custom_bool"),
        ]


class ColumnMappingItemDefinition(Definition):
    model = resolve("ColumnMappingModel")
    async_model = resolve("AsyncColumnMappingModel")
    table_name = "column_mapping_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.column("item_total", Int(self.dialect)),
            self.text("remarks"),
        ]


class MixedAnnotationItemDefinition(Definition):
    model = resolve("MixedAnnotationModel")
    async_model = resolve("AsyncMixedAnnotationModel")
    table_name = "mixed_annotation_items"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            # ``tags`` is a list serialized by ``ListToStringAdapter`` into a
            # string column, so it must stay text even where the dialect has a
            # native array type.
            self.longtext("tags"),
            self.text("meta"),
            self.longtext("description"),
            self.default("status", VarChar(self.dialect, 32), "active"),
        ]


class BulkUserDefinition(Definition):
    model = resolve("BulkUser")
    async_model = resolve("AsyncBulkUser")
    table_name = "bulk_users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.default("age", Int(self.dialect), 0),
            self.text("email"),
        ]


class OrderDefinition(Definition):
    model = resolve("Order")
    async_model = resolve("AsyncOrder")
    table_name = "orders"

    def columns(self):
        return [
            self.auto_pk(),
            self.column("total", Numeric(self.dialect, 12, 4)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class OrderItemDefinition(Definition):
    """Composite-key order item owned by the basic topic."""

    model = resolve("OrderItem")
    async_model = resolve("AsyncOrderItem")
    table_name = "order_items"

    def columns(self):
        return [
            self.column("order_id", Int(self.dialect)),
            self.column("product_id", Int(self.dialect)),
            self.column("quantity", Int(self.dialect)),
            self.column("unit_price", Numeric(self.dialect, 12, 4)),
        ]

    def table_constraints(self):
        return [
            TableConstraint(
                self.dialect,
                branch=TablePrimaryKey(
                    self.dialect, ["order_id", "product_id"]
                ),
            )
        ]


class ProductDefinition(Definition):
    model = resolve("Product")
    async_model = resolve("AsyncProduct")
    table_name = "product"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.column("price", Float(self.dialect)),
            self.column("quantity", Int(self.dialect)),
        ]


class StoreInventoryDefinition(Definition):
    model = resolve("StoreInventory")
    async_model = resolve("AsyncStoreInventory")
    table_name = "store_inventory"

    def columns(self):
        return [
            self.column("store_id", Int(self.dialect)),
            self.column("product_id", Int(self.dialect)),
            self.column("batch_id", VarChar(self.dialect, 64)),
            self.default("stock", Int(self.dialect), 0),
        ]

    def table_constraints(self):
        return [
            TableConstraint(
                self.dialect,
                branch=TablePrimaryKey(
                    self.dialect, ["store_id", "product_id", "batch_id"]
                ),
            )
        ]


class TestUserDefinition(Definition):
    """The connection-pool tests' table; its model lives in that directory."""

    table_name = "test_users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.text("email"),
        ]


BASIC_DEFINITIONS = {
    "users": UserDefinition,
    "test_users": TestUserDefinition,
    "type_cases": TypeCaseDefinition,
    "type_tests": TypeTestDefinition,
    "validated_field_users": ValidatedFieldUserDefinition,
    "validated_users": ValidatedUserDefinition,
    "pydantic_validated_models": PydanticValidatedModelDefinition,
    "type_adapter_tests": TypeAdapterTestDefinition,
    "posts": PostDefinition,
    "comments": CommentDefinition,
    "column_mapping_items": ColumnMappingItemDefinition,
    "mixed_annotation_items": MixedAnnotationItemDefinition,
    "bulk_users": BulkUserDefinition,
    "orders": OrderDefinition,
    "order_items": OrderItemDefinition,
    "product": ProductDefinition,
    "store_inventory": StoreInventoryDefinition,
}
