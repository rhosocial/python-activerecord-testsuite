# src/rhosocial/activerecord/testsuite/feature/basic/interfaces.py
"""
This file defines the interface (or contract) that a backend's test provider
must adhere to for the "basic" feature group.

By defining a standard interface, the generic tests in the testsuite can rely on
these methods being available, regardless of which database backend is actually
running the tests. Each backend must provide a concrete class that implements
these abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Type, List
from rhosocial.activerecord.model import ActiveRecord

class IBasicProvider(ABC):
    """
    The interface for the provider of the 'basic' feature tests.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.
        """
        pass

    @abstractmethod
    def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `User` model under a
        given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def setup_type_case_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `TypeCase` model under a
        given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def setup_type_test_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `TypeTestModel` model under a
        given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def setup_validated_field_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `ValidatedFieldUser` model
        under a given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def setup_validated_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the `ValidatedUser` model
        under a given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass
