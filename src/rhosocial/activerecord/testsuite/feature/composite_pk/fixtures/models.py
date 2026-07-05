# src/rhosocial/activerecord/testsuite/feature/composite_pk/fixtures/models.py
from typing import ClassVar, Optional
from decimal import Decimal

from pydantic import Field

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.field import CompositePKMixin, IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.base.fields import UseColumn
from rhosocial.activerecord.base.field_proxy import FieldProxy

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated


class OrderItem(CompositePKMixin, ActiveRecord):
    """Composite PK (order_id, product_id), PK provided by application."""
    __table_name__ = "order_items"
    __primary_key__ = ("order_id", "product_id")
    c: ClassVar[FieldProxy] = FieldProxy()

    order_id: int
    product_id: int
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class AsyncOrderItem(CompositePKMixin, AsyncActiveRecord):
    """Async variant of OrderItem."""
    __table_name__ = "order_items"
    __primary_key__ = ("order_id", "product_id")
    c: ClassVar[FieldProxy] = FieldProxy()

    order_id: int
    product_id: int
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class StoreInventory(CompositePKMixin, ActiveRecord):
    """Triple-column composite PK."""
    __table_name__ = "store_inventory"
    __primary_key__ = ("store_id", "product_id", "batch_id")
    c: ClassVar[FieldProxy] = FieldProxy()

    store_id: int
    product_id: int
    batch_id: str
    stock: int = 0


class AsyncStoreInventory(CompositePKMixin, AsyncActiveRecord):
    """Async variant of StoreInventory."""
    __table_name__ = "store_inventory"
    __primary_key__ = ("store_id", "product_id", "batch_id")
    c: ClassVar[FieldProxy] = FieldProxy()

    store_id: int
    product_id: int
    batch_id: str
    stock: int = 0


class Order(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Single-column auto-increment PK — backward compatibility control group."""
    __table_name__ = "orders"
    __primary_key__ = "id"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    total: Decimal = Decimal("0.00")


class AsyncOrder(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async variant of Order."""
    __table_name__ = "orders"
    __primary_key__ = "id"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    total: Decimal = Decimal("0.00")


class MappedOrderItem(CompositePKMixin, ActiveRecord):
    """Composite PK with UseColumn mapping — Python field names differ from DB column names."""
    __table_name__ = "order_items"
    __primary_key__ = ("order_id", "product_id")

    order_ref: Annotated[int, UseColumn("order_id")]
    product_ref: Annotated[int, UseColumn("product_id")]
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")


class AsyncMappedOrderItem(CompositePKMixin, AsyncActiveRecord):
    """Async variant of MappedOrderItem."""
    __table_name__ = "order_items"
    __primary_key__ = ("order_id", "product_id")
    c: ClassVar[FieldProxy] = FieldProxy()

    order_ref: Annotated[int, UseColumn("order_id")]
    product_ref: Annotated[int, UseColumn("product_id")]
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
