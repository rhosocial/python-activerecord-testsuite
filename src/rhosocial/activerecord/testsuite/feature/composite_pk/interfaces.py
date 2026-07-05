# src/rhosocial/activerecord/testsuite/feature/composite_pk/interfaces.py
from abc import ABC, abstractmethod
from typing import Type, List, Tuple
from rhosocial.activerecord.model import ActiveRecord


class ICompositePKProvider(ABC):
    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        pass

    @abstractmethod
    def setup_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_store_inventory_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_order_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_mapped_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    async def setup_async_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    async def setup_async_store_inventory_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    async def setup_async_order_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    async def setup_async_mapped_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        pass

    @abstractmethod
    async def cleanup_after_test_async(self, scenario_name: str):
        pass
