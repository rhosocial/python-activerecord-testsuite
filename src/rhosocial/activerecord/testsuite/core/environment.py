# src/rhosocial/activerecord/testsuite/core/environment.py
"""The environment one test runs in.

The backend owns the scenario: how it is loaded, where it lives, how it is
created or cleared.  The testsuite only knows the logical database name, which
it derives from the test directory.

A directory keeps one connection per scenario (and one per sync/async mode) for
its whole run, the same way a long-lived session does: preparing tables and
binding models must not reconnect for every test.  ``prepare`` / ``teardown``
still run per test; only the connections are shared.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType

DDL_OPTIONS = ExecutionOptions(stmt_type=StatementType.DDL)


class _Session:
    """One connection for a (scenario, database, sync|async) triple."""

    def __init__(self, scenario, database: str, async_: bool) -> None:
        self.scenario = scenario
        self.database = database
        self.async_ = async_
        self.backend = None

    @property
    def backend_class(self):
        return self.scenario.async_backend_class if self.async_ else self.scenario.backend_class

    def acquire(self):
        if self.backend is None:
            backend = self.backend_class(
                connection_config=self.scenario.make_config(self.database)
            )
            backend.connect()
            backend.introspect_and_adapt()
            self.backend = backend
        return self.backend

    async def acquire_async(self):
        if self.backend is None:
            backend = self.backend_class(
                connection_config=self.scenario.make_config(self.database)
            )
            await backend.connect()
            await backend.introspect_and_adapt()
            self.backend = backend
        return self.backend

    def close(self) -> None:
        if self.backend is not None:
            try:
                self.backend.disconnect()
            except Exception:  # noqa: BLE001 - session teardown must not fail
                pass
            self.backend = None


_SESSIONS: Dict[Tuple[str, str, bool], _Session] = {}


def _session(scenario, database: str, async_: bool) -> _Session:
    key = (getattr(scenario, "name", None), database, async_)
    session = _SESSIONS.get(key)
    if session is None:
        session = _Session(scenario, database, async_)
        _SESSIONS[key] = session
    return session


def close_all() -> None:
    """Close every shared session connection at the end of a pytest session."""
    for session in _SESSIONS.values():
        session.close()
    _SESSIONS.clear()


class Environment:
    """One test's database, scenario and shared connections."""

    active: Optional["Environment"] = None

    def __init__(self, scenario, database: str, directory: str) -> None:
        self.scenario = scenario
        self.database = database
        self.directory = directory
        Environment.active = self

    # --- database ---------------------------------------------------------

    def make_config(self):
        """Return the connection configuration for this database and scenario."""
        return self.scenario.make_config(self.database)

    def reset_database(self) -> None:
        """Create the database when missing, clear it when present."""
        self.scenario.reset_database(self.database)

    # --- DDL connection ---------------------------------------------------

    @property
    def backend(self):
        """The sync backend used for table preparation and teardown."""
        return _session(self.scenario, self.database, False).acquire()

    @property
    def dialect(self):
        return self.backend.dialect

    def execute(self, expression) -> None:
        """Execute one DDL expression (or a raw SQL string)."""
        if isinstance(expression, str):
            self.backend.execute(expression, (), options=DDL_OPTIONS)
            return
        self.backend.execute(*expression.to_sql(), options=DDL_OPTIONS)

    # --- models -----------------------------------------------------------

    @staticmethod
    def _bind(model, config, backend_class, backend) -> None:
        model.__connection_config__ = config
        model.__backend_class__ = backend_class
        model.__backend__ = backend
        if getattr(model, "_dummy_backend", None) is not None:
            model._dummy_backend = None

    def configure(self, model):
        """Bind a sync model to this directory's shared connection."""
        backend = _session(self.scenario, self.database, False).acquire()
        self._bind(
            model,
            self.scenario.make_config(self.database),
            self.scenario.backend_class,
            backend,
        )
        return model

    async def configure_async(self, model):
        """Configure an async model against this database and return it.

        Async connections belong to the event loop they were opened in, and
        pytest gives every test its own loop, so these cannot be shared the
        way sync connections are.
        """
        await model.configure(self.make_config(), self.scenario.async_backend_class)
        return model

    # --- lifecycle --------------------------------------------------------

    def disconnect(self) -> None:
        """Nothing to do: connections are shared for the whole session."""
        return

    @classmethod
    def current(cls) -> "Environment":
        if cls.active is None:
            raise RuntimeError("No testsuite environment is active")
        return cls.active


def configure(model) -> Any:
    """Configure a sync model in the active environment."""
    return Environment.current().configure(model)


async def configure_async(model) -> Any:
    """Configure an async model in the active environment."""
    return await Environment.current().configure_async(model)
