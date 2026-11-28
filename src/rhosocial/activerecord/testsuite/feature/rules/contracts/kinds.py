# src/rhosocial/activerecord/testsuite/feature/rules/contracts/kinds.py
"""One expression name, one artifact kind.

An expression survives outside Python as an artifact: a kind string plus
parameters. The kind is computed by the framework from the class name -- never
stored -- so the artifact vocabulary and the class names cannot drift apart, as
long as two things hold and one more is stated:

**Names are unique inside a subject.** Two classes called ``Foo`` in different
modules are two nodes with one name: a traceback, a kind string or a diagram
cannot tell them apart.

**The registry is a bijection over the classes it admits.** Every kind resolves
to a class whose own ``kind()`` is that kind -- no kind names a class that
derives a different one -- and every admitted class appears under the kind it
derives. A reader rebuilding an artifact then gets exactly the class the writer
described.

**A class answers one kind.** A kind names one class, and one class answers one
kind. The exception the framework currently makes -- ``Parameter`` answering the
payload-typed value kinds -- is reported by this rule rather than excused here:
an undocumented alias is exactly what the claim forbids.

Derivation is read from the running framework, not reimplemented: a backend may
assign ``KIND_RESERVED`` at import time (``_value.KIND_RESERVED = ("MySQL",)``),
so a second static implementation would disagree with the framework on the very
cases the rule is about. The claim that matters is between the registry and the
classes, and both exist at run time.

What this cannot see: a kind registered outside a registry the subject exposes,
and a class the registry resolves but the subject's trees do not define.
"""

from __future__ import annotations

import ast
from typing import Dict, List, Optional, Set, Tuple

from .naming import (
    Tree,
    _subject_tree,
    base_names,
    core_vocabulary_tree,
    decorator_name,
    node_entries,
)
from .subject import CORE_BASE, ExpressionSubject

Definition = Tuple[str, str]


def _class_definition(trees: Tuple[Tree, ...], definition: Definition) -> Optional[ast.ClassDef]:
    """The class statement for *definition*, in whichever scanned tree holds it."""
    for tree in trees:
        entry = tree.classes.get(definition)
        if entry is not None:
            return entry[2]
    return None


def _base_chain(trees: Tuple[Tree, ...], definition: Definition) -> List[Definition]:
    """This class followed by its resolvable bases, most derived first.

    A source-order walk stands in for the runtime MRO: it is the order in which
    a reader meets declarations, and it is enough to decide which declaration
    of ``format_method``, ``REGISTER_BY_DEFAULT`` or an abstract name wins.
    """
    chain: List[Definition] = []
    seen: Set[Definition] = set()

    def visit(current: Definition) -> None:
        if current in seen:
            return
        seen.add(current)
        chain.append(current)
        node = _class_definition(trees, current)
        if node is None:
            return
        for base in base_names(node):
            for tree in trees:
                target = tree.resolve(current[0], base)
                if target is not None:
                    visit(target)
                    break

    visit(definition)
    return chain


def _declared_names(node: ast.ClassDef) -> Dict[str, bool]:
    """Names this class declares, mapped to whether the declaration is abstract."""
    found: Dict[str, bool] = {}
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[item.name] = any(
                decorator_name(decorator) == "abstractmethod"
                for decorator in item.decorator_list
            )
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = False
        elif (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and item.value is not None
        ):
            found[item.target.id] = False
    return found


def _abstract_names(trees: Tuple[Tree, ...], chain: List[Definition]) -> Set[str]:
    """Names still abstract once the whole base chain has been read.

    A most-derived concrete declaration clears an abstract one from a base --
    the same test ``__abstractmethods__`` applies at run time.
    """
    status: Dict[str, bool] = {}
    for definition in chain:
        node = _class_definition(trees, definition)
        if node is None:
            continue
        for name, abstract in _declared_names(node).items():
            status[name] = abstract
    return {name for name, abstract in status.items() if abstract}


def _declares_formatter(trees: Tuple[Tree, ...], chain: List[Definition]) -> bool:
    """Whether the chain resolves to a concrete ``format_method``.

    Only ``BaseExpression``'s sentinel means "none"; a base that supplies a
    formatter for its subclasses is a real declaration, as in core's collector.
    """
    for definition in chain:
        node = _class_definition(trees, definition)
        if node is None:
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                declares = item.name == "format_method"
            elif isinstance(item, ast.Assign):
                declares = any(
                    isinstance(target, ast.Name) and target.id == "format_method"
                    for target in item.targets
                )
            elif isinstance(item, ast.AnnAssign):
                declares = (
                    isinstance(item.target, ast.Name) and item.target.id == "format_method"
                )
            else:
                declares = False
            if declares:
                return definition[1] != CORE_BASE
    return False


