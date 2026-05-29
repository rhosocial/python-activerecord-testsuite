"""Shared pytest fixtures for benchmark scenarios."""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark-size",
        action="store",
        default="small",
        choices=("small", "medium", "large"),
        help="Data size for rhosocial benchmark scenarios.",
    )
    parser.addoption(
        "--fastapi-concurrent-rounds",
        action="store",
        default=5,
        type=int,
        help="Number of benchmark rounds for concurrent FastAPI tests (each round runs the full concurrent workload once).",
    )


@pytest.fixture(scope="function")
def benchmark_size(request):
    return request.config.getoption("--benchmark-size")


@pytest.fixture(scope="function")
def fastapi_concurrent_rounds(request):
    return request.config.getoption("--fastapi-concurrent-rounds")
