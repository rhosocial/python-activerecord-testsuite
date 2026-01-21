# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_blog_models.py
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo, AsyncHasOne


class AsyncUser(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async User model with basic relations."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "users"

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    posts: ClassVar[AsyncHasMany['AsyncPost']] = AsyncHasMany(foreign_key='user_id', inverse_of='author')
    comments: ClassVar[AsyncHasMany['AsyncComment']] = AsyncHasMany(foreign_key='user_id', inverse_of='author')


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