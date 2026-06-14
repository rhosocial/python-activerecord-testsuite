from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo, AsyncHasOne


class AsyncUser(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async User model with basic relations."""
    __table_name__ = "users"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    orders: ClassVar[AsyncHasMany['AsyncOrder']] = AsyncHasMany(foreign_key='user_id', inverse_of='user')
    posts: ClassVar[AsyncHasMany['AsyncPost']] = AsyncHasMany(foreign_key='user_id', inverse_of='author')
    comments: ClassVar[AsyncHasMany['AsyncComment']] = AsyncHasMany(foreign_key='user_id', inverse_of='author')

    profile: ClassVar[AsyncHasOne['AsyncProfile']] = AsyncHasOne(
        foreign_key='user_id',
        inverse_of='user'
    )


class AsyncOrder(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Order model with basic relations."""
    __table_name__ = "orders"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[AsyncHasMany['AsyncOrderItem']] = AsyncHasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='orders')


class AsyncOrderItem(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Order item model with basic relations."""
    __table_name__ = "order_items"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal = Field(default=Decimal('0'))

    order: ClassVar[AsyncBelongsTo['AsyncOrder']] = AsyncBelongsTo(foreign_key='order_id', inverse_of='items')


class AsyncProfile(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Profile model with HasOne relation to AsyncUser.

    Mirrors sync Profile for sync/async parity.
    Used for testing HasOne batch loading via with_().
    """
    __table_name__ = "profiles"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    user_id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    user: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(
        foreign_key='user_id',
        inverse_of='profile'
    )


class AsyncPost(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Post model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "posts"

    id: Optional[int] = None
    user_id: int
    title: str
    content: str
    status: str = 'published'

    author: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='posts')
    comments: ClassVar[AsyncHasMany['AsyncComment']] = AsyncHasMany(foreign_key='post_id', inverse_of='post')


class AsyncComment(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Comment model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "comments"

    id: Optional[int] = None
    user_id: int
    post_id: int
    content: str
    is_hidden: bool = False

    author: ClassVar[AsyncBelongsTo['AsyncUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='comments')
    post: ClassVar[AsyncBelongsTo['AsyncPost']] = AsyncBelongsTo(foreign_key='post_id', inverse_of='comments')
