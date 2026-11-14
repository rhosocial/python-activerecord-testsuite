# src/rhosocial/activerecord/testsuite/core/declarations.py
"""Directory contracts read from the conftest modules pytest has loaded.

A directory becomes a minimal test set when its ``conftest.py`` defines
``prepare(environment)`` and ``teardown(environment)``.  Its logical database
name is derived from the directory path, so no conftest has to write it down:

    tests/.../feature/basic/crud  ->  test_basic_crud

The category directories ``feature`` and ``benchmark`` are not part of the
name; derivation starts one level below them.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

CATEGORY_DIRECTORIES = ("feature", "benchmark")

DATABASE_PREFIX = "test_"

PREPARE_NAME = "prepare"
TEARDOWN_NAME = "teardown"
ENSURE_DATABASE_NAME = "ensure_database"


class DeclarationError(RuntimeError):
    """A directory that runs tests declares no usable contract."""


@dataclass(frozen=True)
class DirectoryContract:
    """The minimal test set a directory's conftest declares."""

    directory: str
    database: str
    module: object

    def ensure_database(self, environment) -> None:
        hook = getattr(self.module, ENSURE_DATABASE_NAME, None)
        if callable(hook):
            hook(environment)

    def prepare(self, environment) -> None:
        self.module.prepare(environment)

    def teardown(self, environment) -> None:
        self.module.teardown(environment)


def conftest_modules(pluginmanager) -> List[object]:
    """Return every ``conftest.py`` module pytest has loaded."""
    modules = []
    for plugin in pluginmanager.get_plugins():
        module_file = getattr(plugin, "__file__", None)
        if not module_file:
            continue
        if os.path.basename(str(module_file)) != "conftest.py":
            continue
        modules.append(plugin)
    return modules


def conftest_map(pluginmanager) -> dict:
    """Map normalized directory path to its conftest module."""
    mapping = {}
    for module in conftest_modules(pluginmanager):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        directory = os.path.normcase(
            os.path.abspath(os.path.dirname(str(module_file)))
        )
        mapping[directory] = module
    return mapping


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


def contract_for_path(pluginmanager, path) -> Optional[DirectoryContract]:
    """Return the nearest declared contract at or above a test file path."""
    if not path:
        return None
    directory = os.path.normcase(
        os.path.abspath(os.path.dirname(os.fspath(path)))
    )
    mapping = conftest_map(pluginmanager)
    candidate = directory
    while True:
        module = mapping.get(candidate)
        if module is not None and _declares_contract(module):
            return DirectoryContract(
                directory=candidate,
                database=database_name(candidate),
                module=module,
            )
        parent = os.path.dirname(candidate)
        if not parent or parent == candidate:
            return None
        candidate = parent


def _declares_contract(module) -> bool:
    return callable(getattr(module, PREPARE_NAME, None)) and callable(
        getattr(module, TEARDOWN_NAME, None)
    )
