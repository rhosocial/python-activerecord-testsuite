# src/rhosocial/activerecord/testsuite/feature/query/fixtures/models_py311.py
"""
Python 3.11+ fixture model definitions for query feature tests.

This file contains model classes using Python 3.11+ syntax features:
- `Self` type for methods that return an instance of the same class
- `X | Y` syntax (inherited from 3.10+)

Note: This file should only be imported and used in Python 3.11+ environments.
"""
from __future__ import annotations

import copy
from decimal import Decimal
from typing import ClassVar, Self

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import HasMany, BelongsTo, HasOne, CacheConfig
from rhosocial.activerecord.base.fields import UseColumn
from typing import Annotated


# Declare that this module requires Python 3.11+
__requires_python__ = (3, 11)


class User(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with basic relations.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "users"

    id: int | None = None  # Primary key, null for new records
    username: str  # Required field
    email: EmailStr  # Required field
    age: int | None = Field(..., ge=0, le=100)  # Optional field
    balance: float = 0.0  # Field with default value
    is_active: bool = True  # Field with default value

    orders: ClassVar[HasMany['Order']] = HasMany(foreign_key='user_id', inverse_of='user')
    posts: ClassVar[HasMany['Post']] = HasMany(
        foreign_key='user_id',
        inverse_of='user'
    )
    comments: ClassVar[HasMany['Comment']] = HasMany(
        foreign_key='user_id',
        inverse_of='user'
    )

    profile: ClassVar[HasOne['Profile']] = HasOne(
        foreign_key='user_id',
        inverse_of='user'
    )

    def activate(self) -> Self:
        """Activate the user and return self for chaining."""
        self.is_active = True
        return self

    def deactivate(self) -> Self:
        """Deactivate the user and return self for chaining."""
        self.is_active = False
        return self

    def with_balance(self, new_balance: float) -> Self:
        """Return a new instance with updated balance."""
        new_user = copy.deepcopy(self)
        new_user.balance = new_balance
        return new_user


class Profile(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Profile model with HasOne relation to User.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "profiles"

    id: int | None = None
    user_id: int
    bio: str | None = None
    avatar_url: str | None = None

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        inverse_of='profile'
    )


class JsonUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model specialized for JSON testing.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "json_users"

    id: int | None = None
    username: str
    email: EmailStr
    age: int | None = Field(None, ge=0, le=100)

    # JSON fields
    settings: str | None = None
    tags: str | None = None
    profile: str | None = None
    roles: str | None = None
    scores: str | None = None
    subscription: str | None = None
    preferences: str | None = None


class Order(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Order model with basic relations.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "orders"

    id: int | None = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[HasMany['OrderItem']] = HasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[BelongsTo['User']] = BelongsTo(foreign_key='user_id', inverse_of='orders')

    def mark_paid(self) -> Self:
        """Mark order as paid and return self for chaining."""
        self.status = 'paid'
        return self


class OrderItem(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Order item model with basic relations.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "order_items"

    id: int | None = None
    order_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal = Field(default=Decimal('0'))

    order: ClassVar[BelongsTo['Order']] = BelongsTo(foreign_key='order_id', inverse_of='items')


class OrderWithCustomCache(Order):
    """Order model with custom TTL cache configuration."""
    __table_name__ = "orders"

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        cache_config=CacheConfig(ttl=1)
    )


class OrderWithLimitedCache(Order):
    """Order model with limited cache size configuration."""
    __table_name__ = "orders"

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        cache_config=CacheConfig(max_size=2)
    )


class OrderWithComplexCache(Order):
    """Order model with complex cache configuration."""
    __table_name__ = "orders"

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        cache_config=CacheConfig(ttl=300, max_size=100)
    )

    items: ClassVar[HasMany['OrderItem']] = HasMany(
        foreign_key='order_id',
        cache_config=CacheConfig(ttl=60, max_size=1000),
    )


class Post(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Post model with user and comments relations.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "posts"

    id: int | None = None
    user_id: int
    title: str
    content: str
    status: str = 'published'

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        inverse_of='posts'
    )
    comments: ClassVar[HasMany['Comment']] = HasMany(
        foreign_key='post_id',
        inverse_of='post'
    )

    def publish(self) -> Self:
        """Publish the post and return self for chaining."""
        self.status = 'published'
        return self


class Comment(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Comment model with user and post relations.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "comments"

    id: int | None = None
    user_id: int
    post_id: int
    content: str
    is_hidden: bool = False

    user: ClassVar[BelongsTo['User']] = BelongsTo(
        foreign_key='user_id',
        inverse_of='comments'
    )
    post: ClassVar[BelongsTo['Post']] = BelongsTo(
        foreign_key='post_id',
        inverse_of='comments'
    )

    def hide(self) -> Self:
        """Hide the comment and return self for chaining."""
        self.is_hidden = True
        return self

    def show(self) -> Self:
        """Show the comment and return self for chaining."""
        self.is_hidden = False
        return self


# --- Mapped Models ---

class MappedUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with custom column name mappings for testing in query feature.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()

    __table_name__ = "users"
    __primary_key__ = "id"

    user_id: Annotated[int | None, UseColumn("id")] = None
    user_name: Annotated[str, UseColumn("username")]
    email_address: Annotated[str, UseColumn("email")]
    created_at: Annotated[str | None, UseColumn("created_time")] = None

    posts: ClassVar[HasMany["MappedPost"]] = HasMany(
        foreign_key="author",
        inverse_of="author"
    )
    comments: ClassVar[HasMany["MappedComment"]] = HasMany(
        foreign_key="author",
        inverse_of="author"
    )


class MappedPost(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Post model with custom column name mappings for testing in query feature.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()

    __table_name__ = "posts"
    __primary_key__ = "id"

    post_id: Annotated[int | None, UseColumn("id")] = None
    author_id: Annotated[int, UseColumn("author")]
    post_title: Annotated[str, UseColumn("title")]
    post_content: Annotated[str, UseColumn("content")]
    published_at: Annotated[str | None, UseColumn("published_time")] = None
    is_published: Annotated[bool, UseColumn("published")]

    author: ClassVar[BelongsTo["MappedUser"]] = BelongsTo(
        foreign_key="author",
        inverse_of="posts"
    )
    comments: ClassVar[HasMany["MappedComment"]] = HasMany(
        foreign_key="post_ref",
        inverse_of="post"
    )


class MappedComment(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Comment model with custom column name mappings for testing in query feature.

    Python 3.11+ version using | syntax and Self type.
    """
    c: ClassVar[FieldProxy] = FieldProxy()

    __table_name__ = "comments"
    __primary_key__ = "id"

    comment_id: Annotated[int | None, UseColumn("id")] = None
    post_id: Annotated[int, UseColumn("post_ref")]
    author_id: Annotated[int, UseColumn("author")]
    comment_text: Annotated[str, UseColumn("text")]
    created_at: Annotated[str | None, UseColumn("created_time")] = None
    is_approved: Annotated[bool, UseColumn("approved")]

    post: ClassVar[BelongsTo["MappedPost"]] = BelongsTo(
        foreign_key="post_ref",
        inverse_of="comments"
    )
    author: ClassVar[BelongsTo["MappedUser"]] = BelongsTo(
        foreign_key="author",
        inverse_of="comments"
    )