def _opts_out(trees: Tuple[Tree, ...], chain: List[Definition]) -> bool:
    """Whether ``REGISTER_BY_DEFAULT`` is false for this class.

    The first declaration along the chain wins, matching attribute lookup on
    the runtime class; without one the framework default is to register.
    """
    for definition in chain:
        node = _class_definition(trees, definition)
        if node is None:
            continue
        for item in node.body:
            value: Optional[ast.AST] = None
            if isinstance(item, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "REGISTER_BY_DEFAULT"
                for target in item.targets
            ):
                value = item.value
            elif (
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "REGISTER_BY_DEFAULT"
            ):
                value = item.value
            if value is not None:
                return isinstance(value, ast.Constant) and value.value is False
    return False


def registers_by_default(trees: Tuple[Tree, ...], definition: Definition) -> bool:
    """Whether this class is admitted to an assembled registry by default.

    Mirrors core's collector: a node is a kind only when it is concrete, resolves
    a formatter of its own rather than ``BaseExpression``'s sentinel, and has
    not opted out. A base that names no formatter, or one that still owes an
    abstract method, is not a kind even though the naming scan sees it.
    """
    chain = _base_chain(trees, definition)
    if _abstract_names(trees, chain):
        return False
    if not _declares_formatter(trees, chain):
        return False
    if _opts_out(trees, chain):
        return False
    return True


def duplicate_name_offenders(subject: ExpressionSubject) -> List[str]:
    """Two nodes of the subject that share one class name."""
    by_name: Dict[str, List[str]] = {}
    for _, label, relative, name in node_entries(subject):
        by_name.setdefault(name, []).append(f"{label}/{relative.as_posix()}")
    return [
        f"{name} is declared by " + ", ".join(sorted(paths))
        for name, paths in sorted(by_name.items())
        if len(paths) > 1
    ]


def _registered(registry: object) -> Dict[str, object]:
    """Kind -> class, for every kind the registry resolves."""
    found: Dict[str, object] = {}
    for kind in registry.node_kinds():
        try:
            found[kind] = registry.resolve_node(kind)
        except Exception:  # a disabled kind is declared but not resolvable
            continue
    return found


def registry_offenders(subject: ExpressionSubject, registry: object) -> List[str]:
    """Disagreements between the registry and the classes it names."""
    trees = (_subject_tree(subject), core_vocabulary_tree())
    registered = _registered(registry)
    names = {name for _, _, _, name in node_entries(subject)}
    problems: List[str] = []

    for kind, cls in sorted(registered.items()):
        derived = cls.kind()
        if derived != kind:
            problems.append(f"{kind} resolves to {cls.__name__}, which derives {derived}")
        if cls.__name__ not in names and not _is_core_class(cls):
            problems.append(f"{kind} resolves to {cls.__name__}, which no node declares")

    admitted: Set[str] = set()
    for definition, label, relative, name in node_entries(subject):
        if not registers_by_default(trees, definition):
            continue
        admitted.add(name)
        if not any(cls.__name__ == name for cls in registered.values()):
            problems.append(
                f"{label}/{relative.as_posix()}: {name} is admitted by default "
                "but no registry kind resolves to it"
            )

    answering: Dict[str, List[str]] = {}
    for kind, cls in sorted(registered.items()):
        if subject.prefix is not None and not _own_kind(subject, kind):
            continue
        answering.setdefault(cls.__name__, []).append(kind)
    for name, kinds in sorted(answering.items()):
        if len(kinds) > 1:
            problems.append(
                f"{name} answers several kinds: " + ", ".join(sorted(kinds))
            )
    return problems


def _own_kind(subject: ExpressionSubject, kind: str) -> bool:
    """Whether *kind* is in this subject's own naming space."""
    if subject.prefix is None:
        return True
    return kind.startswith(_prefix_kind(subject.prefix))


def _prefix_kind(prefix: str) -> str:
    """The snake_case form a backend prefix takes in kinds."""
    return prefix.lower()


def _is_core_class(cls: object) -> bool:
    return str(getattr(cls, "__module__", "")).startswith(
        "rhosocial.activerecord.backend.expression"
    )


def test_expression_names_are_unique(subject: ExpressionSubject) -> None:
    """One name, one class: a traceback or a kind must identify one node."""
    offenders = duplicate_name_offenders(subject)
    assert not offenders, "\n".join(offenders)


def test_names_and_artifact_kinds_correspond(
    subject: ExpressionSubject, registry: object
) -> None:
    """Kind and class describe each other, one to one."""
    problems = registry_offenders(subject, registry)
    assert not problems, "\n".join(problems)
