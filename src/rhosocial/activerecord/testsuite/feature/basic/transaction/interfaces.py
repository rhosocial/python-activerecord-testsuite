# src/rhosocial/activerecord/testsuite/feature/basic/transaction/interfaces.py
"""
Interface definitions for transaction API black-box tests.

This module defines the interface that backend test providers must implement
to support savepoint / release / rollback_to API contract tests defined in
the rhosocial-activerecord-testsuite transaction basic feature module.
"""
from abc import ABC, abstractmethod
from typing import Type, Tuple

from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord
from rhosocial.activerecord.connection.pool import BackendPool, AsyncBackendPool


class ITransactionBasicProvider(ABC):
    """Interface for providers supporting savepoint API black-box tests."""

    @abstractmethod
    def get_test_scenarios(self) -> list:
        """Return the list of supported scenario names."""
        pass

    @abstractmethod
    def setup_sync_pool_and_model(self, scenario_name: str) -> Tuple[BackendPool, Type[ActiveRecord]]:
        """Setup a sync pool and a test model for transaction API tests."""
        pass

    @abstractmethod
    async def setup_async_pool_and_model(self, scenario_name: str) -> Tuple[AsyncBackendPool, Type[AsyncActiveRecord]]:
        """Setup an async pool and a test model for transaction API tests."""
        pass

    @abstractmethod
    def cleanup_sync(self, scenario_name: str, pool: BackendPool) -> None:
        """Cleanup sync resources for the scenario."""
        pass

    @abstractmethod
    async def cleanup_async(self, scenario_name: str, pool: AsyncBackendPool) -> None:
        """Cleanup async resources for the scenario."""
        pass
