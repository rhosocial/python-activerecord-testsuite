# src/rhosocial/activerecord/testsuite/feature/rules/contracts/expression.py
"""Each expression node owns exactly one formatter, and no formatter is shared.

An expression is data; rendering it is the dialect's behaviour. The two are
bound one-to-one: a node names the formatter that renders it, and no two nodes
name the same one. The binding is what lets a dialect be composed from feature
groups -- an override replaces one formatter by name, and if two nodes claimed
that name an override would silently change the rendering of a node nobody
meant to touch.

Three claims, all read from source:

**Every node resolves to a formatter.** A node either declares ``format_method``
itself or inherits it. A node that reaches neither is data with no renderer: it
can be constructed, serialized and compared, but nothing in any dialect will
turn it into SQL.

**Every formatter name is a formatter name.** ``format_`` is the prefix the
dialect side looks up; a declared name without it is a node pointing at an
attribute that cannot exist.

**No formatter name is declared twice.** Two declarations of one name are the
same defect as an alias: an override hits one declaration and leaves the other
pointing at the old behaviour.

Resolution is ``(module, name)`` and follows the same rules as
:mod:`.naming`: a bare class name is ambiguous across a tree, so the base chain
is walked through each module's own ``from ... import`` statements. A base that
resolves outside the subject's tree is looked up in core's vocabulary -- that is
the reuse case, where a backend node deliberately keeps core's formatter, and it
must keep exactly the same one.

Not claimed here: a closed vocabulary of class-name suffixes. The families are an
open set -- a new statement kind invents a suffix before anyone writes it down --
so a rule that demanded one of a fixed list would forbid the extension the
framework is built to allow. What ties a node to its category is the formatter it
declares, which this module does check.

What this cannot see: a formatter named through a computed attribute or assigned
after the class body, and the dialect side itself -- whether the named attribute
exists on a composed dialect is a separate claim, checked where a dialect
instance is available.
"""

from __future__ import annotations

import ast
from typing import Dict, List, Optional, Set, Tuple

from .naming import Tree, base_names, node_entries
from .subject import ExpressionSubject, core_expression_root

Definition = Tuple[str, str]

FORMAT_PREFIX = "format_"


def _decorator_name(decorator: ast.AST) -> str:
    """A decorator's simple name."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return ""


def declared_format(node: ast.ClassDef) -> Optional[str]:
    """The formatter name a class body declares, if it declares one.

    Only a ``property`` named ``format_method`` returning a string literal
    counts. A method that computes its answer at run time is a formatter nobody
    can name from source, and the claims above are about names.
    """
    for item in node.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if item.name != "format_method":
            continue
        if not any("property" in _decorator_name(d) for d in item.decorator_list):
            continue
        for child in ast.walk(item):
            if (
                isinstance(child, ast.Return)
                and isinstance(child.value, ast.Constant)
                and isinstance(child.value.value, str)
            ):
                return child.value.value
    return None


# ---- core's own vocabulary ---------------------------------------------- #


def core_expression_tree() -> Tree:
    """Core's expression package, read as definitions."""
    tree = Tree()
    tree.add_root(core_expression_root(), set())
    return tree


def core_formats() -> Dict[Definition, str]:
    """Every core expression class's formatter, declared or inherited.

    Computed inside core's own tree: a core class either declares the name or
    inherits it from another core class, and the chain never leaves the package.
    """
    tree = core_expression_tree()
    resolved: Dict[Definition, Optional[str]] = {}
    visiting: Set[Definition] = set()

    def resolve(definition: Definition) -> Optional[str]:
        if definition in resolved:
            return resolved[definition]
        entry = tree.classes.get(definition)
        if entry is None or definition in visiting:
            return None
        visiting.add(definition)
        node = entry[2]
        name = declared_format(node)
        if name is None:
            for base in base_names(node):
                if base == "BaseExpression":
                    break
                target = tree.resolve(definition[0], base)
                if target is None:
                    continue
                name = resolve(target)
                if name:
                    break
        visiting.discard(definition)
        resolved[definition] = name
        return name

    for definition in tree.classes:
        resolve(definition)
    formats = {definition: name for definition, name in resolved.items() if name}
    # A caller names the package, not the submodule: ``from ...statements import
    # InsertStatement`` is the ordinary spelling. Without the alias keys the
    # vocabulary would know only definition sites, and every backend node
    # deriving from a re-exported core class would look formatter-less.
    changed = True
    while changed:
        changed = False
        for alias, target in tree.imports.items():
            if alias in formats or target not in formats:
                continue
            formats[alias] = formats[target]
            changed = True
    return formats


def format_of(
    tree: Tree,
    definition: Definition,
    core: Dict[Definition, str],
    memo: Optional[Dict[Definition, Optional[str]]] = None,
    visiting: Optional[Set[Definition]] = None,
) -> Optional[str]:
    """The formatter a node resolves to, searching every declared base.

    A class may list several bases -- ``AbsoluteIntegerFunction(AbsoluteFunction,
    DeclaredValueType, NumericValue)`` is one -- and the formatter can come from
    any of them, so the walk is depth-first over all bases rather than through
    the first one that resolves. A base that resolves outside the subject's tree
    is looked up in core's vocabulary: that is the reuse case, where a backend
    node keeps core's formatter.
    """
    memo = {} if memo is None else memo
    visiting = set() if visiting is None else visiting
    if definition in memo:
        return memo[definition]
    if definition in visiting:  # a cycle is a defect no rule should guess at
        return None
    entry = tree.classes.get(definition)
    if entry is None:
        return core.get(definition)
    visiting.add(definition)
    name = declared_format(entry[2])
    if name is None:
        for base in base_names(entry[2]):
            if base == "BaseExpression":
                continue
            target = tree.resolve(definition[0], base)
            if target is None:
                continue
            name = format_of(tree, target, core, memo, visiting)
            if name:
                break
    visiting.discard(definition)
    memo[definition] = name
    return name

