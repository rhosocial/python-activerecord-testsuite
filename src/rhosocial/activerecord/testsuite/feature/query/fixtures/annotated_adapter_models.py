# src/rhosocial/activerecord/testsuite/feature/query/fixtures/annotated_adapter_models.py
"""Model fixtures using Annotated-based type adapters for query feature tests."""

import sys
from typing import Any, List, Type, Dict, Optional, Set, get_origin, ClassVar

# Conditionally import Annotated and field_validator based on Python version
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator

from rhosocial.activerecord.model import ActiveRecord
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.field import IntegerPKMixin, DefaultTimestampMixin
from rhosocial.activerecord.base.fields import UseAdapter
from rhosocial.activerecord.backend.type_adapter import BaseSQLTypeAdapter


class ListToStringAdapter(BaseSQLTypeAdapter):
    """
    Type adapter for converting a list of strings to a comma-separated string for the database
    and vice-versa.
    """
    def _do_to_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]]) -> Any:
        if not isinstance(value, list):
            raise TypeError(f"Expected a list for conversion to DB, got {type(value)}")
        if target_type == str:
            return ",".join(value)
        raise TypeError(f"ListToStringAdapter cannot convert to target DB type {target_type}")

    def _do_from_database(self, value: Any, target_type: Type, options: Optional[Dict[str, Any]]) -> Any:
        if value is None:
            return []
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception as e:
                raise TypeError(f"Expected a string from DB, got {type(value)}") from e
        
        if target_type == List[str] or get_origin(target_type) is list:
            if not value:
                return []
            return [item.strip() for item in value.split(',') if item.strip()]
            
        raise TypeError(f"ListToStringAdapter cannot convert from DB to target Python type {target_type}")

    @property
    def supported_types(self) -> Dict[Type, Set[Type]]:
        return {List[str]: {str}}


class SearchableItem(IntegerPKMixin, ActiveRecord):
    """Model for testing Annotated Type Adapters."""
    c: ClassVar[FieldProxy] = FieldProxy()
    __table_name__ = 'searchable_items'
    id: Optional[int] = None
    name: str
    tags: Annotated[Optional[List[str]], UseAdapter(ListToStringAdapter(), str)] = None

    @field_validator('tags', mode='before')
    @classmethod
    def tags_must_be_list(cls, v):
        if v is None:
            return []
        return v
