# src/rhosocial/activerecord/testsuite/feature/setop/fixtures/models_py310.py
"""Python 3.10+ order model group for the ``setop`` topic.

Uses ``X | Y`` instead of ``Optional[X]``.  Only ``User``, ``Order`` and
``OrderItem`` are kept from the former query fixture set.
"""
from decimal import Decimal
from typing import ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import HasMany, BelongsTo


# Declare that this module requires Python 3.10+
__requires_python__ = (3, 10)


class User(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """User model with basic relations, using 3.10+ ``|`` syntax."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "users"

    id: int | None = None  # Primary key, null for new records
    username: str
    email: EmailStr
    age: int | None = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    orders: ClassVar[HasMany['Order']] = HasMany(foreign_key='user_id', inverse_of='user')


class Order(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order model, using 3.10+ ``|`` syntax."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "orders"

    id: int | None = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[HasMany['OrderItem']] = HasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[BelongsTo['User']] = BelongsTo(foreign_key='user_id', inverse_of='orders')


class OrderItem(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order item model, using 3.10+ ``|`` syntax."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "order_items"

    id: int | None = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal = Field(default=Decimal('0'))

    order: ClassVar[BelongsTo['Order']] = BelongsTo(foreign_key='order_id', inverse_of='items')
