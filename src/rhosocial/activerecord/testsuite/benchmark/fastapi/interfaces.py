"""Provider contracts for FastAPI benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Type, runtime_checkable


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


class UnsupportedBenchmarkScenario(Exception):
    pass


@runtime_checkable
class IFastAPIBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    async def setup_benchmark_async(
        self,
        scenario: str,
        size: str,
    ) -> Optional[FastAPIBenchmarkContext]: ...

    async def teardown_benchmark_async(
        self,
        scenario: str,
        context: FastAPIBenchmarkContext,
    ) -> None: ...
