# src/rhosocial/activerecord/testsuite/feature/ddl/interfaces.py
"""
Provider interface for the ``feature.ddl`` test group.

Providers hand over configured model classes whose DDL declarations are the
single source of truth; the tests derive DDL via
``Model.generate_create_table(dialect)``, execute it through the backend, and
verify the resulting structure round-trips.
"""
from abc import ABC, abstractmethod
from typing import List, Type

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

from .fixtures.models import (
    AsyncBareItem,
    AsyncCapabilityPost,
    AsyncSpecComment,
    AsyncSpecOrder,
    BareItem,
    CapabilityPost,
    SpecComment,
    SpecOrder,
)


class DDLProviderBase(ABC):
    """Shared, non-I/O surface for ddl-group providers."""

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """Scenario names (database configurations) this backend supports."""
        pass


class IDDLSyncProvider(DDLProviderBase):
    """Sync interface: setup returns configured model classes."""

    @abstractmethod
    def setup_bare_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_spec_order_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_capability_post_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_spec_comment_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_spec_comment_with_parent_models(
        self, scenario_name: str
    ) -> "tuple[Type[ActiveRecord], Type[ActiveRecord]]":
        """Set up SpecComment and its parent SpecOrder on the same
        connection, so the FK target exists where inserts happen."""
        pass


class IDDLAsyncProvider(DDLProviderBase):
    """Async interface: setup returns configured async model classes."""

    @abstractmethod
    async def setup_bare_item_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        pass

    @abstractmethod
    async def setup_spec_order_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        pass

    @abstractmethod
    async def setup_capability_post_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        pass

    @abstractmethod
    async def setup_spec_comment_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        pass

    @abstractmethod
    async def setup_spec_comment_with_parent_models(
        self, scenario_name: str
    ) -> "tuple[Type[AsyncActiveRecord], Type[AsyncActiveRecord]]":
        pass


__all__ = [
    "DDLProviderBase", "IDDLSyncProvider", "IDDLAsyncProvider",
    "BareItem", "AsyncBareItem", "SpecOrder", "AsyncSpecOrder",
    "CapabilityPost", "AsyncCapabilityPost", "SpecComment", "AsyncSpecComment",
]
