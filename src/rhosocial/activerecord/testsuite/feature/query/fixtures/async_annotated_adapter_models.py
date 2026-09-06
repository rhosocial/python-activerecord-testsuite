# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_annotated_adapter_models.py
"""Async model fixtures using Annotated-based type adapters for query tests."""

from typing import Optional, ClassVar
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated, List
else:
    from typing_extensions import Annotated
    from typing import List

try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin
from rhosocial.activerecord.base.fields import UseAdapter

from .annotated_adapter_models import ListToStringAdapter


class AsyncSearchableItem(IntegerPKMixin, AsyncActiveRecord):
    """Async SearchableItem model for testing Annotated type adapters in queries."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "searchable_items"

    id: Optional[int] = None
    name: str = ""
    tags: Annotated[Optional[List[str]], UseAdapter(ListToStringAdapter(), str)] = None

    @field_validator('tags', mode='before')
    @classmethod
    def tags_must_be_list(cls, v):
        if v is None:
            return []
        return v
