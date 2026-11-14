# src/rhosocial/activerecord/testsuite/benchmark/registry.py
"""Benchmark implementations a backend can provide.

A benchmark test needs a backend-specific context: configured models, seeded
data and a way to tear them down.  A backend registers one implementation per
benchmark feature; features without an implementation skip.  The registry
lives with the benchmark suite, not with the fixture machinery.
"""
from typing import Any, Dict, List


class BenchmarkImplementation:
    """One backend's benchmark setup for a feature."""

    def scenarios(self) -> List[str]:
        return []

    def connection_strategies(self) -> List[str]:
        return ["context"]

    def sync_setup(self, scenario: str, size: str) -> Any:
        return None

    def sync_teardown(self, scenario: str, context: Any) -> None:
        return None

    async def async_setup(self, scenario: str, size: str, strategy: str = "context") -> Any:
        return None

    async def async_teardown(self, scenario: str, context: Any) -> None:
        return None


class BenchmarkRegistry:
    """Feature name to implementation."""

    def __init__(self) -> None:
        self._implementations: Dict[str, BenchmarkImplementation] = {}

    def register(self, feature: str, implementation: BenchmarkImplementation) -> None:
        self._implementations[feature] = implementation

    def get(self, feature: str):
        return self._implementations.get(feature)


benchmarks = BenchmarkRegistry()

__all__ = ["BenchmarkImplementation", "BenchmarkRegistry", "benchmarks"]
