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


class IQueryProvider(ABC):
    """
    The interface for the provider of the 'query' feature tests.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.
        """
        pass

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
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass
