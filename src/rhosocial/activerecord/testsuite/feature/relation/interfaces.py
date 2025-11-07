# src/rhosocial/activerecord/testsuite/feature/relation/interfaces.py
"""
This file defines the interface (or contract) that a backend's test provider
must adhere to for the "relation" feature group.

By defining a standard interface, the generic tests in the testsuite can rely on
these methods being available, regardless of which database backend is actually
running the tests. Each backend must provide a concrete class that implements
these abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Type, List, Tuple
from rhosocial.activerecord.model import ActiveRecord


class IRelationProvider(ABC):
    """
    The interface for the provider of the 'relation' feature tests.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.
        """
        pass

    @abstractmethod
    def setup_employee_department_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the employee-department models (Employee, Department)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (Employee, Department) model classes
        """
        pass

    @abstractmethod
    def setup_author_book_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the author-book models (Author, Book, Chapter, Profile)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (Author, Book, Chapter, Profile) model classes
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass
