# src/rhosocial/activerecord/testsuite/feature/derived_field/interfaces.py
from abc import ABC, abstractmethod
from typing import Type, List

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class IDerivedFieldProvider(ABC):

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        pass

    @abstractmethod
    def setup_product_model(self, scenario_name: str) -> Type[ActiveRecord]:
        pass

    @abstractmethod
    def setup_product_form_a_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Setup product model using Form A declaration (ClassVar assignment)."""
        pass

    @abstractmethod
    def setup_product_with_proxy_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Setup product model using FieldProxy in DerivedField expressions."""
        pass

    @abstractmethod
    def setup_product_with_column_and_adapter_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """Setup product model using UseColumn and UseAdapter on derived fields."""
        pass

    @abstractmethod
    def setup_async_product_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        """Setup async product model."""
        pass

    def setup_async_product_form_a_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        """Setup async product model using Form A declaration (ClassVar assignment).

        Default implementation raises NotImplementedError. Backends should override
        this method to support async product form A model tests.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support setup_async_product_form_a_model"
        )

    @abstractmethod
    def setup_async_product_with_proxy_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        """Setup async product model using FieldProxy."""
        pass

    @abstractmethod
    def setup_async_product_with_column_and_adapter_model(self, scenario_name: str) -> Type[AsyncActiveRecord]:
        """Setup async product model using UseColumn and UseAdapter."""
        pass

    async def cleanup_after_test_async(self, scenario_name: str) -> None:
        """Perform async cleanup after a test.

        Default implementation raises NotImplementedError. Backends should override
        this method to support async cleanup.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support cleanup_after_test_async"
        )

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str) -> None:
        pass
