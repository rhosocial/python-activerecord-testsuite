# src/rhosocial/activerecord/testsuite/feature/query/interfaces.py
"""
This file defines the interface (or contract) that a backend's test provider
must adhere to for the \"query\" feature group.

By defining a standard interface, the generic tests in the testsuite can rely on
these methods being available, regardless of which database backend is actually
running the tests. Each backend must provide a concrete class that implements
these abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Type, List, Tuple
from rhosocial.activerecord.model import ActiveRecord


class QueryProviderBase(ABC):
    """
    The shared base for providers of the 'query' feature tests, containing
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

    # --- Optional capability declarations ---

    def supports_orphan_relations(self) -> bool:
        """
        Whether this provider can create records whose FK points to
        non-existent parent records.

        Returns True if the schema does NOT enforce FK constraints
        (or uses ON DELETE SET NULL / CASCADE), allowing orphan FK
        references for testing purposes.

        Returns:
            bool: True if orphan FK references are possible.
        """
        return False

    # --- Deprecated: subclasses should move these to the concrete interface ---


class IQuerySyncProvider(QueryProviderBase):
    """
    The sync interface for the provider of the 'query' feature tests.
    """

    @abstractmethod
    def setup_order_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the order-related models (User, Order, OrderItem)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (User, Order, OrderItem) model classes
        """
        pass

    @abstractmethod
    def setup_blog_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the blog-related models (User, Post, Comment)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (User, Post, Comment) model classes
        """
        pass

    @abstractmethod
    def setup_json_user_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for the JSON user model
        under a given scenario and return a tuple containing the JsonUser model class.

        Returns:
            Tuple containing (JsonUser,) model class
        """
        pass

    @abstractmethod
    def setup_tree_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for the tree structure model (Node)
        under a given scenario and return a tuple containing the Node model class.

        Returns:
            Tuple containing (Node,) model class
        """
        pass

    @abstractmethod
    def setup_extended_order_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the extended order-related models (User, ExtendedOrder, ExtendedOrderItem)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (User, ExtendedOrder, ExtendedOrderItem) model classes
        """
        pass

    @abstractmethod
    def setup_combined_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the combined models (User, Order, OrderItem, Post, Comment)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (User, Order, OrderItem, Post, Comment) model classes
        """
        pass

    @abstractmethod
    def setup_annotated_query_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for models using Annotated type adapters in queries,
        under a given scenario and return a tuple containing the configured model class(es).

        Returns:
            Tuple containing (SearchableItem,) model class.
        """
        pass

    @abstractmethod
    def setup_mapped_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for `MappedUser`, `MappedPost`,
        and `MappedComment` models under a given scenario and return the
        configured model classes as a tuple.

        Returns:
            Tuple of (MappedUser, MappedPost, MappedComment) model classes
        """
        pass

    # --- Profile fixtures ---

    @abstractmethod
    def setup_profile_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for Profile (HasOne to User)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (User, Profile) model classes
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass

    # --- Composite primary key ---

    @abstractmethod
    def setup_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the composite-PK OrderItem model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured OrderItem model class.
        """
        pass


class IQueryAsyncProvider(QueryProviderBase):
    """
    The async interface for the provider of the 'query' feature tests.
    """

    @abstractmethod
    async def setup_order_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async order-related models (AsyncUser, AsyncOrder, AsyncOrderItem)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncUser, AsyncOrder, AsyncOrderItem) model classes
        """
        pass

    @abstractmethod
    async def setup_blog_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async blog-related models (AsyncUser, AsyncPost, AsyncComment)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncUser, AsyncPost, AsyncComment) model classes
        """
        pass

    @abstractmethod
    async def setup_json_user_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for the async JSON user model
        under a given scenario and return a tuple containing the AsyncJsonUser model class.

        Returns:
            Tuple containing (AsyncJsonUser,) model class
        """
        pass

    @abstractmethod
    async def setup_tree_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for the async tree structure model (AsyncNode)
        under a given scenario and return a tuple containing the AsyncNode model class.

        Returns:
            Tuple containing (AsyncNode,) model class
        """
        pass

    @abstractmethod
    async def setup_extended_order_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async extended order-related models (AsyncUser, AsyncExtendedOrder, AsyncExtendedOrderItem)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncUser, AsyncExtendedOrder, AsyncExtendedOrderItem) model classes
        """
        pass

    @abstractmethod
    async def setup_combined_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for the async combined models (AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment) model classes
        """
        pass

    @abstractmethod
    async def setup_annotated_query_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], ...]:
        """
        Should prepare the testing environment for async models using Annotated type adapters in queries,
        under a given scenario and return a tuple containing the configured model class(es).

        Returns:
            Tuple containing (AsyncSearchableItem,) model class.
        """
        pass

    @abstractmethod
    async def setup_mapped_models(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for `AsyncMappedUser`, `AsyncMappedPost`,
        and `AsyncMappedComment` models under a given scenario and return the
        configured model classes as a tuple.

        Returns:
            Tuple of (AsyncMappedUser, AsyncMappedPost, AsyncMappedComment) model classes
        """
        pass

    @abstractmethod
    async def setup_profile_fixtures(self, scenario_name: str) -> Tuple[Type[ActiveRecord], Type[ActiveRecord]]:
        """
        Should prepare the testing environment for AsyncProfile (HasOne to AsyncUser)
        under a given scenario and return a tuple of the configured model classes.

        Returns:
            Tuple of (AsyncUser, AsyncProfile) model classes
        """
        pass

    @abstractmethod
    async def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary async cleanup after a test has run.
        """
        pass

    # --- Composite primary key (async) ---

    @abstractmethod
    async def setup_order_item_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the async composite-PK OrderItem model
        under a given scenario and return the configured model class.

        Returns:
            Type[ActiveRecord]: The configured AsyncOrderItem model class.
        """
        pass
