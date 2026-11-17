# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/type_adapter_models.py
"""Type-adapter fixtures for the ``basic/type_adapter`` group.

The group has one bare/annotated pair sharing a single table (``adapter_rows``):

* ``AdapterRow`` / ``AsyncAdapterRow`` write only Python type annotations.
* ``AdapterRowAnnotated`` / ``AsyncAdapterRowAnnotated`` add ``UseColumn``,
  ``UseAdapter`` and ``UseColumnType``.  Those markers change how a value is
  adapted, not the stored columns (README section 2 P2), so both models bind
  to the same table and the declaration tests compare their derived DDL.

Identity is not a variant axis (F11).  Sync and async twins share one mixin
per variant (P4).  The legacy ``TypeAdapterTest``/``AsyncTypeAdapterTest``
models stay on their own ``type_adapter_tests`` table for the existing adapter
contracts; they are not part of this variant pair.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Type, Union

from rhosocial.activerecord.backend.expression import NumericColumn
from rhosocial.activerecord.backend.expression.types import TextType
from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseAdapter, UseColumn, UseColumnType, UseSqlType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .operations import Operation, TableFixture

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


# --- bare / annotated adapter variants (shared table) ------------------------


class ScaleByTenAdapter:
    """Store an int multiplied by ten, divide it back on read.

    The adaptation keeps the stored value an int, so the annotated variant
    derives exactly the same DDL as the bare one while giving the behavior
    tests a real value transformation to observe.
    """

    def to_database(self, value, target_type, options=None):
        return None if value is None else value * 10

    def from_database(self, value, target_type, options=None, original_type=None):
        # ``original_type`` is the declared annotation; this adapter only needs
        # the driver value.
        return None if value is None else value // 10

    @property
    def supported_types(self):
        return {int: {int}}


class AdapterRowFields:
    """Bare fields: Python annotations only, zero ``Annotated`` markers."""

    id: Optional[int] = None
    label: str
    count: int


class AdapterRowAnnotatedFields:
    """Annotated fields: column rename, value adapter and column class.

    Only non-storage-changing markers appear here, so this model derives the
    very same ``adapter_rows`` table as :class:`AdapterRowFields`.  ``title``
    maps to the ``label`` column and ``scaled`` to ``count``.
    """

    id: Optional[int] = None
    title: Annotated[str, UseColumn("label")]
    scaled: Annotated[
        int,
        UseColumn("count"),
        UseAdapter(ScaleByTenAdapter(), int),
        UseColumnType(NumericColumn),
    ]


class AdapterRow(AdapterRowFields, ActiveRecord):
    """Bare adapter variant, bound to ``adapter_rows``."""

    @classmethod
    def table_name(cls):
        return "adapter_rows"


class AsyncAdapterRow(AdapterRowFields, AsyncActiveRecord):
    """Async twin of :class:`AdapterRow` (P4: same fields, same table)."""

    @classmethod
    def table_name(cls):
        return "adapter_rows"


class AdapterRowAnnotated(AdapterRowAnnotatedFields, ActiveRecord):
    """Fully annotated adapter variant, bound to the same ``adapter_rows`` table."""

    @classmethod
    def table_name(cls):
        return "adapter_rows"


class AsyncAdapterRowAnnotated(AdapterRowAnnotatedFields, AsyncActiveRecord):
    """Async twin of :class:`AdapterRowAnnotated` (P4)."""

    @classmethod
    def table_name(cls):
        return "adapter_rows"


# --- End of module-level definitions ---

_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))
TYPE_ADAPTER_FIXTURES = (
    TableFixture(table="type_adapter_tests", source=TypeAdapterTest, operations=_OPS),
)

_ADAPTER_COLUMN_SWITCHES = (
    ("id", "integer"),
    ("label", "varchar"),
    ("count", "integer"),
)
_ADAPTER_COLUMN_OPS = tuple(
    Operation("create_table", requires_on=(switch,), column=column)
    for column, switch in _ADAPTER_COLUMN_SWITCHES
)
TYPE_ADAPTER_VARIANT_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(
        table="adapter_rows",
        source=AdapterRow,
        operations=_OPS + _ADAPTER_COLUMN_OPS,
    ),
)

__all__ = [
    "TYPE_ADAPTER_FIXTURES",
    "TYPE_ADAPTER_VARIANT_FIXTURES",
    "AdapterRow",
    "AdapterRowAnnotated",
    "AsyncAdapterRow",
    "AsyncAdapterRowAnnotated",
    "AsyncTypeAdapterTest",
    "ScaleByTenAdapter",
    "TypeAdapterTest",
    "YesOrNoBooleanAdapter",
]
