from typing import Optional, ClassVar

from pydantic import Field, EmailStr
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo


class AsyncMappedUser(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async User model with SQLAlchemy mapped annotations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "users"

    id: Optional[int] = None
    username: str = mapped_column(String(50), nullable=False)
    email: EmailStr = mapped_column(String(100), nullable=False)
    age: Optional[int] = mapped_column(Integer, default=Field(default=0, ge=0, le=100))
    balance: float = mapped_column(default=0.0)
    is_active: bool = mapped_column(default=True)

    orders: ClassVar[AsyncHasMany['AsyncMappedOrder']] = AsyncHasMany(foreign_key='user_id', inverse_of='user')


class AsyncMappedPost(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Post model with SQLAlchemy mapped annotations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "posts"

    id: Optional[int] = None
    user_id: int = mapped_column(Integer, nullable=False)
    title: str = mapped_column(String(200), nullable=False)
    content: str = mapped_column(nullable=False)
    status: str = mapped_column(String(20), default='published')

    user: ClassVar[AsyncBelongsTo['AsyncMappedUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='posts')


class AsyncMappedComment(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async Comment model with SQLAlchemy mapped annotations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "comments"

    id: Optional[int] = None
    user_id: int = mapped_column(Integer, nullable=False)
    post_id: int = mapped_column(Integer, nullable=False)
    content: str = mapped_column(nullable=False)
    is_hidden: bool = mapped_column(default=False)

    user: ClassVar[AsyncBelongsTo['AsyncMappedUser']] = AsyncBelongsTo(foreign_key='user_id', inverse_of='comments')
    post: ClassVar[AsyncBelongsTo['AsyncMappedPost']] = AsyncBelongsTo(foreign_key='post_id', inverse_of='comments')