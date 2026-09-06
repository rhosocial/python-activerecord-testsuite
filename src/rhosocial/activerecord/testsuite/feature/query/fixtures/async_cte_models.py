# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_cte_models.py
"""Async model fixtures for CTE query feature tests."""

from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.relation import AsyncHasMany, AsyncBelongsTo


class AsyncNode(IntegerPKMixin, DefaultTimestampMixin, AsyncActiveRecord):
    """Async Node model for tree structure tests (recursive CTEs)."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "nodes"

    id: Optional[int] = None
    name: str
    parent_id: Optional[int] = None
    value: Decimal = Field(default=Decimal('0.00'))

    # Self-referencing relation for tree structure
    parent: ClassVar[AsyncBelongsTo['AsyncNode']] = AsyncBelongsTo(foreign_key='parent_id', inverse_of='children')
    children: ClassVar[AsyncHasMany['AsyncNode']] = AsyncHasMany(foreign_key='parent_id', inverse_of='parent')