# src/rhosocial/activerecord/testsuite/feature/cli/interfaces.py
"""Provider interfaces for the CLI feature tests."""

from abc import ABC, abstractmethod
from typing import Any, List


class CLIProviderBase(ABC):
    """Shared scenario discovery for CLI providers."""

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """Return scenario names supported by this backend."""
        pass


class ICLISyncProvider(CLIProviderBase):
    """Provider contract for synchronous CLI tests."""

    @abstractmethod
    def setup_cli_models(self, scenario_name: str) -> Any:
        """Configure and return the CLI model bundle for one scenario."""
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """Drop tables and disconnect after a CLI test."""
        pass


class ICLIAsyncProvider(CLIProviderBase):
    """Provider contract for asynchronous CLI tests."""

    @abstractmethod
    async def setup_cli_models(self, scenario_name: str) -> Any:
        """Configure and return the async CLI model bundle for one scenario."""
        pass

    @abstractmethod
    async def cleanup_after_test(self, scenario_name: str):
        """Drop tables and disconnect after an async CLI test."""
        pass
