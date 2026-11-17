# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the basic tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""

from .operations import Operation, TableFixture
from datetime import datetime
from typing import Optional, Type, Union, Any, Dict


from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter
from rhosocial.activerecord.base.fields import UseAdapter, UseSqlType
from rhosocial.activerecord.backend.expression.types import TextType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy

# These mixins are assumed to be provided by the core `rhosocial-activerecord`
# package to handle common field behaviors like auto-incrementing IDs or timestamps.

try:
    from typing import Annotated, ClassVar
except ImportError:
    from typing_extensions import Annotated, ClassVar


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


class YesOrNoBooleanAdapter(BaseSQLTypeAdapter):
    """Converts Python's True/False to 'yes'/'no' strings."""

    def _do_to_database(
        self, value: bool, target_type: Type, options: Optional[Dict[str, Any]] = None
    ) -> str:
        return "yes" if value else "no"

    def _do_from_database(
        self, value: str, target_type: Type, options: Optional[Dict[str, Any]] = None
    ) -> bool:
        return value == "yes"


class TypeAdapterTest(ActiveRecord):
    """Model for testing various type adapter scenarios."""

    @classmethod
    def table_name(cls):
        return "type_adapter_tests"

    id: Optional[int] = None
    name: str
    # Fields for testing implicit Optional[T] handling
    optional_name: Optional[str] = None
    optional_age: Optional[int] = None
    last_login: Annotated[Optional[datetime], UseSqlType(TextType())] = None
    is_premium: Optional[bool] = None
    # Field for testing unsupported Union
    unsupported_union: Annotated[Union[str, int], UseSqlType(TextType())] = 0
    # Fields for testing explicit adapter annotation
    custom_bool: Annotated[
        bool, UseAdapter(YesOrNoBooleanAdapter(), str), UseSqlType(TextType())
    ] = None
    optional_custom_bool: Annotated[
        Optional[bool], UseAdapter(YesOrNoBooleanAdapter(), str), UseSqlType(TextType())
    ] = None


class AsyncTypeAdapterTest(AsyncActiveRecord):
    """Model for testing various type adapter scenarios."""

    @classmethod
    def table_name(cls):
        return "type_adapter_tests"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    # Fields for testing implicit Optional[T] handling
    optional_name: Optional[str] = None
    optional_age: Optional[int] = None
    last_login: Annotated[Optional[datetime], UseSqlType(TextType())] = None
    is_premium: Optional[bool] = None
    # Field for testing unsupported Union
    unsupported_union: Annotated[Union[str, int], UseSqlType(TextType())] = 0
    # Fields for testing explicit adapter annotation
    custom_bool: Annotated[
        bool, UseAdapter(YesOrNoBooleanAdapter(), str), UseSqlType(TextType())
    ] = None
    optional_custom_bool: Annotated[
        Optional[bool], UseAdapter(YesOrNoBooleanAdapter(), str), UseSqlType(TextType())
    ] = None


# --- End of module-level definitions ---

_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
TYPE_ADAPTER_FIXTURES = (
    TableFixture(table="type_adapter_tests", source=TypeAdapterTest, operations=_OPS),
)
