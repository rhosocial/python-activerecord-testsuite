# src/rhosocial/activerecord/testsuite/feature/relation/interfaces.py
"""
Interface (contract) that backend test providers must implement for 'relation' feature tests.

Each backend (SQLite, MySQL, PostgreSQL, etc.) provides a concrete class that fulfills
this interface. The testsuite runs the same test logic regardless of backend, relying
on these methods for model setup, cleanup, and data loading.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Type
from rhosocial.activerecord.model import ActiveRecord


class RelationProviderBase(ABC):
    """
    The shared base for providers of the 'relation' feature tests, containing
    common non-I/O helper methods used by both sync and async providers.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.

        Returns:
            List[str]: A list of supported scenario names.
        """
        pass


class IRelationSyncProvider(RelationProviderBase):
    """
    The sync interface for the provider of the 'relation' feature tests.
    """

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
    def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup User model with HasMany posts, FieldProxy, DerivedField, and JSON fields.
        """
        pass

    @abstractmethod
    def setup_post_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup Post model with BelongsTo user, HasMany comments, FieldProxy, DerivedField, and JSON fields.
        """
        pass

    @abstractmethod
    def setup_comment_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup Comment model with BelongsTo post, FieldProxy, DerivedField, and JSON fields.
        """
        pass

    @abstractmethod
    def setup_relation_boundary_fixtures(
        self,
        scenario_name: str,
    ) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Setup models for backend-agnostic relation boundary tests.

        Returns:
            Tuple of (Owner, Profile, Post) model classes.
        """
        pass

    @abstractmethod
    def load_relation_boundary_dataset(
        self,
        scenario_name: str,
        dataset_name: str,
    ) -> Dict[str, int]:
        """
        Load a named relation boundary dataset.

        Implementations should return stable IDs keyed by semantic names so tests
        can query records without knowing backend-specific insert details.
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass


class IRelationAsyncProvider(RelationProviderBase):
    """
    The async interface for the provider of the 'relation' feature tests.
    """

    @abstractmethod
    async def setup_employee_department_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async employee-department models (AsyncEmployee, AsyncDepartment)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncEmployee, AsyncDepartment) model classes
        """
        pass

    @abstractmethod
    async def setup_author_book_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async author-book models (AsyncAuthor, AsyncBook, AsyncChapter, AsyncProfile)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncAuthor, AsyncBook, AsyncChapter, AsyncProfile) model classes
        """
        pass

    @abstractmethod
    async def setup_user_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup async User model.
        """
        pass

    @abstractmethod
    async def setup_post_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup async Post model.
        """
        pass

    @abstractmethod
    async def setup_comment_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Setup async Comment model.
        """
        pass

    @abstractmethod
    async def setup_relation_boundary_fixtures(
        self,
        scenario_name: str,
    ) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Setup async models for backend-agnostic relation boundary tests.

        Returns:
            Tuple of (AsyncOwner, AsyncProfile, AsyncPost) model classes.
        """
        pass

    @abstractmethod
    async def load_relation_boundary_dataset(
        self,
        scenario_name: str,
        dataset_name: str,
    ) -> Dict[str, int]:
        """
        Load a named async relation boundary dataset.
        """
        pass

    @abstractmethod
    async def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary async cleanup after a test has run.
        """
        pass
