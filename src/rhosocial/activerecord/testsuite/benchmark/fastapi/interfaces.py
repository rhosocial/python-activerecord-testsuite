"""Provider contracts for FastAPI benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Protocol, Type, runtime_checkable


@dataclass
class FastAPIBenchmarkContext:
    scenario: str
    size: str
    app: Any
    client: Any
    model_class: Type[Any]
    payloads: List[dict]
    record_ids: List[Any]
    backend_namespace: str
    backend_name: str
    connection_strategy: str
    pool_stats: Optional[Callable[[], Any]] = None


class UnsupportedBenchmarkScenario(Exception):
    pass


@runtime_checkable
class IFastAPIBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    def get_connection_strategies(self) -> List[str]: ...

    async def setup_benchmark_async(
        self,
        scenario: str,
        size: str,
        connection_strategy: str = "context",
    ) -> Optional[FastAPIBenchmarkContext]: ...

    async def teardown_benchmark_async(
        self,
        scenario: str,
        context: FastAPIBenchmarkContext,
    ) -> None: ...
