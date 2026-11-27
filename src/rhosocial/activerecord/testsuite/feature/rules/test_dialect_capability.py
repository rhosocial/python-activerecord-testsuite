# src/rhosocial/activerecord/testsuite/feature/rules/test_dialect_capability.py
"""Formal source: backend-expression-dialect-capability.md §1.3 / §1.3.1.

Instantiation collects parameters; capability probes and version checks belong
to ``format_*``. §1.3.1 calls the first half "收集，不校验" and the second
"格式化 = 校验". A constructor that refuses through a module helper is the
same violation as one that refuses inline -- core's own
``feature/rules/test_expression_constructors_do_not_refuse.py`` established
the indirect-refusal scan for ``UnsupportedFeatureError``; this module extends
it to capability reads. Everything is read with ``ast`` and type checks: no
expression is probed with ``getattr`` / ``hasattr``.
"""

import ast
from pathlib import Path
from typing import Iterable, Set, Union

import pytest

from rhosocial.activerecord.backend.expression import bases as _bases

_Function = Union[ast.FunctionDef, ast.AsyncFunctionDef]
_CAPABILITY = ("supports_", "server_version", "version_info")
_CORE_SRC = Path(_bases.__file__).parent


def _capability_names(node: ast.AST) -> Set[str]:
    """Names read or called inside *node*, bare or as an attribute."""
    found = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Name):
                found.add(func.id)
            elif isinstance(func, ast.Attribute):
                found.add(func.attr)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            found.add(sub.id)
        elif isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Load):
            found.add(sub.attr)
    return found


def _reads_capability(node: ast.AST) -> bool:
    return any(
        name.startswith(_CAPABILITY[0]) or name in _CAPABILITY[1:]
        for name in _capability_names(node)
    )


def _offenders(tree: ast.Module, label: str) -> list:
    """Module-level functions and constructors that read a capability.

    Method-level probes are the renderer's or a public ``validate_*`` hook's
    business (core owns that half of the rule). The construction path -- a
    module helper called by ``__init__``, transitively -- is what is checked
    here; a dialect fact reaching a node along that path is the violation
    §1.3.1 forbids.
    """
    helpers = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    capability_helpers = {name for name, fn in helpers.items() if _reads_capability(fn)}
    changed = True
    while changed:
        changed = False
        for name, fn in helpers.items():
            if name not in capability_helpers and _capability_names(fn) & capability_helpers:
                capability_helpers.add(name)
                changed = True

    found = []
    candidates = list(helpers.values())
    for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        candidates.extend(
            n
            for n in cls.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__init__"
        )
    for fn in candidates:
        if _reads_capability(fn) or _capability_names(fn) & capability_helpers:
            found.append(f"{label}:{fn.lineno} {fn.name} reads capability at construction")
    return found


def _source_files() -> Iterable[Path]:
    return (p for p in sorted(_CORE_SRC.rglob("*.py")) if "__pycache__" not in p.parts)


def test_installed_core_expression_tree_is_scannable():
    files = list(_source_files())
    if not files:
        pytest.skip("core's expression source is not available in this environment")
    assert any("query_parts.py" in f.name for f in files)


def test_no_construction_path_reads_a_capability():
    offenders = []
    for path in _source_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError):
            continue  # a grammar younger than this interpreter, as in core's audit
        offenders.extend(_offenders(tree, path.name))
    assert not offenders, "\n".join(offenders)


def test_construction_collects_parameters_without_a_dialect():
    """§1.3.1: the node carries intent, even one the dialect may refuse."""
    from rhosocial.activerecord.backend.expression.query_parts import LimitOffsetClause
    from rhosocial.activerecord.backend.expression.types import VarCharType

    assert VarCharType(length=255).get_params()["length"] == 255
    # OFFSET without LIMIT is refused by some dialects at format time; with no
    # dialect bound there is nobody to ask, so construction still collects it.
    assert LimitOffsetClause(None, offset=5).get_params()["offset"] == 5


@pytest.mark.parametrize(
    "source",
    [
        "def probe(d):\n    return d.supports_window()\n",
        "def probe(d):\n    return d.server_version >= (3, 35)\n",
    ],
    ids=["supports", "version"],
)
def test_the_scan_detects_a_direct_module_helper(source):
    assert _offenders(ast.parse(source), "probe")


def test_the_scan_detects_an_indirect_refusal_chain():
    """The UUID family's shape: the constructor never names the probe itself."""
    source = (
        "def _inner(d):\n    return d.supports_x()\n"
        "def _outer(d):\n    return _inner(d)\n"
        "class P:\n"
        "    def __init__(self, d):\n        _outer(d)\n"
    )
    assert _offenders(ast.parse(source), "probe")


def test_the_scan_accepts_a_collecting_constructor():
    source = "class P:\n    def __init__(self, value):\n        self.value = value\n"
    assert not _offenders(ast.parse(source), "probe")
