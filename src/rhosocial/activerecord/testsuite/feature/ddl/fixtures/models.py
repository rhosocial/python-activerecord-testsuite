# src/rhosocial/activerecord/testsuite/feature/ddl/fixtures/models.py
"""
Fixture model definitions for the ``feature.ddl`` test group.

The declared constants and field annotations are the single source of truth:
``ModelSchemaGenerator.generate_create_table(dialect)`` derives the DDL from
exactly these declarations. Providers execute the derived statements, so the
tests verify the "model -> DDL -> live database" round trip on every backend.

Three declaration levels are covered:

1. **Zero declaration** — ``BareItem``: no DDL Specs at all. Verifies the
   default derivation rules (field name = column name, Python type via
   ``suggest_column_type``, required -> NOT NULL, PK rules).
2. **Generic Specs** — ``SpecOrder`` (UUID PK) and ``SpecComment`` (explicit
   integer PK): the portable, standard-semantics Specs. Primary keys come in
   three shapes across the fixtures (auto integer / UUID / explicit integer)
   to show that derivation follows the model's PK metadata
   (``__primary_key__`` / ``__pk_auto_generated__``) rather than any mixin.
3. **Capability Specs** — ``CapabilityPost``: Specs whose acceptance is gated
   by backend capability (partial index, JSON column, generated column).
   Backends claim what they support and silently ignore the rest; the tests
   assert that derivation and execution succeed either way.

Sync and async (``Async``-prefixed) variants share identical declarations.

Python-version notes: this module sticks to Python 3.8-compatible syntax
(``Optional[X]``, ``typing.Annotated`` import guard) so the base fixtures run
everywhere. Python 3.10+ syntax variants (``X | None``) live in
``models_py310.py`` and are selected via ``select_fixture``.
"""

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from typing import Optional

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.base import (
    UseSqlType,
    UseConstraint,
    UseIndex,
    ColumnConstraintType,
    CheckSpec,
    UniqueSpec,
    NotNullSpec,
    PrimaryKeySpec,
    DefaultSpec,
    ForeignKeySpec,
    IndexSpec,
    PartialIndexSpec,
    JsonColumnSpec,
    GeneratedColumnSpec,
)
from typing import ClassVar

from rhosocial.activerecord.backend.expression.types import VarCharType
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import UUIDMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


# ---------------------------------------------------------------------------
# 1. Zero declaration (auto integer PK via the default PK metadata)
# ---------------------------------------------------------------------------
class BareItem(ActiveRecord):
    """No DDL declarations at all — default derivation rules apply.

    Uses the default PK metadata (``__primary_key__ = "id"`` with
    ``__pk_auto_generated__ = True``), so the derived DDL carries an
    auto-incrementing integer primary key.
    """

    __table_name__ = "ddl_bare_items"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    quantity: int
    price: float
    note: Optional[str] = None


class AsyncBareItem(AsyncActiveRecord):
    """Async twin of :class:`BareItem` (same declarations)."""

    __table_name__ = "ddl_bare_items"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    quantity: int
    price: float
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# 2. Generic Specs — UUID PK
# ---------------------------------------------------------------------------
class SpecOrder(UUIDMixin, ActiveRecord):
    """Generic DDL Specs on a UUID primary key.

    The PK is application-generated (``UUIDMixin``); the derived DDL renders a
    non-auto-increment PK column of the UUID-representing type.
    """

    __table_name__ = "ddl_spec_orders"
    c: ClassVar[FieldProxy] = FieldProxy()

    # Field-level annotations
    code: Annotated[str, UseSqlType(VarCharType(length=32))]
    status: Annotated[str, UseConstraint(
        ColumnConstraintType.CHECK,
        check_condition=lambda d: Column(d, "status").in_(["open", "paid", "shipped"]),
        name="ck_spec_orders_status",
    )]
    quantity: Annotated[int, UseConstraint(ColumnConstraintType.NOT_NULL)] = 1

    # Table-level generic Specs
    __table_constraints__ = [
        UniqueSpec(columns=["code", "status"], name="uq_ddl_spec_orders_code_status"),
        DefaultSpec(column="quantity", value=1),
        IndexSpec(columns=["code"], name="ix_ddl_spec_orders_code"),
    ]

    total: float = 0.0


