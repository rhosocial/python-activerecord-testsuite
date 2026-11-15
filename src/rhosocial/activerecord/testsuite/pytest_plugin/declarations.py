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

    purpose: str = ""
    passes_means: str = ""
    fails_means: str = ""

    requires: Tuple[Requirement, ...] = field(default_factory=tuple)
    """Dialect answers this scope's fixtures require.

    Evaluated by the environment fixture, which is the first place the concrete
    backend -- and therefore the dialect -- is known.
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


__all__ = [
    "DECLARATION_ATTRIBUTE",
    "Declaration",
    "conftest_map",
    "declaration_for",
    "entries_of",
]
