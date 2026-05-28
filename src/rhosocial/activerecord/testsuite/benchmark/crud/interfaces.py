"""Provider contracts for CRUD benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Type, runtime_checkable


@dataclass
class CrudBenchmarkContext:
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
class ICrudBenchmarkProvider(Protocol):
    def get_benchmark_scenarios(self) -> List[str]: ...

    def setup_benchmark_sync(self, scenario: str, size: str) -> Optional[CrudBenchmarkContext]: ...

    def teardown_benchmark_sync(self, scenario: str, context: CrudBenchmarkContext) -> None: ...

    async def setup_benchmark_async(self, scenario: str, size: str) -> Optional[CrudBenchmarkContext]: ...

    async def teardown_benchmark_async(self, scenario: str, context: CrudBenchmarkContext) -> None: ...
