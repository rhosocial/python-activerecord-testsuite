# src/rhosocial/activerecord/testsuite/feature/rules/contracts/naming.py
"""Where an expression node may live, and what it may be called.

Three claims, each true of both sides of the split and parameterised by the
subject rather than by which side is being examined:

**Placement.** A node lives in the subject's expression namespace -- ``expression/``
as a package, or ``expression.py`` as a single module -- and nowhere else in the
subject's trees. A node declared elsewhere has no separator between it and the
rest of the tree: it can be imported by name, and nothing says who owns it.

**Naming.** The side that owns proprietary vocabulary writes its own name in
front of every node it declares. The prefix is what keeps that vocabulary
distinguishable wherever only a class name survives -- a kind string, a
traceback, a serialized payload. The generic side owns no proprietary
vocabulary, so this claim does not apply there; it is skipped as not applicable
rather than satisfied by a list of names to avoid.

**Ownership.** A node that carries an owner's name must not also be a core
expression name: one description with two owners is the same defect as two
names for one description. This applies only where an owner exists, so the
generic side's own vocabulary is not checked against itself.

Resolution is ``(module, name)``, never the bare name. A tree can define the
same name twice for unrelated reasons -- an expression object and a plain base
class sharing ``Procedure`` is a real example -- and a rule keyed on the bare
name would treat a subclass of the second as a node of the first. A base name is
resolved through the defining module's own ``from ... import`` statements, so
the class a declaration actually derives from is the one that decides.

Everything is read from source with ``ast`` and no scanned module is imported:
a shipped example may open a connection at import time, and a static audit must
not wait on it. A class *defined* in the subject's tree is owned by it whatever
its name, which is what lets a reused core name be reported instead of folded
into core's vocabulary.

What this cannot see: a node defined outside the subject's own directories, a
class built at run time with ``type()``, a base named through an alias this
reader cannot resolve (it is treated as not-a-node rather than guessed), and --
on the generic side -- a name that merely looks like some backend's, since
recognising it would require the knowledge this side is defined not to have.
"""

from __future__ import annotations

import ast
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple

from .subject import (
    CORE_BASE,
    ExpressionSubject,
    Root,
    core_expression_root,
)

Definition = Tuple[str, str]  # (module, name)


# ---- source reading ----------------------------------------------------- #


def source_files(directory: Path) -> List[Path]:
    """Every Python source below *directory*, in a stable order."""
    return sorted(
        path for path in Path(directory).rglob("*.py") if "__pycache__" not in path.parts
    )


def module_of(root: Root, relative: Path) -> str:
    """The dotted module a file contributes to under *root*."""
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    return ".".join([root.module, *parts]) if parts else root.module


def base_names(node: ast.ClassDef) -> Set[str]:
    """Base-class names in a class statement, local or qualified."""
    found: Set[str] = set()
    for base in node.bases:
        if isinstance(base, ast.Name):
            found.add(base.id)
        elif isinstance(base, ast.Attribute):
            found.add(base.attr)
    return found


