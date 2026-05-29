"""Provider contracts for FastAPI benchmark scenarios."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Protocol, Type, runtime_checkable

FASTAPI_CONTEXT_STRATEGY = "context"
FASTAPI_POOL_NEAR_MIN_STRATEGY = "pool-near-min"
FASTAPI_POOL_NEAR_MAX_STRATEGY = "pool-near-max"
FASTAPI_POOL_OVER_MAX_STRATEGY = "pool-over-max"
FASTAPI_CONNECTION_STRATEGIES = [
    FASTAPI_CONTEXT_STRATEGY,
    FASTAPI_POOL_NEAR_MIN_STRATEGY,
    FASTAPI_POOL_NEAR_MAX_STRATEGY,
    FASTAPI_POOL_OVER_MAX_STRATEGY,
]
FASTAPI_DEFAULT_CONCURRENCY = 20
FASTAPI_DEFAULT_REPEAT = 3
FASTAPI_RUNTIME_CONFIGS = {
    FASTAPI_CONTEXT_STRATEGY: {
        "concurrency": FASTAPI_DEFAULT_CONCURRENCY,
        "repeat": FASTAPI_DEFAULT_REPEAT,
        "pool_min_size": None,
        "pool_max_size": None,
    },
    FASTAPI_POOL_NEAR_MIN_STRATEGY: {
        "concurrency": 10,
        "repeat": 3,
        "pool_min_size": 10,
        "pool_max_size": 20,
    },
    FASTAPI_POOL_NEAR_MAX_STRATEGY: {
        "concurrency": 18,
        "repeat": 3,
        "pool_min_size": 10,
        "pool_max_size": 20,
    },
    FASTAPI_POOL_OVER_MAX_STRATEGY: {
        "concurrency": 30,
        "repeat": 3,
        "pool_min_size": 10,
        "pool_max_size": 20,
    },
}


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
    concurrency: int = FASTAPI_DEFAULT_CONCURRENCY
    repeat: int = FASTAPI_DEFAULT_REPEAT
    pool_config: Optional[dict] = None
    pool_connection_mode: Optional[str] = None
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
