# src/rhosocial/activerecord/testsuite/core/scenario.py
"""Scenario metadata model for parallel test execution.

A *scenario* describes one concrete database instance/shape (e.g. an SQLite
file layout, a MySQL server version, a PostgreSQL version with/without
plugin extensions). Scenarios of the same backend are isolated from each
other, so the same test case can safely run for several scenarios in
parallel.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


@dataclass(frozen=True)
class Scenario:
    """
    Metadata describing a single test scenario.

    Attributes:
        name: Unique scenario name (used as parametrization id).
        description: Human readable description of the database shape.
        tags: Optional tags (e.g. "file", "memory", "version:9.7").
        is_poolable: Whether databases of this scenario may be pooled and
            reused across tests. File based databases are poolable;
            in-memory ones are not (they vanish with their connection).
        config_factory: Optional callable returning the backend config for
            this scenario.
    """

    name: str
    description: str = ""
    tags: Tuple[str, ...] = ()
    is_poolable: bool = True
    config_factory: Optional[Callable] = None