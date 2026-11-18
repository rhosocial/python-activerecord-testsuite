# src/rhosocial/activerecord/testsuite/pytest_plugin/declarations.py
"""What a scope of the test tree declares about itself.

A scope owns one database per scenario, so its tests are one parallel subset:
everything in it runs serially on one worker, while different scenarios stay
isolated and may run in parallel.  That subset is **declared**, never inferred
-- a scope that says nothing is left alone and may run in unlimited parallel,
which is exactly what a scope of pure expression assertions wants.

The scope is a directory today, and the declaration does not assume that: a
module or a file may declare itself the same way later, so the class is named
for the act, not for the container.

The declaration also carries the scope's text: what it is for, and what a pass
or a failure means.  That text never influences the outcome; it is there so a
failure in CI says what went wrong in the system rather than in the code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .requirements import Entry, Requirement, requirement_list

#: Directories whose name is a category rather than part of a database name.
CATEGORY_DIRECTORIES = ("feature", "benchmark")

#: Prefix every directory-owned database carries.
DATABASE_PREFIX = "test_"

#: Module attribute a ``conftest.py`` uses to declare its scope.
DECLARATION_ATTRIBUTE = "DECLARATION"


@dataclass(frozen=True)
class Declaration:
    """One scope's declaration."""

    parallel: bool = False
    """Declare the scope a parallel subset (one database per scenario).

    ``False`` means "do not group": the scope is free to run in unlimited
    parallel, which is the right answer for scopes that only render and inspect
    expressions.
    """

    uses_database: bool = False
    """Declare that this scope needs a prepared database.

    ``True`` makes the shared L1 gate request the directory's ``schema``
    fixture, which connects the backend and (re)creates its tables. ``False``
    -- the default -- means the scope never opens a connection: pure Python or
    expression-only tests declare nothing and touch no database. A scope that
    declares ``True`` must provide ``database`` and ``schema`` fixtures; the
    gate fails loudly if it does not.
    """

    purpose: str = ""
    passes_means: str = ""
    fails_means: str = ""

    requires: Tuple[Requirement, ...] = field(default_factory=tuple)
    """Dialect answers this scope's fixtures require.

    Evaluated at call time by ``hooks.evaluate``, the first moment the directory
    has opened its fixtures and therefore knows which dialect it is talking to.
    A requirement this scope declares but no dialect answers fails the item: a
    dialect gap is not an "unsupported" answer.
    """

    def __post_init__(self) -> None:
        if not self.requires:
            object.__setattr__(self, "requires", ())
        elif not isinstance(self.requires[0], Requirement):
            object.__setattr__(
                self, "requires", requirement_list(self.requires)
            )


def conftest_map(pluginmanager) -> Dict[str, object]:
    """Map normalised directory path to the ``conftest.py`` module loaded there."""
    mapping = {}
    for plugin in pluginmanager.get_plugins():
        module_file = getattr(plugin, "__file__", None)
        if not module_file:
            continue
        if os.path.basename(str(module_file)) != "conftest.py":
            continue
        directory = os.path.normcase(
            os.path.abspath(os.path.dirname(str(module_file)))
        )
        mapping[directory] = plugin
    return mapping


def declaration_for(pluginmanager, path) -> Optional[Declaration]:
    """The nearest declaration at or above a test file path."""
    if not path:
        return None
    mapping = conftest_map(pluginmanager)
    candidate = os.path.normcase(
        os.path.abspath(os.path.dirname(os.fspath(path)))
    )
    while True:
        module = mapping.get(candidate)
        if module is not None:
            declaration = getattr(module, DECLARATION_ATTRIBUTE, None)
            if isinstance(declaration, Declaration):
                return declaration
        parent = os.path.dirname(candidate)
        if not parent or parent == candidate:
            return None
        candidate = parent


def entries_of(declaration: Optional[Declaration]) -> Tuple[Entry, ...]:
    """The requirements a scope declares, as evaluator input."""
    if declaration is None:
        return ()
    return tuple(declaration.requires)


def database_name(directory) -> str:
    """Derive a logical database name from a test directory path.

    The name starts below ``feature`` / ``benchmark``; when neither appears
    in the path, the last directory name is used.
    """
    parts = list(os.path.normpath(os.path.abspath(os.fspath(directory))).split(os.sep))
    lowered = [part.lower() for part in parts]
    start = 0
    for category in CATEGORY_DIRECTORIES:
        if category in lowered:
            start = len(lowered) - lowered[::-1].index(category)
            break
    else:
        start = len(parts) - 1
    names = [part for part in parts[start:] if part]
    return DATABASE_PREFIX + "_".join(names)



__all__ = [
    "CATEGORY_DIRECTORIES",
    "DATABASE_PREFIX",
    "DECLARATION_ATTRIBUTE",
    "Declaration",
    "conftest_map",
    "database_name",
    "declaration_for",
    "entries_of",
]
