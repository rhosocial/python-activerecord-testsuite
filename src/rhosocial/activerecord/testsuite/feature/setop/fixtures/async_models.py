# src/rhosocial/activerecord/testsuite/feature/setop/fixtures/async_models.py
"""Async order model group for the ``setop`` topic.

Async twins of ``setop/fixtures/models.py``: ``AsyncUser``, ``AsyncOrder`` and
``AsyncOrderItem`` only.
"""

from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo


class AsyncUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async User model with the ``orders`` relation used by the order group."""

    @classmethod
    def table_name(cls):
        return "users"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    orders: ClassVar[AsyncHasMany['AsyncOrder']] = AsyncHasMany(foreign_key='user_id', inverse_of='user')


class AsyncOrder(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async Order model carrying the status/amount columns the set operations query."""

    @classmethod
    def table_name(cls):
        return "orders"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[AsyncHasMany['AsyncOrderItem']] = AsyncHasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='orders')


class AsyncOrderItem(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async Order item model with its ``order`` relation."""

    @classmethod
    def table_name(cls):
        return "order_items"

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal = Field(default=Decimal('0'))

    order: ClassVar[AsyncBelongsTo['AsyncOrder']] = AsyncBelongsTo(foreign_key='order_id', inverse_of='items')
