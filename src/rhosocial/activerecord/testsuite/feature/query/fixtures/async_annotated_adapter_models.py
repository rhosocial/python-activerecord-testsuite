from typing import Optional, ClassVar
from pydantic import Field

from rhosocial.activerecord.model import AsyncActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin


class AsyncSearchableItem(IntegerPKMixin, TimestampMixin, AsyncActiveRecord):
    """Async SearchableItem model for testing Annotated type adapters in queries."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = "searchable_items"

    id: Optional[int] = None
    name: str = ""
    tags: str = ""