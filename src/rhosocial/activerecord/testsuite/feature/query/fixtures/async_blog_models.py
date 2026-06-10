# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_blog_models.py
"""Async blog model fixtures.

NOTE: AsyncUser is imported from async_models to guarantee sync/async parity —
the sync models.User is a single class, so the async AsyncUser must also be
a single class.  Importing avoids a second, incompatible AsyncUser class.
"""
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo

from .async_models import AsyncUser


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