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


@pytest.fixture(scope="function")
def benchmark_size(request):
    return request.config.getoption("--benchmark-size")
