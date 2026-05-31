# src/rhosocial/activerecord/testsuite/feature/derived_field/interfaces.py
from abc import ABC, abstractmethod
from typing import Type, List

from rhosocial.activerecord.model import ActiveRecord


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
    def cleanup_after_test(self, scenario_name: str) -> None:
        pass
