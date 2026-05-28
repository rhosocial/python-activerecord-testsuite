"""Provider contracts for query benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Type, runtime_checkable


@dataclass
class QueryBenchmarkContext:
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
class IQueryBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    def setup_benchmark_sync(
        self, scenario: str, size: str
    ) -> Optional[QueryBenchmarkContext]: ...

    def teardown_benchmark_sync(
        self, scenario: str, context: QueryBenchmarkContext
    ) -> None: ...

    async def setup_benchmark_async(
        self, scenario: str, size: str
    ) -> Optional[QueryBenchmarkContext]: ...

    async def teardown_benchmark_async(
        self, scenario: str, context: QueryBenchmarkContext
    ) -> None: ...
