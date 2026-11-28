# src/rhosocial/activerecord/testsuite/feature/rules/backend/support.py
"""Helpers a backend uses to describe its own namespace.

A backend declares a ``subject``; building that subject needs one lookup -- where
its ``impl/<name>`` directory is -- and this module answers it without importing
the backend's behaviour.

Nothing here names a backend: the caller passes its own expression package and
the path is derived from that, so adding a backend never touches this file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def module_search_paths(module: object) -> Iterable[Path]:
    """The directories a module or package was loaded from.

    ``__path__`` covers a package; ``__file__`` covers a single module, which is
    how a backend that keeps its whole vocabulary in one file exposes it. Both
    are yielded so the caller never has to know which shape it was handed.
    """
    for candidate in vars(module).get("__path__", ()):
        yield Path(candidate).resolve()
    source = vars(module).get("__file__")
    if source:
        yield Path(source).resolve()


def impl_root_of(expression_package: object) -> Path:
    """``backend/impl/<name>`` for the backend that owns *expression_package*.

    The expression namespace is the anchor because it is the one directory a
    backend is required to have: walking up from it to the ``impl`` directory
    gives the backend's own root without a name being spelled anywhere.
    """
    for base in module_search_paths(expression_package):
        for candidate in [base] + list(base.parents):
            if candidate.name == "impl" and candidate.parent.name == "backend":
                return candidate / base.relative_to(candidate).parts[0]
    raise AssertionError(
        f"{vars(expression_package).get('__name__', expression_package)!r} does not "
        "live under backend/impl"
    )
