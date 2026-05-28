"""Provider contracts for transaction benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Type, runtime_checkable


@dataclass
class TransactionBenchmarkContext:
    scenario: str
    size: str
    model_class: Type[Any]
    payloads: List[dict]
    record_ids: List[Any]
    backend_namespace: str
    backend_name: str


class UnsupportedBenchmarkScenario(Exception):
    pass


@runtime_checkable
class ITransactionBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    def setup_benchmark_sync(
        self, scenario: str, size: str
    ) -> Optional[TransactionBenchmarkContext]: ...

    def teardown_benchmark_sync(
        self, scenario: str, context: TransactionBenchmarkContext
    ) -> None: ...

    async def setup_benchmark_async(
        self, scenario: str, size: str
    ) -> Optional[TransactionBenchmarkContext]: ...

    async def teardown_benchmark_async(
        self, scenario: str, context: TransactionBenchmarkContext
    ) -> None: ...
