# src/rhosocial/activerecord/testsuite/pytest_plugin/declarations.py
"""What a test directory declares about itself.

A directory owns one database per scenario, so its tests are one parallel
subset: everything in it runs serially on one worker, while different
scenarios stay isolated and may run in parallel.  That subset is **declared**,
never inferred -- a directory that says nothing is left alone and may run in
unlimited parallel, which is exactly what a directory of pure expression
assertions wants.

The declaration also carries the directory's text: what it is for, and what a
pass or a failure means.  That text never influences the outcome; it is there
so a failure in CI says what went wrong in the system rather than in the code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .switches import Entry, Requirement, requirement_list

#: Module attribute a directory's ``conftest.py`` uses to declare itself.
DECLARATION_ATTRIBUTE = "DECLARATION"


@dataclass(frozen=True)
class DirectoryDeclaration:
    """One directory's declaration."""

    parallel: bool = False
    """Declare the directory a parallel subset (one database per scenario).

    ``False`` means "do not group": the directory is free to run in
    unlimited parallel, which is the right answer for directories that only
    render and inspect expressions.
    """

    purpose: str = ""
    passes_means: str = ""
    fails_means: str = ""

    switches: Tuple[Requirement, ...] = field(default_factory=tuple)
    """Switches this directory's fixture definitions require.

    Evaluated by the environment fixture, which is the first place the
    concrete backend -- and therefore the dialect -- is known.
    """

    def __post_init__(self) -> None:
        if not self.switches:
            object.__setattr__(self, "switches", ())
        elif not isinstance(self.switches[0], Requirement):
            object.__setattr__(
                self, "switches", requirement_list(self.switches)
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


def declaration_for(pluginmanager, path) -> Optional[DirectoryDeclaration]:
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
            if isinstance(declaration, DirectoryDeclaration):
                return declaration
        parent = os.path.dirname(candidate)
        if not parent or parent == candidate:
            return None
        candidate = parent


def entries_of(declaration: Optional[DirectoryDeclaration]) -> Tuple[Entry, ...]:
    """The switch entries a directory declares, as evaluator input."""
    if declaration is None:
        return ()
    return tuple(declaration.switches)


__all__ = [
    "DECLARATION_ATTRIBUTE",
    "DirectoryDeclaration",
    "conftest_map",
    "declaration_for",
    "entries_of",
]
