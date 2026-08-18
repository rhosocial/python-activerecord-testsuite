# src/rhosocial/activerecord/testsuite/core/pool.py
"""Database pool for parallel test execution.

A simple preemptive database-slot allocator. Before the session starts the
master prepares ``{base}_0`` .. ``{base}_{N-1}`` databases for every scenario
(creating them if missing and clearing leftover tables), where N is the pool
size (defaults to the number of xdist workers). Each test then takes any free
slot when its fixtures need a database, uses it, and gives it back when the
test finishes. Tests own their schema: they set up and tear down their own
tables, and the pool only guarantees the slot databases were clean at session
start.

Pool semantics:

- **Naming**: ``{database}_{index}`` — the prefix is derived from the
  scenario's configured database name (e.g. MySQL scenarios whose YAML sets
  ``database: test_db`` produce ``test_db_0``, ``test_db_1``, ...). Each
  backend registers its scenarios' base names via :func:`register_base_database`;
  scenarios without a registration fall back to ``test_db``. SQLite appends
  ``.sqlite`` (``test_db_3.sqlite``); server backends use the bare
  ``test_db_3`` database/schema name. The scenario name is deliberately NOT
  part of the database name; the scenario selects the server (host/port) while
  the index selects the database on that server.
- **Preparation**: :func:`prepare_pool` runs once per test session on the
  master, before any test is dispatched. It invokes the backend's registered
  preparation handler for every slot of every scenario; handlers ensure the
  database exists and drop leftover tables.
- **Allocation**: a test acquires a slot per scenario the first time it needs
  the database name, taking the first slot whose per-slot file lock is free
  (preemptive allocation). The slot is held for the rest of the test and
  released by :func:`release_all`. Per-slot file locks coordinate across xdist
  worker processes; the OS releases a lock automatically if a worker crashes.
  Because the pool size equals the number of workers, a free slot is always
  available, so allocation does not spin.
- **Lifecycle**: ``{database}_*`` databases are not removed after the session;
  they persist and are prepared (cleared) again at the start of the next
  session.
- Pooling is only active when running under xdist workers with a positive
  pool size. Serial runs (no ``-n``) keep the previous unique-file/unique-
  database behaviour.
"""
import os
import re
import tempfile
import threading
import time
from typing import Callable, Dict, Iterable, List, Optional

_POOL_SIZE = 0
_RESET_HANDLER: Optional[Callable[[str, str], None]] = None
_CLEAR_ON_ACQUIRE = True
_POOL_DIR: Optional[str] = None

_DEFAULT_BASE_DATABASE = "test_db"
_BASE_DATABASES: Dict[str, str] = {}

_WORKER_RE = re.compile(r"^gw(\d+)$")

# Slots held by the current worker for the currently executing test.
_HELD: Dict[str, int] = {}
_OPEN_LOCKS: Dict[tuple, object] = {}
_GUARD = threading.Lock()


def register_base_database(scenario: str, base_database: str) -> None:
    """Register the base database name used for a scenario's pooled databases.

    The pooled database name for a scenario is ``{base_database}_{index}``
    (e.g. ``test_db_3``). Backends register each scenario's configured database
    name (e.g. from the YAML ``database`` field) so the pool name derivation
    follows the scenario configuration instead of a hardcoded prefix.
    """
    _BASE_DATABASES[scenario] = base_database


def base_database(scenario: str) -> str:
    """Return the registered base database name for a scenario.

    Falls back to ``test_db`` when the scenario has no registered base name.
    """
    return _BASE_DATABASES.get(scenario, _DEFAULT_BASE_DATABASE)


def configure_pool_dir(path: Optional[str]) -> None:
    """Set the directory where pooled ``test_db_*`` files are created.

    Falls back to the default temp directory when ``None``.
    """
    global _POOL_DIR
    _POOL_DIR = path or None


def pool_dir() -> str:
    """Return the directory where pooled ``test_db_*`` files are created."""
    return _POOL_DIR or os.path.join(tempfile.gettempdir(), "rhosocial-test-db")


def configure_pool_size(size: int) -> None:
    """Set the configured pool size (0 disables pooling).

    The pool size is the number of slot databases prepared per scenario. It
    defaults to the number of xdist workers so a free slot is always available.
    """
    global _POOL_SIZE
    _POOL_SIZE = max(0, int(size))


def pool_size() -> int:
    """Return the configured pool size (0 means pooling disabled)."""
    return _POOL_SIZE


def is_xdist_worker() -> bool:
    """Return True when running inside a pytest-xdist worker process."""
    return bool(os.environ.get("PYTEST_XDIST_WORKER"))


