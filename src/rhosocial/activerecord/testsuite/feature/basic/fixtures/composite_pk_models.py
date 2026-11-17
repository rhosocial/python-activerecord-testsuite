# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/composite_pk_models.py
"""The ``crud_composite_pk`` group: its models and table registrations.

The composite-key model bodies moved here from ``models.py``; a composite key
is never identity-generated, so no identifier annotation is needed. The table
registrations derive DDL from these models through ``operations.py``.
"""

from decimal import Decimal
from typing import Optional

try:  # Python 3.8
    from typing import Annotated, ClassVar
except ImportError:  # pragma: no cover
    from typing_extensions import Annotated, ClassVar

from rhosocial.activerecord.base.fields import UseColumn
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import CompositePKMixin, DefaultTimestampMixin, IntegerPKMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .operations import Operation, TableFixture

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


_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))

COMPOSITE_PK_FIXTURES = (
    TableFixture(table="orders", source=Order, operations=_OPS),
    TableFixture(table="order_items", source=OrderItem, operations=_OPS),
    TableFixture(table="store_inventory", source=StoreInventory, operations=_OPS),
)

__all__ = [
    "AsyncOrder",
    "AsyncOrderItem",
    "COMPOSITE_PK_FIXTURES",
    "MappedOrderItem",
    "Order",
    "OrderItem",
    "StoreInventory",
]