def subject_formats(subject: ExpressionSubject) -> Dict[Definition, Optional[str]]:
    """Every node of *subject*, mapped to the formatter it resolves to."""
    from .naming import _subject_tree

    tree = _subject_tree(subject)
    core = core_formats()
    return {
        definition: format_of(tree, definition, core)
        for definition, _, _, _ in node_entries(subject)
    }

# ---- the claims --------------------------------------------------------- #


def unresolved_offenders(subject: ExpressionSubject) -> List[str]:
    """Leaf nodes that reach no formatter at all.

    A base class is not a renderer's client: ``SQLValue``, ``SchemaObject`` and
    their kin exist to be derived from, and the nodes below them carry the
    formatter. So the claim applies to leaves -- a node nobody derives from --
    where a missing renderer means data that no dialect can turn into SQL.
    """
    from .naming import _subject_tree

    tree = _subject_tree(subject)
    found = subject_formats(subject)
    parents: Set[Definition] = set()
    types: Set[Definition] = set()
    for definition, _, _, _ in node_entries(subject):
        reach = _ancestors(tree, definition)
        parents |= reach
        types |= {d for d in reach if d[1] == "DataType"}
    return [
        f"{label}/{relative.as_posix()}: {name} resolves to no format_*"
        for definition, label, relative, name in node_entries(subject)
        if found.get(definition) is None
        and definition not in parents
        and not (_ancestors(tree, definition) & types)
    ]

def misnamed_offenders(subject: ExpressionSubject) -> List[str]:
    """Declared formatter names that are not formatter names."""
    found = subject_formats(subject)
    problems: List[str] = []
    for definition, name in found.items():
        if name is None or name.startswith(FORMAT_PREFIX):
            continue
        problems.append(f"{definition[0]}.{definition[1]}: declares {name!r}")
    return problems


def _ancestors(tree: Tree, definition: Definition) -> Set[Definition]:
    """Every class *definition* derives from, inside the tree."""
    seen: Set[Definition] = set()
    stack = [definition]
    while stack:
        current = stack.pop()
        for base in base_names(tree.classes[current][2]) if current in tree.classes else ():
            target = tree.resolve(current[0], base)
            if target is not None and target not in seen:
                seen.add(target)
                stack.append(target)
    return seen


def duplicate_offenders(subject: ExpressionSubject) -> List[str]:
    """Formatter names declared by classes that are not one family.

    A shared name is acceptable when one declarer is an ancestor of every other:
    the base is the canonical declaration and the descendants restate it, which
    a dialect's family dispatcher relies on. A shared name with no such
    ancestry means two unrelated nodes claim the same renderer, and an override
    of that name changes a node nobody meant to touch.
    """
    from .naming import _subject_tree

    tree = _subject_tree(subject)
    owners: Dict[str, List[Definition]] = {}
    for definition, (_, _, node) in tree.classes.items():
        name = declared_format(node)
        if name is not None:
            owners.setdefault(name, []).append(definition)
    problems: List[str] = []
    for name, defs in sorted(owners.items()):
        if len(defs) < 2:
            continue
        core_tree = core_expression_tree()
        common: Optional[Set[Definition]] = None
        for definition in defs:
            reach = _ancestors(tree, definition) | _ancestors(core_tree, definition) | {definition}
            common = reach if common is None else (common & reach)
        # A shared ancestor inside the subject means one family served by one
        # dispatcher: the typed columns are exactly that case. Only BaseExpression
        # in common means the declarers are unrelated, and one renderer cannot
        # be both nodes' canonical declaration.
        shared = {d for d in (common or set()) if d[1] != "BaseExpression"}
        if shared:
            continue
        problems.append(
            f"{name} declared by unrelated classes: "
            + ", ".join(f"{module}.{cls}" for module, cls in sorted(defs))
        )
    return problems

# ---- the tests every consumer runs -------------------------------------- #

MIN_FORMATS = 1


def test_the_scan_reaches_the_formatters(subject: ExpressionSubject) -> None:
    """The mapping must reach real declarations, or the claims below are vacuous."""
    found = subject_formats(subject)
    assert len(found) >= MIN_FORMATS, f"no expression node was resolved for {subject.label}"


def test_every_node_resolves_to_a_formatter(subject: ExpressionSubject) -> None:
    """A node with no renderer is data no dialect can turn into SQL."""
    offenders = unresolved_offenders(subject)
    assert not offenders, "\n".join(offenders)


def test_formatter_names_are_named_as_formatters(subject: ExpressionSubject) -> None:
    """``format_`` is the prefix the dialect side looks up."""
    offenders = misnamed_offenders(subject)
    assert not offenders, "\n".join(offenders)


def test_no_formatter_name_is_declared_twice(subject: ExpressionSubject) -> None:
    """Two declarations of one name are an alias: an override forks."""
    offenders = duplicate_offenders(subject)
    assert not offenders, "\n".join(offenders)
