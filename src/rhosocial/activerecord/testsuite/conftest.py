# src/rhosocial/activerecord/testsuite/conftest.py
"""
This file serves as the root pytest configuration for the entire testsuite package.
Its purpose is to define global configurations and hooks for pytest, such as
registering custom markers that can be used to categorize and filter tests.
"""
import os
import sys
import pytest
import warnings

# Set the environment variable that the testsuite uses to locate the provider registry.
# The testsuite is a generic package and doesn't know the specific location of the
# provider implementations for this backend (SQLite). This environment variable
# acts as a bridge, pointing the testsuite to the correct import path.
#
# `setdefault` is used to ensure that this value is set only if it hasn't been
# set already, allowing for overrides in different environments if needed.
os.environ.setdefault(
    'TESTSUITE_PROVIDER_REGISTRY',
    'providers.registry:provider_registry'
)

# Early-parse --scenarios from sys.argv and set TESTSUITE_ACTIVE_SCENARIOS env
# var. This must happen before provider scenario modules are imported (they
# filter their SCENARIO_MAP at import time).
_argv_scenarios = None
for _i, _arg in enumerate(sys.argv):
    if _arg.startswith("--scenarios="):
        _argv_scenarios = _arg.split("=", 1)[1]
    elif _arg == "--scenarios" and _i + 1 < len(sys.argv):
        _argv_scenarios = sys.argv[_i + 1]

if _argv_scenarios:
    os.environ["TESTSUITE_ACTIVE_SCENARIOS"] = _argv_scenarios


# Guard against registering the same options twice when the conftest is loaded
# both as a plugin (e.g. ``-p rhosocial.activerecord.testsuite.conftest`` in the
# core CI) and as a path-based conftest for testsuite-path tests.
_pytest_options_registered = False


def pytest_addoption(parser):
    """Register the generic --scenarios option used by all backends."""
    global _pytest_options_registered
    if _pytest_options_registered:
        return
    _pytest_options_registered = True

    parser.addoption(
        "--scenarios",
        action="store",
        default=None,
        help="Comma-separated list of scenario names to run "
             "(e.g., --scenarios=firebird_5,mysql_80). Backend scenario "
             "modules filter their registered scenarios accordingly.",
    )
    parser.addoption(
        "--scenarios-parallel",
        action="store_true",
        default=True,
        help="Allow scenario variants of the same test to run in parallel "
             "(default: True). With --scenarios-parallel, scenario variants "
             "are freely distributed across xdist workers; without it, they "
             "are pinned to the same worker and run sequentially.",
    )
    parser.addoption(
        "--db-pool-size",
        action="store",
        type=int,
        default=None,
        help="Number of pooled test_db_* databases prepared per scenario "
             "(default: follow the number of workers, i.e. -n, minimum 1). "
             "Use 0 to disable pooling and keep per-test unique databases.",
    )
    parser.addoption(
        "--serial-group",
        action="store",
        default="serial",
        help="xdist_group name that serial tests are pinned to (default: serial).",
    )


