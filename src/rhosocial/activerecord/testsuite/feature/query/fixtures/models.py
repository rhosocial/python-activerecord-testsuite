# src/rhosocial/activerecord/testsuite/feature/query/fixtures/models.py
"""
This file defines the generic ActiveRecord model classes used by the query tests.

These models are "generic" because they define the data structure and validation
rules (using Pydantic), but they are not tied to any specific database backend.
The backend-specific provider is responsible for taking these classes and
configuring them with a live database connection at test time.
"""
from datetime import datetime
from typing import ClassVar, Optional

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from pydantic import EmailStr, Field

from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin, UUIDMixin
from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.relation import HasMany, BelongsTo
from rhosocial.activerecord.base.fields import UseColumn

class User(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """A standard User model for general CRUD operation testing."""
    __table_name__ = "users"

    username: str
    email: EmailStr
    age: Optional[int] = Field(..., ge=0, le=100)
    balance: float = 0.0
    is_active: bool = True

    # Relationships
    posts: ClassVar[HasMany["Post"]] = HasMany(
        foreign_key="author_id",
        inverse_of="author"
    )
    comments: ClassVar[HasMany["Comment"]] = HasMany(
        foreign_key="author_id",
        inverse_of="author"
    )


class Post(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """A standard Post model for general CRUD operation testing."""
    __table_name__ = "posts"

    author_id: int
    title: str
    content: str
    is_published: bool = False
    published_at: Optional[datetime] = None

    # Relationships
    author: ClassVar[BelongsTo["User"]] = BelongsTo(
        foreign_key="author_id",
        inverse_of="posts"
    )
    comments: ClassVar[HasMany["Comment"]] = HasMany(
        foreign_key="post_id",
        inverse_of="post"
    )


class Comment(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """A standard Comment model for general CRUD operation testing."""
    __table_name__ = "comments"

    post_id: int
    author_id: int
    content: str
    is_approved: bool = True

    # Relationships
    post: ClassVar[BelongsTo["Post"]] = BelongsTo(
        foreign_key="post_id",
        inverse_of="comments"
    )
    author: ClassVar[BelongsTo["User"]] = BelongsTo(
        foreign_key="author_id",
        inverse_of="comments"
    )

class JsonUser(UUIDMixin, ActiveRecord):
    """A User model for testing JSON field types."""
    __table_name__ = "json_users"

    username: str
    metadata: Optional[dict] = None # JSON field

class MappedUser(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """User model with custom column name mappings for testing in query feature."""

    __table_name__ = "users"
    __primary_key__ = "id"

    # Python field: user_id, Database column: id
    user_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: user_name, Database column: username
    user_name: Annotated[str, UseColumn("username")]

    # Python field: email_address, Database column: email
    email_address: Annotated[str, UseColumn("email")]

    # Python field: created_at, Database column: created_time
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

    # Python field: post_id, Database column: id
    post_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: author_id, Database column: author
    author_id: Annotated[int, UseColumn("author")]

    # Python field: post_title: Annotated[str, UseColumn("title")]
    post_title: Annotated[str, UseColumn("title")]

    # Python field: post_content: Annotated[str, UseColumn("content")]
    post_content: Annotated[str, UseColumn("content")]

    # Python field: published_at, Database column: published_time
    published_at: Annotated[Optional[str], UseColumn("published_time")] = None

    # Python field: is_published, Database column: published
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

    # Python field: comment_id, Database column: id
    comment_id: Annotated[Optional[int], UseColumn("id")] = None

    # Python field: post_id, Database column: post_ref
    post_id: Annotated[int, UseColumn("post_ref")]

    # Python field: author_id: Annotated[int, UseColumn("author")]
    author_id: Annotated[int, UseColumn("author")]

    # Python field: comment_text, Database column: text
    comment_text: Annotated[str, UseColumn("text")]

    # Python field: created_at, Database column: created_time
    created_at: Annotated[Optional[str], UseColumn("created_time")] = None

    # Python field: is_approved, Database column: approved
    is_approved: Annotated[bool, UseColumn("approved")]

    post: ClassVar[BelongsTo["MappedPost"]] = BelongsTo(
        foreign_key="post_ref",
        inverse_of="comments"
    )
    author: ClassVar[BelongsTo["MappedUser"]] = BelongsTo(
        foreign_key="author",
        inverse_of="comments"
    )
