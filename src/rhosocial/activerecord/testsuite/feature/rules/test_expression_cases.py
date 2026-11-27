# src/rhosocial/activerecord/testsuite/feature/rules/test_expression_cases.py
"""Formal source: capability §3.1 and families §6.1.

Every concrete expression falls into exactly one case: reuse of a core node,
derivation that adds parameters to a core node, or a self-named proprietary
node. §6.1 makes the three mutually exclusive and decidable by three questions
("is it in core? is it a core subclass with extra params? is it backend-named
with no core counterpart?"). §3.1 adds that a derivative depends on core one
way only. Classification below uses ``issubclass``, module names and signatures
-- never ``getattr`` / ``hasattr`` on an expression node.
"""

import inspect

import pytest

from rhosocial.activerecord.backend.expression.bases import BaseExpression

_CORE = "rhosocial.activerecord.backend.expression"
_REUSE = "reuse"
_DERIVE = "derive"
_PROPRIETARY = "proprietary"


def _concrete_core_ancestor(cls):
    """The nearest core ancestor that itself declares a formatter.

    Shared bases such as ``SQLPredicate`` carry no ``format_method``; a node
    inheriting only those has no core counterpart, which is §6.1's proprietary
    case even when it subclasses a generic base.
    """
    for base in cls.__mro__[1:]:
        if base is object or base is BaseExpression:
            continue
        if base.__module__.startswith(_CORE) and "format_method" in vars(base):
            return base
    return None


def _case(cls):
    """§6.1's decision, returning exactly one of the three labels."""
    if cls.__module__.startswith(_CORE):
        return _REUSE
    base = _concrete_core_ancestor(cls)
    if base is None:
        return _PROPRIETARY
    own = set(inspect.signature(cls.__init__).parameters) - {"self", "dialect"}
    inherited = set(inspect.signature(base.__init__).parameters) - {"self", "dialect"}
    return _DERIVE if own > inherited else _REUSE


@pytest.fixture
def sqlite_nodes():
    """A real backend's three cases; skip where SQLite is not installed."""
    try:
        from rhosocial.activerecord.backend.impl.sqlite.expression.fts5 import (
            SQLiteFTS5MatchPredicate,
        )
        from rhosocial.activerecord.backend.impl.sqlite.expression.types import (
            SQLiteNumericType,
        )
    except ImportError as exc:
        pytest.skip(f"SQLite expression package not available: {exc}")
    from rhosocial.activerecord.backend.expression.core import Literal

    return {
        _REUSE: Literal,
        _DERIVE: SQLiteNumericType,
        _PROPRIETARY: SQLiteFTS5MatchPredicate,
    }


def test_each_case_is_decidable(sqlite_nodes):
    for label, cls in sqlite_nodes.items():
        assert _case(cls) == label, (label, cls.__name__)


def test_derived_adds_parameters_and_keeps_the_core_ones(sqlite_nodes):
    """§3.1: 派生增参，原参数不动."""
    derived = sqlite_nodes[_DERIVE]
    base = _concrete_core_ancestor(derived)
    assert base is not None and base.__module__.startswith(_CORE)
    own = set(inspect.signature(derived.__init__).parameters) - {"self", "dialect"}
    inherited = set(inspect.signature(base.__init__).parameters) - {"self", "dialect"}
    assert own - inherited, "a derivation must add backend parameters"
    assert inherited <= own, "a derivation may not drop core parameters"


def test_proprietary_has_no_concrete_core_ancestor(sqlite_nodes):
    assert _concrete_core_ancestor(sqlite_nodes[_PROPRIETARY]) is None
    assert sqlite_nodes[_PROPRIETARY].kind().startswith("sqlite_")


def test_the_three_labels_are_mutually_exclusive(sqlite_nodes):
    labels = {_case(cls) for cls in sqlite_nodes.values()}
    assert labels == {_REUSE, _DERIVE, _PROPRIETARY}
