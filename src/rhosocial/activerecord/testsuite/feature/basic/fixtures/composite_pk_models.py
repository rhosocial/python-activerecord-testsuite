# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/composite_pk_models.py
"""Fixture registrations for the ``crud_composite_pk`` group.

The model bodies still live in ``models.py``; this module owns the table
registration that derives their DDL from the models themselves. A composite
key is never identity-generated, so no identifier annotation is needed here.
"""

from .models import (
    AsyncOrder,
    AsyncOrderItem,
    MappedOrderItem,
    Order,
    OrderItem,
    StoreInventory,
)
from .operations import Operation, TableFixture

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
