# src/rhosocial/activerecord/testsuite/plugin.py
"""The pytest plugin the shared suite installs into every backend.

The plugin is registered through the package's ``pytest11`` entry point, so a
backend only has to install ``rhosocial-activerecord-testsuite`` to get it.

What it does:

* provides the ``environment`` fixture every testsuite fixture depends on;
* before each test it runs the directory's ``prepare`` and afterwards its
  ``teardown`` (the directory conftest owns both);
* once per directory and scenario, before that directory's first test, it
  runs the directory's ``ensure_database``;
* pins a directory's tests per scenario for xdist, so tests that share a
  database never run on two workers;
* applies the ``requires_protocol`` / ``requires_functions`` markers.
"""
from __future__ import annotations

import sys

import pytest

from rhosocial.activerecord.testsuite.core.capabilities import (
    dialect_for,
    scenario_of,
    skip_if_unsupported,
)
from rhosocial.activerecord.testsuite.core.declarations import (
    DeclarationError,
    contract_for_path,
)
from rhosocial.activerecord.testsuite.core.environment import Environment

SCENARIO_FIXTURE_NAME = "backend_scenario"

_RESET_DATABASES = set()

_EXTRA_MARKERS = (
    "requires_protocol: skip when the backend dialect lacks the protocol/switch",
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


def _contract(item):
    return contract_for_path(item.config.pluginmanager, item.path)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Pin each directory's tests to one worker.

    The logical database is owned by the directory, so every test below it --
    including backend-local tests that resolve their own scenario fixture --
    has to land on the same worker.  A per-scenario key would split them when
    scenario resolution differs between items, and two workers resetting the
    directory's database concurrently is exactly the table-vanishes race seen
    under ``--dist=loadgroup``.
    """
    for item in items:
        contract = _contract(item)
        if contract is None:
            continue
        item._testsuite_contract = contract
        item.add_marker(
            pytest.mark.xdist_group(f"testsuite::{contract.directory}")
        )


def pytest_runtest_setup(item):
    """Apply capability markers before any fixture is set up."""
    scenario = scenario_of(item)
    if scenario is None:
        return
    skip_if_unsupported(item, scenario, dialect_for(scenario))


@pytest.fixture(scope="function")
def environment(request, backend_scenario):
    """Prepare one test's directory fixtures and tear them down afterwards."""
    contract = getattr(request.node, "_testsuite_contract", None) or _contract(
        request.node
    )
    if contract is None:
        raise DeclarationError(
            f"No directory contract above {request.node.path}: its conftest must "
            "define prepare(environment) and teardown(environment)"
        )

    env = Environment(backend_scenario, contract.database, contract.directory)
    key = (contract.directory, getattr(backend_scenario, "name", "default"))
    try:
        if key not in _RESET_DATABASES:
            contract.ensure_database(env)
            _RESET_DATABASES.add(key)
        contract.prepare(env)
        yield env
    finally:
        # Drops are idempotent, so clean up even when preparation failed halfway;
        # a teardown error must not mask an error already in flight.
        failed = sys.exc_info()[1] is not None
        try:
            contract.teardown(env)
        except Exception:
            if not failed:
                raise
        finally:
            env.disconnect()
            Environment.active = None