def pytest_configure(config):
    """
    A pytest hook that runs at the beginning of a test session to configure
    the test environment.
    """
    scenarios_opt = config.getoption("--scenarios", default=None)
    if scenarios_opt:
        os.environ["TESTSUITE_ACTIVE_SCENARIOS"] = scenarios_opt

    # Register custom markers to allow for selective test runs.
    # For example, `pytest -m feature` will run only the core feature tests.
    config.addinivalue_line("markers", "requires_protocol: Mark tests that require specific database protocol support")
    config.addinivalue_line("markers", "requires_functions: Mark tests that require specific database functions")
    config.addinivalue_line("markers", "benchmark: Mark tests as performance benchmarks")
    config.addinivalue_line("markers", "benchmark_sync: Mark synchronous benchmark tests")
    config.addinivalue_line("markers", "benchmark_async: Mark asynchronous benchmark tests")
    config.addinivalue_line("markers", "benchmark_read: Mark read-oriented benchmark tests")
    config.addinivalue_line("markers", "benchmark_write: Mark write-oriented benchmark tests")
    config.addinivalue_line("markers", "benchmark_crud: Mark CRUD benchmark tests")
    config.addinivalue_line("markers", "benchmark_backend: Mark backend-owned direct benchmark tests")
    config.addinivalue_line("markers", "benchmark_query: Mark query benchmark tests")
    config.addinivalue_line("markers", "benchmark_transaction: Mark transaction benchmark tests")
    config.addinivalue_line("markers", "benchmark_mixin: Mark mixin benchmark tests")
    config.addinivalue_line("markers", "benchmark_fastapi: Mark FastAPI benchmark tests")
    config.addinivalue_line(
        "markers", "serial: Mark tests that must run serially (never concurrently with other tests)"
    )

    from rhosocial.activerecord.testsuite.core.pool import configure_pool_size

    configure_pool_size(_resolve_pool_size(config))

    # Preload the provider registry. Importing the registry module pulls in
    # the backend's provider modules, whose side effect is registering the
    # backend-specific pool reset handler (e.g. SQLite's drop-all-tables).
    # This must happen here, in every xdist worker, so that the per-test
    # setup hook can reset pooled databases before the first test runs.
    try:
        from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

        get_provider_registry()
    except Exception:
        pass

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """
    Pin serial tests to a single xdist worker so they never run concurrently.

    Tests marked ``serial`` (e.g. WorkerPool tests that spawn their own
    sub-processes) must not overlap with each other: they share a dedicated
    database and a concurrent run would race on schema setup. They are pinned
    to one worker via the ``xdist_group`` marker, which only takes effect with
    ``--dist=loadgroup`` (pytest-xdist appends the group name to the nodeid).

    Note: pytest-xdist runs this hook in *every* worker, where ``-n`` is not
    present on the command line. xdist is therefore detected through the
    ``PYTEST_XDIST_WORKER`` environment variable so the markers are applied in
    workers too. ``tryfirst=True`` makes the markers visible to xdist's own
    nodeid-rewriting step.

    During collection time, backend-specific capabilities aren't available
    through the provider interface since providers set up backends per test
    scenario. Protocol and function checking happens during test execution when
    provider-configured models are available.
    """
    # Apply serial / parallel scheduling only when running under xdist with
    # more than one worker (otherwise everything is naturally serial).
    import os

    n_workers = config.getoption("-n", default=None)
    if n_workers is None:
        n_workers = config.getoption("--numprocesses", default=None)
    if isinstance(n_workers, str):
        n_workers = n_workers.strip("auto")
    try:
        workers = int(n_workers)
    except (TypeError, ValueError):
        workers = 0

    if workers <= 1 and os.environ.get("PYTEST_XDIST_WORKER") is None:
        return

    serial_group = config.getoption("--serial-group", default="serial")
    scenarios_parallel = config.getoption("--scenarios-parallel", default=True)
    known_scenarios = _known_scenario_names()

    for item in items:
        is_serial = item.get_closest_marker("serial") is not None
        if not is_serial:
            # Cross-scenario tests use 2+ distinct scenario values at once and
            # cannot be parallelized: pin them to the serial group.
            scenario_params = _scenario_params_of(item, known_scenarios)
            if len(scenario_params) > 1:
                is_serial = True
        if is_serial:
            item.add_marker(pytest.mark.xdist_group(serial_group))
            print(f"[AR_DBG] serial-pinned: {item.nodeid} -> group={serial_group}", flush=True)
        elif not scenarios_parallel:
            # Pin scenario variants of the same test to a single worker.
            base_nodeid = item.nodeid.split("[", 1)[0]
            item.add_marker(pytest.mark.xdist_group(f"scenario::{base_nodeid}"))


def _resolve_pool_size(config):
    """Resolve the database pool size.

    Defaults to the number of xdist workers (``-n``, minimum 1) so that every
    worker owns a dedicated ``test_db_*`` slot. An explicit ``--db-pool-size``
    overrides it; 0 disables pooling.

    Workers don't see the master's ``-n`` option, so the master publishes the
    resolved size through ``RHS_AR_POOL_SIZE`` (inherited by worker processes)
    and workers reuse it.
    """
    explicit = config.getoption("--db-pool-size", default=None)
    env_size = os.environ.get("RHS_AR_POOL_SIZE")
    if explicit is not None:
        size = explicit
    elif env_size:
        size = int(env_size)
    else:
        size = _resolve_worker_count(config)
    if os.environ.get("PYTEST_XDIST_WORKER") is None:
        os.environ["RHS_AR_POOL_SIZE"] = str(size)
    return size


