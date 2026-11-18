# src/rhosocial/activerecord/testsuite/feature/setop/fixtures/models.py
"""Order model group for the ``setop`` topic (Python 3.8 baseline).

Trimmed from the former ``query/fixtures/models.py`` to the three models the
set-operation tests actually use: ``User``, ``Order``, ``OrderItem``.  The
composite-primary-key set-operation tests borrow ``OrderItem`` from the basic
topic's public name instead (see ``setop/conftest.py``).
"""
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import HasMany, BelongsTo


class User(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """User model with the ``orders`` relation used by the order group."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "users"

    id: Optional[int] = None  # Primary key, null for new records
    username: str  # Required field
    email: EmailStr  # Required field
    age: Optional[int] = Field(..., ge=0, le=100)  # Optional field
    balance: float = 0.0  # Field with default value
    is_active: bool = True  # Field with default value

    orders: ClassVar[HasMany['Order']] = HasMany(foreign_key='user_id', inverse_of='user')


class Order(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order model carrying the status/amount columns the set operations query."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "orders"

    id: Optional[int] = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[HasMany['OrderItem']] = HasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[BelongsTo['User']] = BelongsTo(foreign_key='user_id', inverse_of='orders')


class OrderItem(IntegerPKMixin, DefaultTimestampMixin, ActiveRecord):
    """Order item model with its ``order`` relation."""
    c: ClassVar[FieldProxy] = FieldProxy()

    @classmethod
    def table_name(cls):
        return "order_items"

    id: Optional[int] = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal = Field(default=Decimal('0'))

    order: ClassVar[BelongsTo['Order']] = BelongsTo(foreign_key='order_id', inverse_of='items')
