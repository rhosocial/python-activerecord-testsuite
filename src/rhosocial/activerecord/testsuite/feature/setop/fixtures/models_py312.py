# src/rhosocial/activerecord/testsuite/feature/setop/fixtures/models_py312.py
"""Python 3.12+ order model group for the ``setop`` topic.

Keeps the version-specific ``@override`` / ``Self`` syntax probes from the
former query fixture copies; only ``User``, ``Order`` and ``OrderItem`` are
retained.
"""
from __future__ import annotations

import copy
from decimal import Decimal
from typing import ClassVar, Self, override

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import HasMany, BelongsTo


# Declare that this module requires Python 3.12+
__requires_python__ = (3, 12)


class User(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """User model, using 3.12+ ``@override`` and ``Self`` syntax."""
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

    @override
    def save(self, **kwargs) -> Self:
        super().save(**kwargs)
        return self

    def activate(self) -> Self:
        self.is_active = True
        return self

    def deactivate(self) -> Self:
        self.is_active = False
        return self

    def with_balance(self, new_balance: float) -> Self:
        new_user = copy.deepcopy(self)
        new_user.balance = new_balance
        return new_user


class Order(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order model, using 3.12+ ``Self`` syntax."""
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

    def mark_paid(self) -> Self:
        self.status = 'paid'
        return self


class OrderItem(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order item model, using 3.12+ ``Self`` syntax."""
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
