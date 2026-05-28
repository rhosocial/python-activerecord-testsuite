"""Provider contracts for backend direct benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Protocol, runtime_checkable


@dataclass
class BackendBenchmarkContext:
    scenario: str
    size: str
    backend: Any
    payloads: List[dict]
    record_ids: List[Any]
    sql: dict
    params_factory: Callable[..., Any]
    backend_namespace: str
    backend_name: str


class UnsupportedBenchmarkScenario(Exception):
    pass


@runtime_checkable
class IBackendBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    def setup_benchmark_sync(self, scenario: str, size: str) -> Optional[BackendBenchmarkContext]: ...

    def teardown_benchmark_sync(self, scenario: str, context: BackendBenchmarkContext) -> None: ...

    async def setup_benchmark_async(self, scenario: str, size: str) -> Optional[BackendBenchmarkContext]: ...

    async def teardown_benchmark_async(self, scenario: str, context: BackendBenchmarkContext) -> None: ...
