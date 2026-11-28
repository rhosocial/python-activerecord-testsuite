# src/rhosocial/activerecord/testsuite/feature/rules/contracts/layout.py
"""Top-level expression sub-namespace names are a *form* rule, not a contract.

This module describes code organization only: which first-level names appear
under a subject's expression root. It is deliberately **not** part of the
semantic formal description -- no expression's meaning, rendering or identity
depends on the directory that holds it.

The canonical set is a code-organization decision. A namespace may be a
directory **or** a same-named module, never both at once: ``types/`` and
``types.py`` coexisting is ambiguous and is reported as an offender. Only the
first-level name is governed. Every owner has adopted the layout, so the rule
is now gated through the shared ``backend/expression`` wrapper. Infrastructure
packages that declare no concrete node (``bases/``) are exempt by construction,
not by an exception list.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Iterable, List, Optional, Set

from ..backend.support import impl_root_of
from .subject import ExpressionSubject

CANONICAL_NAMESPACES: frozenset = frozenset(
    {
        "functions",
        "objects",
        "sources",
        "statements",
        "types",
        "predicates",
        "query_parts",
        "operators",
        "value_types",
        "column_types",
        "introspection",
    }
)

#: Names that are never part of a namespace vocabulary. Dunder entries such as
#: ``__init__.py`` and ``__pycache__``, dot-directories and build/cache suffixes
#: are packaging artifacts, not expression namespaces.
_CACHE_DIRS: frozenset = frozenset(
    {".pytest_cache", ".ruff_cache", ".mypy_cache", ".tox", ".venv", ".eggs", "node_modules"}
)
_CACHE_SUFFIXES: tuple = (".pyc", ".pyo", ".pyd", ".so", ".egg-info", ".dist-info")


class _SortedNamespaceSet(set):
    """A ``set`` that iterates in stable sorted order, for readable reports."""

    def __iter__(self):
        return iter(sorted(super().__iter__()))


def _is_artifact(name: str) -> bool:
    """Whether a top-level entry is a cache, dunder or hidden artifact."""
    if name.startswith(".") or (name.startswith("__") and name.endswith("__")):
        return True
    if name in _CACHE_DIRS or name.endswith(_CACHE_SUFFIXES):
        return True
    return False


def _namespace_of(entry: Path) -> Optional[str]:
    """Normalized namespace name of a directory or a Python module.

    A directory and a same-named module both spell one name, but they may not
    coexist -- :func:`_ambiguous_shape_names` reports that collision. Non-Python
    files and all artifacts are ignored.
    """
    name = entry.name
    if _is_artifact(name):
        return None
    if entry.is_dir():
        return name
    if entry.is_file() and name.endswith(".py"):
        stem = name[: -len(".py")]
        # Check the stem too: ``__init__.py`` is a dunder *after* normalization.
        return None if _is_artifact(stem) else stem
    return None


def _expression_roots(subject: ExpressionSubject) -> Iterable[Path]:
    """Directories whose immediate children are the subject's sub-namespaces.

    A subject normally supplies these through its ``roots``: a core-style root
    is the expression package itself, while a backend root is ``impl/<name>``
    with an ``expression/`` child. A subject that only declares
    ``impl_module_prefix`` is located with :func:`impl_root_of` instead.
    """
    candidates: List[Path] = []
    for root in subject.roots:
        path = Path(root.path).resolve()
        if path.name in subject.expression_dirs or root.module.endswith(".expression"):
            candidates.append(path)
        for name in subject.expression_dirs:
            child = path / name
            if child.is_dir():
                candidates.append(child)
            # A single ``expression.py`` has no sub-namespaces to enumerate.

    if not candidates and subject.impl_module_prefix:
        try:
            package = importlib.import_module(f"{subject.impl_module_prefix}.expression")
        except (ImportError, AssertionError):
            pass
        else:
            impl_root = impl_root_of(package)
            for name in subject.expression_dirs:
                child = impl_root / name
                if child.is_dir():
                    candidates.append(child)

    seen: Set[Path] = set()
    for candidate in candidates:
        key = candidate.resolve()
        if key in seen:
            continue
        seen.add(key)
        yield candidate


def expression_namespaces(subject: ExpressionSubject) -> Set[str]:
    """Top-level sub-namespace names under the subject's expression root(s).

    Directories and ``.py`` modules are reported by their comparable name;
    ``__init__.py``, ``__pycache__``, dunder entries and cache artifacts are
    excluded. The result iterates in stable sorted order; callers that build
    strings from it still use :func:`sorted` explicitly.
    """
    found: Set[str] = _SortedNamespaceSet()
    for root in _expression_roots(subject):
        try:
            entries = sorted(root.iterdir(), key=lambda entry: entry.name)
        except OSError:
            continue
        for entry in entries:
            name = _namespace_of(entry)
            if name is not None:
                found.add(name)
    return found


#: Root expression classes are infrastructure, not concrete nodes. A namespace
#: that declares only these (or declares no class at all) is exempt from the
#: canonical-name rule by construction, not by a name-based exception list.
_ROOT_CLASSES = frozenset(
    {
        "BaseExpression",
        "SQLValue",
        "SQLPredicate",
        "ColumnBase",
        "QueryStatement",
        "DataType",
    }
)


def _declares_concrete_node(path: Path) -> bool:
    """Whether *path* (a namespace directory or module) declares a concrete node.

    A class is a concrete node when it derives from one of the root expression
    classes and is not itself one of those roots. Mixins, enums, protocols and
    helper functions are not nodes; a namespace holding only those is
    infrastructure. The decision is made from the AST, never from a directory
    name.
    """
    files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
    for source in files:
        if "__pycache__" in source.parts:
            continue
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name in _ROOT_CLASSES:
                continue
            for base in node.bases:
                if isinstance(base, ast.Name):
                    name = base.id
                elif isinstance(base, ast.Attribute):
                    name = base.attr
                else:
                    continue
                if name in _ROOT_CLASSES:
                    return True
    return False


def _ambiguous_shape_names(subject: ExpressionSubject) -> List[str]:
    """Names present as both a directory and a same-named module."""
    found: Set[str] = set()
    for root in _expression_roots(subject):
        try:
            entries = list(root.iterdir())
        except OSError:
            continue
        dirs = {e.name for e in entries if e.is_dir() and not _is_artifact(e.name)}
        mods = {
            e.stem
            for e in entries
            if e.is_file() and e.suffix == ".py" and not _is_artifact(e.stem)
        }
        found |= dirs & mods
    return sorted(found)


def layout_offenders(subject: ExpressionSubject) -> List[str]:
    """Names that violate the form rule: collisions, or non-canonical families."""
    if not CANONICAL_NAMESPACES:
        names = ", ".join(sorted(expression_namespaces(subject))) or "(none)"
        return [
            f"{subject.label}: canonical namespace set is empty "
            f"(pending design decision); observed: {names}"
        ]
    problems = [
        f"{subject.label}: expression namespace {name!r} exists as both a "
        "directory and a module"
        for name in _ambiguous_shape_names(subject)
    ]
    roots = list(_expression_roots(subject))
    for name in sorted(expression_namespaces(subject) - CANONICAL_NAMESPACES):
        if any(
            _declares_concrete_node(root / name) or _declares_concrete_node(root / f"{name}.py")
            for root in roots
        ):
            problems.append(f"{subject.label}: expression namespace {name!r} is not canonical")
    return problems


def test_expression_namespaces_are_canonical(subject: ExpressionSubject) -> None:
    """A future form rule: every subject uses the same top-level namespace names.

    Skipped until the canonical set is agreed. pytest is imported here only so
    the pure helpers above stay importable from the non-test diagnostics module.
    """
    if not CANONICAL_NAMESPACES:
        import pytest

        pytest.skip("canonical namespace set not decided yet")
    offenders = layout_offenders(subject)
    assert not offenders, "\n".join(offenders)