def _resolve_worker_count(config):
    """Return the number of xdist workers from the ``-n`` option (default 1)."""
    workers = 1
    try:
        n_workers = config.getoption("-n", default=None)
    except (ValueError, TypeError):
        n_workers = None
    if n_workers is not None:
        value = str(n_workers).strip().lower()
        if value == "auto":
            workers = os.cpu_count() or 1
        else:
            try:
                workers = int(value)
            except ValueError:
                workers = 1
    return max(workers, 1)


_KNOWN_SCENARIOS = None


def _known_scenario_names():
    """Collect all scenario names advertised by the registered providers."""
    global _KNOWN_SCENARIOS
    if _KNOWN_SCENARIOS is not None:
        return _KNOWN_SCENARIOS
    try:
        from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

        registry = get_provider_registry()
    except Exception:
        _KNOWN_SCENARIOS = set()
        return _KNOWN_SCENARIOS
    names = set()
    for provider_class in registry.all_providers():
        try:
            names.update(provider_class().get_test_scenarios())
        except Exception:
            continue
    _KNOWN_SCENARIOS = names
    return names


def _scenario_params_of(item, known_scenarios):
    """Return the set of scenario names used by an item's parametrization."""
    if not known_scenarios:
        return set()
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return set()
    values = set()
    for value in callspec.params.values():
        if isinstance(value, str) and value in known_scenarios:
            values.add(value)
    return values

def pytest_sessionstart(session):
    """
    Hook to generate capability support warnings at session start.

    This hook generates warnings about important unsupported capabilities
    to alert developers about backend limitations. It also prepares this
    worker's pooled databases (ensures they exist) before any test connects.
    """
    try:
        from rhosocial.activerecord.testsuite.core.pool import is_xdist_worker, prepare_pool

        if not is_xdist_worker():
            prepare_pool()
    except Exception as e:
        warnings.warn(f"Could not prepare the database pool at session start: {e}", UserWarning)

    try:
        from rhosocial.activerecord.backend.dialect.protocols import (
            WindowFunctionSupport,
            AdvancedGroupingSupport,
            CTESupport,
            ReturningSupport,
        )

        from rhosocial.activerecord.testsuite.utils import get_current_backend
        backend = get_current_backend()

        if backend is None:
            return

        dialect = backend.dialect
        unsupported_important_capabilities = []

        if not isinstance(dialect, WindowFunctionSupport) or not dialect.supports_window_functions():
            unsupported_important_capabilities.append("Window Functions")

        if not isinstance(dialect, AdvancedGroupingSupport):
            if not (hasattr(dialect, 'supports_cube') and dialect.supports_cube()):
                unsupported_important_capabilities.append("CUBE Grouping")
            if not (hasattr(dialect, 'supports_rollup') and dialect.supports_rollup()):
                unsupported_important_capabilities.append("ROLLUP Grouping")
        else:
            if hasattr(dialect, 'supports_cube') and not dialect.supports_cube():
                unsupported_important_capabilities.append("CUBE Grouping")
            if hasattr(dialect, 'supports_rollup') and not dialect.supports_rollup():
                unsupported_important_capabilities.append("ROLLUP Grouping")

        if not isinstance(dialect, CTESupport) or not dialect.supports_basic_cte():
            unsupported_important_capabilities.append("Common Table Expressions")

        if not isinstance(dialect, ReturningSupport) or not dialect.supports_returning_clause():
            unsupported_important_capabilities.append("RETURNING Clause")

        if unsupported_important_capabilities:
            warnings.warn(
                f"Current backend does not support important capabilities: "
                f"{', '.join(unsupported_important_capabilities)}. "
                f"Some tests will be automatically skipped.",
                UserWarning
            )
    except Exception as e:
        warnings.warn(f"Could not check capability support at session start: {e}", UserWarning)


def pytest_sessionfinish(session, exitstatus):
    """Reset the database pool state.

    ``test_db_*`` databases are intentionally NOT removed after the session;
    they persist across sessions and are re-prepared on the next session.
    """
    from rhosocial.activerecord.testsuite.core.pool import reset_pool

    reset_pool()


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    """Release every pool slot acquired during the just-finished test.

    Fixtures have already been torn down, so backends are disconnected before
    their slots are freed; the next test on any worker can take them.
    """
    from rhosocial.activerecord.testsuite.core.pool import release_all

    release_all()