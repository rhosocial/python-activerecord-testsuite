# src/rhosocial/activerecord/testsuite/plugin.py
"""The pytest plugin the shared suite installs into every backend.

The plugin is registered through the package's ``pytest11`` entry point, so a
backend only has to install ``rhosocial-activerecord-testsuite`` to get it.

What it does:

* pins a directory's database-backed tests per scenario for xdist, so tests
  that share a database never run on two workers;
* applies the ``requires_*`` markers and reports what a failure means.

A directory's tables, fixtures and database belong to that directory's
``conftest.py``; this plugin owns neither, and keeps no environment of its own.
"""
from __future__ import annotations


import pytest

from rhosocial.activerecord.testsuite.pytest_plugin import hooks

SCENARIO_FIXTURE_NAME = "backend_scenario"

_EXTRA_MARKERS = (
    "requires_protocol: skip when the backend dialect lacks the protocol or its answer",
    "requires_functions: skip when the dialect reports the functions unsupported",
    "requires_inner_join: skip when the dialect cannot render an inner join",
    "requires_json_operations: skip when the dialect lacks JSON operations",
    "serial: keep this test on a single worker",
)

# The benchmark suite can be run straight from the installed package, without
# the backend's own ``pyproject.toml`` as rootdir; without these registrations
# pytest refuses to collect the benchmark modules.
_BENCHMARK_MARKERS = (
    "benchmark: marks tests as performance benchmarks",
    "benchmark_sync: marks synchronous benchmark tests",
    "benchmark_async: marks asynchronous benchmark tests",
    "benchmark_read: marks read-oriented benchmark tests",
    "benchmark_write: marks write-oriented benchmark tests",
    "benchmark_crud: marks CRUD benchmark tests",
    "benchmark_backend: marks backend direct benchmark tests",
    "benchmark_query: marks query benchmark tests",
    "benchmark_transaction: marks transaction benchmark tests",
    "benchmark_mixin: marks mixin benchmark tests",
    "benchmark_fastapi: marks FastAPI benchmark tests",
    "benchmark_relation: marks relation benchmark tests",
)


def pytest_configure(config):
    for marker in _EXTRA_MARKERS + _BENCHMARK_MARKERS:
        config.addinivalue_line("markers", marker)
    _assert_loadgroup(config)


def _assert_loadgroup(config) -> None:
    """Refuse a parallel run that would split a directory's shared tables."""
    workers = config.getoption("numprocesses", default=None)
    if workers in (None, 0, "0"):
        return
    dist = str(config.getoption("dist", default="no"))
    if dist != "loadgroup":
        raise pytest.UsageError(
            "Testsuite directories share tables per scenario; parallel runs must "
            f"use --dist=loadgroup (got --dist={dist})."
        )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Group a directory's tests onto one worker **only when it declares so**.

    Parallel grouping is declared, never inferred: a directory that declares
    ``Declaration(parallel=True)`` pins its tests (per scenario) to one worker,
    because its tests share one database. A directory that declares nothing is
    left ungrouped and free to run in unlimited parallel -- a ``conftest.py``
    or a ``database`` fixture alone is *not* a declaration of serial intent.
    """
    hooks.collection_modifyitems(config, items)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    """Apply a case's requirement markers against the dialect the test opened.

    This runs at ``call`` rather than ``setup`` because the dialect exists only
    once the directory's own fixtures have prepared the backend.
    """
    hooks.runtest_call(item)


def pytest_runtest_logreport(report):
    """Say what a failure means, where the failure is reported."""
    hooks.logreport(report)