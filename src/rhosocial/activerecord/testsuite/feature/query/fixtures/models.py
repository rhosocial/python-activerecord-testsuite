# src/rhosocial/activerecord/testsuite/feature/query/fixtures/models.py
"""
This module defines the generic models used by the query feature tests in the
testsuite. These models are then configured with specific backends by the
provider implementations in each backend package.
"""
from decimal import Decimal
from typing import Optional, ClassVar

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from pydantic import Field, EmailStr

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin
from rhosocial.activerecord.relation import HasMany, BelongsTo, CacheConfig
from rhosocial.activerecord.base.fields import UseColumn


class User(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with basic relations."""
    __table_name__ = "users"

    id: Optional[int] = None  # Primary key, null for new records
    username: str  # Required field
    email: EmailStr  # Required field
    age: Optional[int] = Field(..., ge=0, le=100)  # Optional field
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


class JsonUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model specialized for JSON testing."""
    __table_name__ = "json_users"

    id: Optional[int] = None
    username: str
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=100)

    # JSON fields
    settings: Optional[str] = None
    tags: Optional[str] = None
    profile: Optional[str] = None
    roles: Optional[str] = None
    scores: Optional[str] = None
    subscription: Optional[str] = None
    preferences: Optional[str] = None


class Order(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Order model with basic relations."""
    __table_name__ = "orders"

    id: Optional[int] = None
    user_id: int
    order_number: str
    total_amount: Decimal = Field(default=Decimal('0'))
    status: str = 'pending'

    items: ClassVar[HasMany['OrderItem']] = HasMany(foreign_key='order_id', inverse_of='order')
    user: ClassVar[BelongsTo['User']] = BelongsTo(foreign_key='user_id', inverse_of='orders')


class OrderItem(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Order item model with basic relations."""
    __table_name__ = "order_items"

    id: Optional[int] = None
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
    """Post model with user and comments relations."""
    __table_name__ = "posts"

    id: Optional[int] = None
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


class Comment(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Comment model with user and post relations."""
    __table_name__ = "comments"

    id: Optional[int] = None
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

# --- Mapped Models (Added from new version) ---

class MappedUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with custom column name mappings for testing in query feature."""

    __table_name__ = "users"
    __primary_key__ = "id"

    user_id: Annotated[Optional[int], UseColumn("id")] = None
    user_name: Annotated[str, UseColumn("username")]
    email_address: Annotated[str, UseColumn("email")]
    created_at: Annotated[Optional[str], UseColumn("created_time")] = None

    posts: ClassVar[HasMany["MappedPost"]] = HasMany(
        foreign_key="author",
        inverse_of="author"
    )
    comments: ClassVar[HasMany["MappedComment"]] = HasMany(
        foreign_key="author",
        inverse_of="author"
    )


class MappedPost(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """Post model with custom column name mappings for testing in query feature."""

    __table_name__ = "posts"
    __primary_key__ = "id"

    post_id: Annotated[Optional[int], UseColumn("id")] = None
    author_id: Annotated[int, UseColumn("author")]
    post_title: Annotated[str, UseColumn("title")]
    post_content: Annotated[str, UseColumn("content")]
    published_at: Annotated[Optional[str], UseColumn("published_time")] = None
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
    """Comment model with custom column name mappings for testing in query feature."""

    __table_name__ = "comments"
    __primary_key__ = "id"

    comment_id: Annotated[Optional[int], UseColumn("id")] = None
    post_id: Annotated[int, UseColumn("post_ref")]
    author_id: Annotated[int, UseColumn("author")]
    comment_text: Annotated[str, UseColumn("text")]
    created_at: Annotated[Optional[str], UseColumn("created_time")] = None
    is_approved: Annotated[bool, UseColumn("approved")]

    post: ClassVar[BelongsTo["MappedPost"]] = BelongsTo(
        foreign_key="post_ref",
        inverse_of="comments"
    )
    author: ClassVar[BelongsTo["MappedUser"]] = BelongsTo(
        foreign_key="author",
        inverse_of="comments"
    )