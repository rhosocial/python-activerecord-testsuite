# src/rhosocial/activerecord/testsuite/feature/ddl/fixtures/models.py
"""DDL derivation fixture models."""

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from typing import ClassVar, Optional
from uuid import UUID

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression.statements.ddl_table import (
    ColumnConstraintType,
    ForeignKeyConstraint,
    GeneratedColumnExpression,
    GeneratedColumnType,
    IndexDefinition,
    ReferentialAction,
    TableConstraint,
    TableConstraintType,
)
from rhosocial.activerecord.backend.expression.types import JsonType, VarCharType
from rhosocial.activerecord.base import (
    UseConstraint,
    UseGeneratedColumn,
    UseSqlType,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import UUIDMixin
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class BareItem(ActiveRecord):
    __table_name__ = "ddl_bare_items"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    quantity: int
    price: float
    note: Optional[str] = None


class AsyncBareItem(AsyncActiveRecord):
    __table_name__ = "ddl_bare_items"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    name: str
    quantity: int
    price: float
    note: Optional[str] = None


class SpecOrder(UUIDMixin, ActiveRecord):
    __table_name__ = "ddl_spec_orders"
    c: ClassVar[FieldProxy] = FieldProxy()

    code: Annotated[str, UseSqlType(VarCharType(length=32))]
    status: Annotated[
        str,
        UseConstraint(
            ColumnConstraintType.CHECK,
            check_condition=lambda dialect: Column(dialect, "status").in_(
                ["open", "paid", "shipped"]
            ),
            name="ck_spec_orders_status",
        ),
    ]
    quantity: Annotated[int, UseConstraint(ColumnConstraintType.NOT_NULL)] = 1
    total: float = 0.0

    __table_constraints__ = [
        TableConstraint(
            None,
            TableConstraintType.UNIQUE,
            name="uq_ddl_spec_orders_code_status",
            columns=["code", "status"],
        )
    ]
    __table_indexes__ = [
        IndexDefinition(None, name="ix_ddl_spec_orders_code", columns=["code"])
    ]


class AsyncSpecOrder(UUIDMixin, AsyncActiveRecord):
    __table_name__ = "ddl_spec_orders"
    c: ClassVar[FieldProxy] = FieldProxy()

    code: Annotated[str, UseSqlType(VarCharType(length=32))]
    status: Annotated[
        str,
        UseConstraint(
            ColumnConstraintType.CHECK,
            check_condition=lambda dialect: Column(dialect, "status").in_(
                ["open", "paid", "shipped"]
            ),
            name="ck_spec_orders_status",
        ),
    ]
    quantity: Annotated[int, UseConstraint(ColumnConstraintType.NOT_NULL)] = 1
    total: float = 0.0

    __table_constraints__ = [
        TableConstraint(
            None,
            TableConstraintType.UNIQUE,
            name="uq_ddl_spec_orders_code_status",
            columns=["code", "status"],
        )
    ]
    __table_indexes__ = [
        IndexDefinition(None, name="ix_ddl_spec_orders_code", columns=["code"])
    ]


class CapabilityPost(ActiveRecord):
    __table_name__ = "ddl_capability_posts"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    title: str
    views: int = 0
    is_published: int = 0
    meta: Annotated[Optional[dict], UseSqlType(JsonType())] = None
    double_views: Annotated[
        int,
        UseGeneratedColumn(
            lambda dialect: GeneratedColumnExpression(
                dialect,
                expression=Column(dialect, "views") * 2,
                storage_type=GeneratedColumnType.STORED,
            )
        ),
    ] = 0

    __table_indexes__ = [
        IndexDefinition(
            None,
            name="ix_ddl_capability_posts_title",
            columns=["title"],
        )
    ]


class AsyncCapabilityPost(AsyncActiveRecord):
    __table_name__ = "ddl_capability_posts"
    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    title: str
    views: int = 0
    is_published: int = 0
    meta: Annotated[Optional[dict], UseSqlType(JsonType())] = None
    double_views: Annotated[
        int,
        UseGeneratedColumn(
            lambda dialect: GeneratedColumnExpression(
                dialect,
                expression=Column(dialect, "views") * 2,
                storage_type=GeneratedColumnType.STORED,
            )
        ),
    ] = 0

    __table_indexes__ = [
        IndexDefinition(
            None,
            name="ix_ddl_capability_posts_title",
            columns=["title"],
        )
    ]


class SpecComment(ActiveRecord):
    __table_name__ = "ddl_spec_comments"
    c: ClassVar[FieldProxy] = FieldProxy()

    __primary_key__ = "comment_id"
    __pk_auto_generated__ = False

    comment_id: int
    order_id: UUID
    body: str

    __table_constraints__ = [
        ForeignKeyConstraint(
            None,
            columns=["order_id"],
            foreign_key_table="ddl_spec_orders",
            foreign_key_columns=["id"],
            on_delete=ReferentialAction.CASCADE,
            name="fk_ddl_spec_comments_order",
        )
    ]


class AsyncSpecComment(AsyncActiveRecord):
    __table_name__ = "ddl_spec_comments"
    c: ClassVar[FieldProxy] = FieldProxy()

    __primary_key__ = "comment_id"
    __pk_auto_generated__ = False

    comment_id: int
    order_id: UUID
    body: str

    __table_constraints__ = [
        ForeignKeyConstraint(
            None,
            columns=["order_id"],
            foreign_key_table="ddl_spec_orders",
            foreign_key_columns=["id"],
            on_delete=ReferentialAction.CASCADE,
            name="fk_ddl_spec_comments_order",
        )
    ]


__all__ = [
    "BareItem",
    "AsyncBareItem",
    "SpecOrder",
    "AsyncSpecOrder",
    "CapabilityPost",
    "AsyncCapabilityPost",
    "SpecComment",
    "AsyncSpecComment",
]
