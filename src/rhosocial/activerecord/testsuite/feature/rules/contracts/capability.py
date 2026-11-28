# src/rhosocial/activerecord/testsuite/feature/rules/contracts/capability.py
"""Capability switches: bare reads, consulted at formatting time.

A dialect answers "can this be done" with switches (``supports_*``). Two claims
about them are checkable from source, and both are about *when* the answer is
read:

**A switch is a bare question.** It takes no arguments and returns a boolean.
A switch that takes a parameter is a policy decision in disguise -- the caller
would have to know which value to pass, which is the knowledge the switch exists
to provide.

**A switch is read while formatting, not while constructing.** An expression
collects its parameters at construction and asks no questions; the dialect
answers during rendering. A constructor that consults a capability has decided
that the dialect cannot do something before any dialect was asked to try, and
that decision is invisible to the caller who swaps dialects later.

What this cannot see: whether a formatter actually refuses when its switch is
False. That needs a node whose rendering the switch gates, and which node that
is differs per feature; the per-feature tests cover it where the feature is
defined.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple

from .naming import source_files
from .subject import ExpressionSubject

CAPABILITY_PREFIX = "supports_"


def _is_switch(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
        CAPABILITY_PREFIX
    )


def _takes_arguments(node: ast.AST) -> bool:
    args = node.args
    if args.posonlyargs or args.args[1:] or args.vararg or args.kwonlyargs or args.kwarg:
        return True
    return False


def _mentions_capability(node: ast.AST) -> bool:
    """Whether a statement reads any ``supports_*`` switch."""
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr.startswith(CAPABILITY_PREFIX):
            return True
        if isinstance(child, ast.Name) and child.id.startswith(CAPABILITY_PREFIX):
            return True
    return False


def _files(subject: ExpressionSubject) -> List[Tuple[Path, ast.AST]]:
    skip = set(subject.excluded_dirs) | set(subject.demonstration_dirs)
    found: List[Tuple[Path, ast.AST]] = []
    for root in subject.roots:
        for path in source_files(root.path):
            relative = path.relative_to(root.path)
            if skip & set(relative.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, ValueError):
                continue
            found.append((relative, tree))
    return found


def switches_with_arguments(subject: ExpressionSubject) -> List[str]:
    """Capability switches that take parameters."""
    problems: List[str] = []
    for relative, tree in _files(subject):
        for node in ast.walk(tree):
            if _is_switch(node) and _takes_arguments(node):
                problems.append(
                    f"{relative.as_posix()}:{node.lineno}: {node.name} takes arguments"
                )
    return problems


def capability_read_at_construction(subject: ExpressionSubject) -> List[str]:
    """``__init__`` bodies that consult a capability switch."""
    problems: List[str] = []
    for relative, tree in _files(subject):
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name != "__init__":
                continue
            for statement in node.body:
                if _mentions_capability(statement):
                    problems.append(
                        f"{relative.as_posix()}:{statement.lineno}: "
                        "capability read in __init__"
                    )
                    break
    return problems


def test_capability_switches_take_no_arguments(subject: ExpressionSubject) -> None:
    """A switch answers a question about the dialect, not about a value."""
    problems = switches_with_arguments(subject)
    assert not problems, "\n".join(problems)


def test_capabilities_are_read_when_formatting_not_before(subject: ExpressionSubject) -> None:
    """Constructing collects; formatting asks. A constructor that asks has
    already decided for a dialect it has not been given."""
    problems = capability_read_at_construction(subject)
    assert not problems, "\n".join(problems)
