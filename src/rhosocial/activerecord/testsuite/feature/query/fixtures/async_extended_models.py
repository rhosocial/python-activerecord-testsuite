# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_extended_models.py
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo


class AsyncUser(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async User model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "users"

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    orders: ClassVar[AsyncHasMany['AsyncExtendedOrder']] = AsyncHasMany(foreign_key='user_id', inverse_of='user')


class AsyncExtendedOrder(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async ExtendedOrder model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "extended_orders"

    id: Optional[int] = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0.00'))
    status: str = 'pending'
    priority: str = 'medium'
    region: str = 'default'
    category: str = ''
    product: str = ''
    department: str = ''
    year: str = ''
    quarter: str = ''

    items: ClassVar[AsyncHasMany['AsyncExtendedOrderItem']] = AsyncHasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='orders')


class AsyncExtendedOrderItem(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async ExtendedOrderItem model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "extended_order_items"

    id: Optional[int] = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    price: Decimal
    category: str = ''
    region: str = ''

    order: ClassVar[AsyncBelongsTo['AsyncExtendedOrder']] = AsyncBelongsTo(foreign_key='order_id', inverse_of='items')