class AsyncSpecOrder(UUIDMixin, AsyncActiveRecord):
    """Async twin of :class:`SpecOrder` (same declarations)."""

    __table_name__ = "ddl_spec_orders"
    c: ClassVar[FieldProxy] = FieldProxy()

    code: Annotated[str, UseSqlType(VarCharType(length=32))]
    status: Annotated[str, UseConstraint(
        ColumnConstraintType.CHECK,
        check_condition=lambda d: Column(d, "status").in_(["open", "paid", "shipped"]),
        name="ck_spec_orders_status",
    )]
    quantity: Annotated[int, UseConstraint(ColumnConstraintType.NOT_NULL)] = 1

    __table_constraints__ = [
        UniqueSpec(columns=["code", "status"], name="uq_ddl_spec_orders_code_status"),
        DefaultSpec(column="quantity", value=1),
        IndexSpec(columns=["code"], name="ix_ddl_spec_orders_code"),
    ]

    total: float = 0.0


# ---------------------------------------------------------------------------
# 3. Capability Specs
# ---------------------------------------------------------------------------
class CapabilityPost(ActiveRecord):
    """Capability-gated Specs: each backend claims what it supports.

    - ``PartialIndexSpec``: gated by ``supports_partial_index``
    - ``JsonColumnSpec``: portable ``JsonType`` (native JSON or TEXT)
    - ``GeneratedColumnSpec``: gated by ``supports_generated_columns``
    """

    __table_name__ = "ddl_capability_posts"
    c: ClassVar[FieldProxy] = FieldProxy()

    __table_constraints__ = [
        JsonColumnSpec("meta"),
        GeneratedColumnSpec(
            "double_views",
            expression=lambda d: Column(d, "views") * 2,
            stored=True,
        ),
    ]
    __table_indexes__ = [
        PartialIndexSpec(
            columns=["title"],
            condition=lambda d: Column(d, "is_published") == 1,
            name="ix_ddl_capability_posts_published_title",
        ),
    ]

    id: Optional[int] = None
    title: str
    views: int = 0
    is_published: int = 0
    meta: object = None
    double_views: int = 0


class AsyncCapabilityPost(AsyncActiveRecord):
    """Async twin of :class:`CapabilityPost` (same declarations)."""

    __table_name__ = "ddl_capability_posts"
    c: ClassVar[FieldProxy] = FieldProxy()

    __table_constraints__ = [
        JsonColumnSpec("meta"),
        GeneratedColumnSpec(
            "double_views",
            expression=lambda d: Column(d, "views") * 2,
            stored=True,
        ),
    ]
    __table_indexes__ = [
        PartialIndexSpec(
            columns=["title"],
            condition=lambda d: Column(d, "is_published") == 1,
            name="ix_ddl_capability_posts_published_title",
        ),
    ]

    id: Optional[int] = None
    title: str
    views: int = 0
    is_published: int = 0
    meta: object = None
    double_views: int = 0


# ---------------------------------------------------------------------------
# 4. Generic Specs — explicit integer PK (application-assigned)
# ---------------------------------------------------------------------------
class SpecComment(ActiveRecord):
    """``PrimaryKeySpec`` / ``ForeignKeySpec`` / ``NotNullSpec`` on an
    explicitly-assigned integer PK."""

    __table_name__ = "ddl_spec_comments"
    c: ClassVar[FieldProxy] = FieldProxy()

    __primary_key__ = "comment_id"
    __pk_auto_generated__ = False

    __table_constraints__ = [
        PrimaryKeySpec(columns=["comment_id"]),
        ForeignKeySpec(
            local_columns=["order_id"],
            ref_table="ddl_spec_orders",
            ref_columns=["id"],
            on_delete="CASCADE",
            name="fk_ddl_spec_comments_order",
        ),
        NotNullSpec(column="body"),
    ]

    comment_id: int
    order_id: "object"  # UUID of the referenced SpecOrder (UUID-typed PK)
    body: str


class AsyncSpecComment(AsyncActiveRecord):
    """Async twin of :class:`SpecComment`."""

    __table_name__ = "ddl_spec_comments"
    c: ClassVar[FieldProxy] = FieldProxy()

    __primary_key__ = "comment_id"
    __pk_auto_generated__ = False

    __table_constraints__ = [
        PrimaryKeySpec(columns=["comment_id"]),
        ForeignKeySpec(
            local_columns=["order_id"],
            ref_table="ddl_spec_orders",
            ref_columns=["id"],
            on_delete="CASCADE",
            name="fk_ddl_spec_comments_order",
        ),
        NotNullSpec(column="body"),
    ]

    comment_id: int
    order_id: "object"  # UUID of the referenced SpecOrder (UUID-typed PK)
    body: str


__all__ = [
    "BareItem", "AsyncBareItem",
    "SpecOrder", "AsyncSpecOrder",
    "CapabilityPost", "AsyncCapabilityPost",
    "SpecComment", "AsyncSpecComment",
]
