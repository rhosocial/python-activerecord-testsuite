# src/rhosocial/activerecord/testsuite/feature/rules/contracts/retired.py
"""Retired APIs and forbidden syntax in an owner's expression trees.

The split moved registration out of the backends and dialect, renamed the value
node, and dropped the value-kind table. Old names are not aliases: a backend
that still imports one is talking to an API that no longer exists. ``global`` is
forbidden as well -- a published table is a value, not rebindable process state.

This is a static read: no scanned module is imported, so a shipped example with
a connection side effect cannot stall the audit.
"""

from __future__ import annotations

import ast
from typing import List

from .naming import source_files
from .subject import ExpressionSubject

_RETIRED = (
    "artifact_registry",
    "backend_registry",
    "registry_for_packages",
    "LiteralKind",
    "WireValue",
    "value_expression_kinds",
    "register_value_kinds",
    "format_literal_expression",
    "params.type",
)


def _audited_files(subject: ExpressionSubject):
    """Expression and registration files only -- not the backend itself.

    A backend may keep process-wide state for its driver (a shared executor,
    for example). The ban is on registration state and on retired expression
    APIs, so the audit follows the owner's expression namespace and its
    published registry, not its connection machinery.
    """
    for root in subject.roots:
        for path in source_files(root.path):
            relative = path.relative_to(root.path)
            in_expression = any(
                part in subject.expression_dirs for part in relative.parts[:-1]
            ) or relative.stem == "expression"
            if in_expression or path.stem.endswith("expression_registry"):
                yield path


def _retired_offenders(subject: ExpressionSubject) -> List[str]:
    found = []
    for path in _audited_files(subject):
        source = path.read_text(encoding="utf-8")
        for token in _RETIRED:
            if token in source:
                found.append(f"{path.as_posix()}: uses retired '{token}'")
    return found


def _global_offenders(subject: ExpressionSubject) -> List[str]:
    """The ban covers the whole backend: no rebindable process state anywhere."""
    found = []
    for root in subject.roots:
        for path in source_files(root.path):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Global):
                    found.append(f"{path.as_posix()}:{node.lineno}: global statement")
    return found


def _literal_class_offenders(subject: ExpressionSubject) -> List[str]:
    found = []
    for path in _audited_files(subject):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Literal":
                found.append(f"{path.as_posix()}:{node.lineno}: class Literal")
    return found


def test_no_retired_api_in_an_owner_tree(subject: ExpressionSubject) -> None:
    offenders = _retired_offenders(subject)
    assert not offenders, "retired API in the owner's tree:\n" + "\n".join(offenders)


def test_no_global_statement_in_an_owner_tree(subject: ExpressionSubject) -> None:
    offenders = _global_offenders(subject)
    assert not offenders, "global state in the owner's tree:\n" + "\n".join(offenders)


def test_no_expression_node_named_literal(subject: ExpressionSubject) -> None:
    offenders = _literal_class_offenders(subject)
    assert not offenders, "the value node is named Parameter:\n" + "\n".join(offenders)
