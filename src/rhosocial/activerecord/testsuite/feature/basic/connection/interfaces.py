# src/rhosocial/activerecord/testsuite/feature/basic/connection/interfaces.py
"""
Interface definitions for connection pool context awareness tests.

This module defines the interface that backend test providers must implement
to support ActiveRecord connection pool context awareness testing.
"""
from abc import ABC, abstractmethod
from typing import Type, Tuple

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.connection.pool import BackendPool, AsyncBackendPool


class IBasicConnectionProvider(ABC):
    """
    Interface for providers that support connection pool context awareness tests
    for basic ActiveRecord operations.
    """

    @abstractmethod
    def get_test_scenarios(self) -> list:
        """
        Return a list of scenario names that this backend supports.

        Returns:
            List[str]: A list of supported scenario names.
        """
        pass

    @abstractmethod
    def setup_sync_pool_and_model(self, scenario_name: str) -> Tuple[BackendPool, Type[ActiveRecord]]:
        """
        Setup a sync connection pool and a test model for context awareness tests.

        Args:
            scenario_name: The test scenario name

        Returns:
            Tuple containing the pool instance and the configured model class
        """
        pass

    @abstractmethod
    def setup_async_pool_and_model(self, scenario_name: str) -> Tuple['AsyncBackendPool', Type[AsyncActiveRecord]]:
        """
        Setup an async connection pool and a test model for context awareness tests.

        Args:
            scenario_name: The test scenario name

        Returns:
            Tuple containing the pool instance and the configured model class
        """
        pass

    @abstractmethod
    def cleanup_sync(self, scenario_name: str, pool: BackendPool):
        """
        Cleanup after sync tests.

        Args:
            scenario_name: The test scenario name
            pool: The pool instance to close
        """
        pass

    @abstractmethod
    async def cleanup_async(self, scenario_name: str, pool: 'AsyncBackendPool'):
        """
        Cleanup after async tests.

        Args:
            scenario_name: The test scenario name
            pool: The pool instance to close
        """
        pass

    @abstractmethod
    def setup_sync_pool_for_crud(self, scenario_name: str) -> Tuple[BackendPool, Type[ActiveRecord]]:
        """
        Setup a sync connection pool and model for CRUD operation tests.

        Args:
            scenario_name: The test scenario name

        Returns:
            Tuple containing the pool instance and the configured model class
        """
        pass

    @abstractmethod
    async def setup_async_pool_for_crud(self, scenario_name: str) -> Tuple['AsyncBackendPool', Type[AsyncActiveRecord]]:
        """
        Setup an async connection pool and model for CRUD operation tests.

        Args:
            scenario_name: The test scenario name

        Returns:
            Tuple containing the pool instance and the configured model class
        """
        pass