def worker_index() -> int:
    """Return the index of the current xdist worker (``gw0`` -> 0, default 0)."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
    match = _WORKER_RE.match(worker_id)
    if match:
        return int(match.group(1))
    return 0


def pooling_active() -> bool:
    """Return True when the database pool should be used for the current test.

    Pooling requires running under xdist workers with a positive pool size.
    Serial runs keep the previous per-test unique-database behaviour.
    """
    return _POOL_SIZE > 0 and is_xdist_worker()


def register_pool_reset_handler(
    handler: Optional[Callable[[str, str], None]], *, clear_on_acquire: bool = True
) -> None:
    """Register a backend-specific slot-preparation callback.

    The callback receives ``(scenario, database_name)`` where ``database_name``
    is the bare pooled name (e.g. ``test_db_3``) of a slot to prepare. It must
    ensure that slot's database exists and is clear of leftover tables.

    ``clear_on_acquire`` controls whether the handler is invoked every time a
    slot is handed to a test. Backends whose tests are fully self-contained
    (they create and drop their own tables) can set it to ``False`` and rely on
    the single session-start preparation, avoiding a DROP-all-tables pass per
    test. File-based backends whose schema setup is order-sensitive (SQLite
    drops a parent table before its dependents, which foreign_keys=ON rejects)
    keep ``True`` so every test still starts from a pristine schema.
    """
    global _RESET_HANDLER, _CLEAR_ON_ACQUIRE
    _RESET_HANDLER = handler
    _CLEAR_ON_ACQUIRE = bool(clear_on_acquire)


def slot_name(index: int, base: str) -> str:
    """Return the bare pooled database name (e.g. ``test_db_3``)."""
    return f"{base}_{index}"


def prepare_pool(scenarios: Optional[Iterable[str]] = None) -> None:
    """Create and clear the pooled databases of every scenario (once per run).

    Runs on the master before any test is dispatched. Every slot database of
    every (enabled) scenario is brought to a clean, empty state so tests start
    from a pristine schema regardless of leftovers from previous sessions.
    """
    if _POOL_SIZE <= 0 or _RESET_HANDLER is None:
        return
    scenario_names = list(scenarios) if scenarios is not None else list(_BASE_DATABASES)
    for scenario in scenario_names:
        base = base_database(scenario)
        for index in range(_POOL_SIZE):
            try:
                _RESET_HANDLER(scenario, slot_name(index, base))
            except Exception:
                pass


def _lock_dir() -> str:
    """Return the directory holding per-slot lock files (shared across workers)."""
    return os.path.join(pool_dir(), "pool-locks")


def _acquire_slot(scenario: str) -> int:
    """Acquire the first free slot index for a scenario (preemptive allocation).

    Takes the per-slot file lock of the first free slot; the lock is released
    when the test finishes (or automatically if the worker crashes). The slot
    database is cleared right after acquisition (the pool manager only hands
    out clean databases), so a test always starts from a pristine schema even
    though the slot file was reused by a previous test. When every slot is
    briefly busy (pool size smaller than the worker count), the caller waits on
    a slot lock instead of spinning.
    """
    import fcntl

    lock_dir = _lock_dir()
    os.makedirs(lock_dir, exist_ok=True)
    base = base_database(scenario)
    lock_base = base.replace(os.sep, "_")
    size = max(_POOL_SIZE, 1)
    while True:
        for index in range(size):
            path = os.path.join(lock_dir, f"{scenario}-{lock_base}-{index}.lock")
            fh = open(path, "a+")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                fh.close()
                continue
            with _GUARD:
                _OPEN_LOCKS[(scenario, index)] = fh
            if _RESET_HANDLER is not None and _CLEAR_ON_ACQUIRE:
                try:
                    _RESET_HANDLER(scenario, slot_name(index, base))
                except Exception:
                    pass
            return index
        # All slots busy: block on the first slot until it is released.
        path = os.path.join(lock_dir, f"{scenario}-{lock_base}-0.lock")
        fh = open(path, "a+")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()


def _slot_for(scenario: str) -> int:
    """Return the worker's held slot index for a scenario, acquiring it on demand.

    The slot is acquired lazily on the first database access of the current
    test and held until :func:`release_all`; repeated lookups within the same
    test return the same slot.
    """
    with _GUARD:
        index = _HELD.get(scenario)
        if index is not None:
            return index
    index = _acquire_slot(scenario)
    with _GUARD:
        _HELD[scenario] = index
    return index


def pooled_database_name(scenario: str) -> Optional[str]:
    """
    Return the pooled database name (e.g. ``test_db_3``) for the scenario's
    currently held slot, or ``None`` when pooling is inactive (callers then
    fall back to the scenario's configured database).
    """
    if not pooling_active():
        return None
    return slot_name(_slot_for(scenario), base_database(scenario))


def pooled_database_path(scenario: str, suffix: str = ".sqlite") -> Optional[str]:
    """
    Return the pooled database on-disk path for the scenario's held slot, or
    ``None`` when pooling is inactive. File-based backends (e.g. SQLite) use
    this to obtain the file path.
    """
    if not pooling_active():
        return None
    name = slot_name(_slot_for(scenario), base_database(scenario))
    path = os.path.join(pool_dir(), name + suffix)
    os.makedirs(pool_dir(), exist_ok=True)
    return path


def release_all() -> None:
    """Release every pool slot held by the current worker.

    Called when a test finishes so the freed slots are immediately available to
    the next test on any worker.
    """
    import fcntl

    with _GUARD:
        held = list(_HELD.items())
        _HELD.clear()
        for scenario, index in held:
            fh = _OPEN_LOCKS.pop((scenario, index), None)
            if fh is None:
                continue
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
            except Exception:
                pass
            fh.close()


def reset_pool() -> None:
    """Release all held slots (used at session end / between sessions)."""
    release_all()