def decorator_name(decorator: ast.AST) -> str:
    """A decorator's simple name."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return decorator_name(decorator.func)
    return ""


def is_abstract(node: ast.ClassDef) -> bool:
    """Whether this class statement refuses to be instantiated."""
    if {"Protocol", "ABC"} & base_names(node):
        return True
    return any(
        any(decorator_name(d) == "abstractmethod" for d in item.decorator_list)
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


class Tree:
    """Classes and imports of one or more roots, keyed by ``(module, name)``."""

    def __init__(self) -> None:
        self.classes: Dict[Definition, Tuple[Root, Path, ast.ClassDef]] = {}
        self.imports: Dict[Definition, Definition] = {}

    def add_root(self, root: Root, skip: Set[str]) -> None:
        for path in source_files(root.path):
            relative = path.relative_to(root.path)
            if skip & set(relative.parts):
                continue
            module = module_of(root, relative)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, ValueError):
                continue
            self._read(root, path, relative, module, tree)

    def _read(self, root: Root, path: Path, relative: Path, module: str, tree: ast.AST) -> None:
        package = module if relative.name == "__init__.py" else module.rsplit(".", 1)[0]
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.classes[(module, node.name)] = (root, relative, node)
            elif isinstance(node, ast.ImportFrom):
                source = self._source_module(package, node.level, node.module)
                if source is None:
                    continue
                for alias in node.names:
                    local = alias.asname or alias.name
                    self.imports[(module, local)] = (source, alias.name)

    @staticmethod
    def _source_module(package: str, level: int, module: Optional[str]) -> Optional[str]:
        """Resolve a ``from`` clause to the module it names."""
        if level == 0:
            return module
        parts = package.split(".")
        if level > len(parts):
            return None
        base = ".".join(parts[: len(parts) - (level - 1)])
        return f"{base}.{module}" if module else base

    def resolve(self, module: str, name: str) -> Optional[Definition]:
        """``(module, name)`` a base name refers to, as written in *module*.

        Re-exports are followed. A package ``__init__`` that re-exports a class
        imported from a submodule is the ordinary way a name reaches a caller,
        and stopping at the package would say the class does not exist. The walk
        ends when a definition is found or a name repeats.
        """
        current: Definition = (module, name)
        seen: Set[Definition] = set()
        via_import = False
        while current not in seen:
            seen.add(current)
            if current in self.classes:
                return current
            target = self.imports.get(current)
            if target is None:
                # A name that was never imported is unknown here; a name reached
                # through an import is that module's class, even when the module
                # lives outside this tree -- core is exactly that case.
                return current if via_import else None
            current = target
            via_import = True
        return None


def reachable(tree: Tree, seed: List[Definition]) -> Set[Definition]:
    """Every class whose own base chain reaches *seed*."""
    seen: Set[Definition] = set(seed)
    changed = True
    while changed:
        changed = False
        for definition, (_, _, node) in tree.classes.items():
            if definition in seen:
                continue
            for base in base_names(node):
                target = tree.resolve(definition[0], base)
                if target in seen:
                    seen.add(definition)
                    changed = True
                    break
                if base == CORE_BASE:
                    seen.add(definition)
                    changed = True
                    break
    return seen


def core_vocabulary_tree() -> Tree:
    """The core expression package, read as ``(module, name)`` definitions."""
    tree = Tree()
    tree.add_root(core_expression_root(), set())
    return tree


def core_vocabulary() -> Set[Definition]:
    """Core's expression vocabulary, as ``(module, name)`` pairs.

    Re-export names are included: ``from ....expression.types import DataType``
    names the package, while the class is defined in the package's submodule. A
    vocabulary that only listed definition sites would fail to recognise the
    name a caller actually wrote, and every node deriving from it would look
    unreachable.
    """
    tree = core_vocabulary_tree()
    seeds = [definition for definition in tree.classes if definition[1] == CORE_BASE]
    seen = reachable(tree, seeds)
    changed = True
    while changed:
        changed = False
        for alias, target in tree.imports.items():
            if alias not in seen and target in seen:
                seen.add(alias)
                changed = True
    return seen


# ---- the subject's own nodes -------------------------------------------- #


@lru_cache(maxsize=None)
def _subject_tree(subject: ExpressionSubject) -> Tree:
    tree = Tree()
    skip = set(subject.excluded_dirs) | set(subject.demonstration_dirs)
    for root in subject.roots:
        tree.add_root(root, skip)
    return tree


def node_entries(subject: ExpressionSubject) -> List[Tuple[Tuple[str, str], str, Path, str]]:
    """Concrete nodes owned by *subject*, with their ``(module, name)`` key.

    Entries are ``((module, name), root label, relative path, class name)``.
    Abstract bases and protocols stay in the inheritance graph and are left out
    of the result: a concrete subclass reaches core through them, and a base is
    not a node.
    """
    tree = _subject_tree(subject)
    vocabulary = core_vocabulary()
    seen = reachable(tree, list(vocabulary))
    found: List[Tuple[Tuple[str, str], str, Path, str]] = []
    for definition in sorted(seen):
        if definition[1] == CORE_BASE:
            continue
        entry = tree.classes.get(definition)
        if entry is None:
            continue  # a core definition, not declared in this subject's trees
        root, relative, node = entry
        if is_abstract(node):
            continue
        found.append((definition, root.label, relative, definition[1]))
    return found


def nodes(subject: ExpressionSubject) -> List[Tuple[str, Path, str]]:
    """Concrete nodes owned by *subject*, as ``(root label, relative path, name)``."""
    return [
        (label, relative, name)
        for _, label, relative, name in node_entries(subject)
    ]



def in_expression_namespace(subject: ExpressionSubject, relative_path: Path) -> bool:
    """Whether a path is one of the subject's expression namespaces.

    Two shapes count: ``expression/…`` as a directory, and ``expression.py`` as a
    single module -- a module is a namespace too, and a subject that keeps its
    whole vocabulary in one file is still keeping it in one place.
    """
    parts = relative_path.parts
    if not parts:
        return False
    if len(parts) > 1 and parts[0] in subject.expression_dirs:
        return True
    return (
        len(parts) == 1
        and parts[0].endswith(".py")
        and parts[0][: -len(".py")] in subject.expression_dirs
    )


# ---- the claims --------------------------------------------------------- #


def placement_offenders(subject: ExpressionSubject) -> List[str]:
    """Nodes declared outside the subject's expression namespace."""
    return [
        f"{label}/{relative.as_posix()}: {name} is declared outside the expression namespace"
        for label, relative, name in nodes(subject)
        if not in_expression_namespace(subject, relative)
    ]


