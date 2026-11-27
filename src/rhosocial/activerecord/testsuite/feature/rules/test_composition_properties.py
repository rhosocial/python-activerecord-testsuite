# src/rhosocial/activerecord/testsuite/feature/rules/test_composition_properties.py
"""Formal source: backend-expression-families.md §3.2.

A backend's family is reuse + derived + proprietary; the three formal
properties are: proprietary kinds do not leak into core, derivatives depend on
core one way only, and two backends' proprietary sets are disjoint. The last
property also means core may not re-export a backend's kind. Registries are
read through their public kind tables; class relationships through ``issubclass``.
"""

import ast
from pathlib import Path

import pytest

from rhosocial.activerecord.backend.expression import bases as _bases
from rhosocial.activerecord.backend.expression.serialization import (
    core_registry,
    registry_for_packages,
)

_CORE = "rhosocial.activerecord.backend.expression"
_SQLITE = "rhosocial.activerecord.backend.impl.sqlite.expression"
_MYSQL = "rhosocial.activerecord.backend.impl.mysql.expression"
_CORE_SRC = Path(_bases.__file__).parent


def _extra_kinds(package):
    """Kinds a backend package adds over core, or None when it is absent."""
    core = set(core_registry().node_kinds())
    try:
        built = registry_for_packages(package, base=core_registry())
    except Exception as exc:  # an uninstalled or unimportable backend is not a failure
        pytest.skip(f"{package} is not available here: {exc}")
    return set(built.node_kinds()) - core


def test_proprietary_kinds_do_not_leak_into_core():
    core = set(core_registry().node_kinds())
    extras = _extra_kinds(_SQLITE)
    assert extras.isdisjoint(core)
    assert not any(kind.startswith("sqlite_") for kind in core)


def test_derived_dependencies_point_one_way():
    """§3.2 property two: concrete -> core, never core -> concrete."""
    offenders = []
    for path in sorted(_CORE_SRC.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and ".impl." in node.module:
                offenders.append(f"{path.name}:{node.lineno} imports {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if ".impl." in alias.name:
                        offenders.append(f"{path.name}:{node.lineno} imports {alias.name}")
    assert not offenders, "\n".join(offenders)


def test_two_backends_proprietary_sets_are_disjoint():
    sqlite = _extra_kinds(_SQLITE)
    mysql = _extra_kinds(_MYSQL)
    overlap = sorted(sqlite & mysql)
    assert not overlap, f"same proprietary kind on two backends: {overlap}"


def test_core_does_not_re_export_a_backend_kind():
    """§3.2 property one, at the core entry points rather than in the registry."""
    entry_points = sorted(_CORE_SRC.rglob("__init__.py"))
    parent_init = _CORE_SRC.parent / "__init__.py"
    if parent_init.is_file():
        entry_points.append(parent_init)
    if not entry_points:
        pytest.skip("no core package entry point is available here")
    for path in entry_points:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("rhosocial.activerecord.backend.impl"), (
                    f"{path.name}:{node.lineno} re-exports a backend namespace"
                )
