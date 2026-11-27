# src/rhosocial/activerecord/testsuite/feature/rules/test_formatter_cases.py
"""Formal source: backend-expression-families.md §5.1-§5.4.

Four formatter cases: reuse (§5.1), override of a reused node (§5.2), a
derived node whose formatter handles both the core and the derived shape
(§5.3), and a proprietary node answered by a backend-named protocol (§5.4).
A registered node whose declared ``format_*`` cannot be reached is a defect:
the declaration can name a formatter nobody implements. Formatter names are
read from the property's source with ``ast``; expression nodes are never
probed with ``getattr`` / ``hasattr``.
"""

import ast
import inspect
import textwrap

import pytest

from rhosocial.activerecord.backend.expression.bases import BaseExpression
from rhosocial.activerecord.backend.expression.serialization import core_registry
from rhosocial.activerecord.backend.impl.dummy.dialect import DummyDialect


class _CoreProbe(BaseExpression):
    @property
    def format_method(self) -> str:
        return "format_probe_node"

    def __init__(self, dialect=None, *, value=None):
        super().__init__(dialect)
        self.value = value


class _DerivedProbe(_CoreProbe):
    def __init__(self, dialect=None, *, value=None, extra=None):
        super().__init__(dialect, value=value)
        self.extra = extra


class _OverrideDialect(DummyDialect):
    """§5.3: one formatter, two shapes, both answered."""

    def format_probe_node(self, expr):
        if isinstance(expr, _DerivedProbe):
            return f"derived({expr.value},{expr.extra})", ()
        return f"core({expr.value})", ()


_UNKNOWN = object()


def _declared_formatter(cls):
    """The ``format_*`` name a class declares, read as source, not probed."""
    for ancestor in cls.__mro__:
        prop = vars(ancestor).get("format_method")
        if prop is None or not isinstance(prop, property) or prop.fget is None:
            continue
        try:
            source = textwrap.dedent(inspect.getsource(prop.fget))
        except (OSError, TypeError):
            return _UNKNOWN  # a build without source cannot be judged here
        tree = ast.parse(source)
        returns = [
            node.value.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Return)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ]
        return returns[0] if returns else None
    return None


def _unreachable(registry, dialect):
    """Registered leaf kinds whose declared formatter the dialect cannot answer."""
    classes = {kind: registry.resolve_node(kind) for kind in registry.node_kinds()}
    has_child = {
        parent
        for parent in classes.values()
        for child in classes.values()
        if parent is not child and issubclass(child, parent)
    }
    missing = []
    for kind, cls in classes.items():
        if cls in has_child:
            continue  # a structural base is not a renderable leaf
        name = _declared_formatter(cls)
        if name is _UNKNOWN:
            continue
        if name is None or not callable(getattr(dialect, name, None)):
            missing.append(kind)
    return sorted(missing)


def test_reuse_keeps_the_core_formatter():
    """§5.1: a backend that does not override a core formatter uses that function."""
    try:
        from rhosocial.activerecord.backend.impl.sqlite.dialect import SQLiteDialect
    except ImportError as exc:
        pytest.skip(f"SQLite dialect not available: {exc}")
    from rhosocial.activerecord.backend.expression.core import Literal

    name = _declared_formatter(Literal)
    if name is _UNKNOWN:
        pytest.skip("core expression source is unavailable here")
    assert name == "format_literal_expression"
    assert DummyDialect.format_literal_expression is SQLiteDialect.format_literal_expression
    assert Literal(None, "x").to_sql(DummyDialect())[0] == "?"


def test_override_reuses_the_node_but_not_the_formatter():
    """§5.2: the expression stays a core node; the formatter changes."""
    try:
        from rhosocial.activerecord.backend.impl.sqlite.dialect import SQLiteDialect
    except ImportError as exc:
        pytest.skip(f"SQLite dialect not available: {exc}")
    from rhosocial.activerecord.backend.expression.types import TextType

    # TextType is core; the backend overrides its per-name formatter.
    name = "format_data_type_text"
    declared = _declared_formatter(TextType)
    if declared is _UNKNOWN:
        pytest.skip("core expression source is unavailable here")
    assert declared == "format_data_type"
    assert getattr(DummyDialect, name) is not getattr(SQLiteDialect, name)
    assert TextType().to_sql(DummyDialect()) == ("TEXT", ())
    assert TextType().to_sql(SQLiteDialect()) == ("TEXT", ())


def test_a_derivation_formatter_handles_both_shapes():
    """§5.3: ``fmt: {e, e'} -> S``, with e' a subclass carrying extra params."""
    dialect = _OverrideDialect()
    assert _CoreProbe(None, value="a").to_sql(dialect) == ("core(a)", ())
    assert _DerivedProbe(None, value="a", extra="b").to_sql(dialect) == ("derived(a,b)", ())


def test_a_proprietary_node_uses_a_backend_named_protocol():
    """§5.4: FTS5 is answered by ``SQLiteFTS5Support``, not by core's family."""
    try:
        from rhosocial.activerecord.backend.impl.sqlite.dialect import SQLiteDialect
        from rhosocial.activerecord.backend.impl.sqlite.expression.fts5 import (
            SQLiteFTS5MatchPredicate,
        )
        from rhosocial.activerecord.backend.impl.sqlite.protocols import SQLiteFTS5Support
    except ImportError as exc:
        pytest.skip(f"SQLite protocol not available: {exc}")

    dialect = SQLiteDialect()
    assert isinstance(dialect, SQLiteFTS5Support)
    node = SQLiteFTS5MatchPredicate(dialect, table="docs", query="hello")
    assert node.to_sql(dialect) == ('"docs" MATCH ?', ("hello",))


def test_every_registered_core_leaf_has_a_reachable_formatter():
    assert not _unreachable(core_registry(), DummyDialect())


def test_unreachable_formatter_is_detected():
    """A planted defect proves the check is not vacuous."""

    class _NoFormatter(BaseExpression):
        def __init__(self, dialect=None):
            super().__init__(dialect)

    class _Registry:
        @staticmethod
        def node_kinds():
            return ("no_formatter",)

        @staticmethod
        def resolve_node(kind):
            return _NoFormatter

    assert _unreachable(_Registry(), DummyDialect()) == ["no_formatter"]