def open_package_offenders(subject: ExpressionSubject) -> List[str]:
    """The ``__init__.py`` that would close the subject's namespace root."""
    if subject.open_package_root is None:
        return []
    target = Path(subject.open_package_root) / "__init__.py"
    if target.exists():
        return [f"{target}: closes a namespace package"]
    return []


# ---- the tests every consumer runs -------------------------------------- #

MIN_NODES = 1


def test_the_scan_reaches_the_subject(subject: ExpressionSubject) -> None:
    """The rule must see the namespace it claims to have cleared.

    An empty node list produces an empty offender list, and every claim below
    looks satisfied. Pinning the reach keeps them meaningful: a subject with no
    nodes is a misdeclared subject, not a clean one.
    """
    found = nodes(subject)
    assert len(found) >= MIN_NODES, (
        f"no expression node was found for {subject.label}; "
        f"roots: {[str(root.path) for root in subject.roots]}"
    )


def test_expression_nodes_live_in_the_expression_namespace(
    subject: ExpressionSubject,
) -> None:
    """A node lives in the subject's expression namespace and nowhere else.

    A node declared beside the namespace has no separator between it and the
    rest of the tree: it can be imported by name, it has no owner visible in the
    import path, and a second distribution contributing to the same tree cannot
    tell its own classes from this subject's.
    """
    offenders = placement_offenders(subject)
    assert not offenders, (
        f"nodes declared outside the expression namespace of {subject.label}:\n"
        + "\n".join(offenders)
    )


def test_the_namespace_root_is_an_open_package(subject: ExpressionSubject) -> None:
    """No ``__init__.py`` may close the subject's namespace root.

    A regular package pins its ``__path__`` to the first location the import
    system reaches, so a distribution contributing to the same namespace from
    another location becomes invisible -- and the failure depends on install
    order, so it passes where it was written and breaks elsewhere.
    """
    offenders = open_package_offenders(subject)
    assert not offenders, "\n".join(offenders)
