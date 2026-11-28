# src/rhosocial/activerecord/testsuite/feature/rules/contracts/registry.py
"""The registry contract every backend's published expression table must meet.

A backend publishes two data values: its own ``kind -> fully qualified class
name`` mapping, and a frozen registry built by merging core's mapping with its
own. The table is the name authority a read uses, so its shape is a rule, not a
backend-specific detail: core kinds plus the owner's, never a sibling's; every
target a resolvable class whose ``kind()`` is the key; ``parameter`` is the one
value node.

Only owners import this module: core's generic layer never publishes a backend
table, so it has no ``registry`` fixture to supply.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from .subject import ExpressionSubject

_CORE_REGISTRY_MODULE = "rhosocial.activerecord.backend.expression_registry"


def _core_expressions() -> dict:
    return importlib.import_module(_CORE_REGISTRY_MODULE).CORE_EXPRESSIONS


def _own_expressions(subject: ExpressionSubject) -> dict:
    module = importlib.import_module(f"{subject.impl_module_prefix}.expression_registry")
    return vars(module)[f"{subject.prefix.upper()}_EXPRESSIONS"]


def _sibling_only_kinds() -> set:
    core = set(_core_expressions())
    kinds = set()
    for name in ("sqlite", "dummy"):
        module = importlib.import_module(
            f"rhosocial.activerecord.backend.impl.{name}.expression_registry"
        )
        kinds |= set(vars(module)[f"{name.upper()}_EXPRESSIONS"])
    return kinds - core


def test_registry_is_frozen(registry: Any) -> None:
    """A published table is a value; no reader may narrow it for everyone."""
    assert registry.is_frozen
    with pytest.raises(Exception) as caught:
        registry.register_node(type("Fake", (), {"kind": staticmethod(lambda: "fake")}))
    assert "frozen" in str(caught.value).lower()


def test_registry_publishes_core_plus_own_kinds(
    registry: Any, subject: ExpressionSubject
) -> None:
    expected = set(_core_expressions()) | set(_own_expressions(subject))
    assert set(registry.node_kinds()) == expected


def test_registry_publishes_no_sibling_backend_kind(registry: Any) -> None:
    """Installing a sibling must not make its kinds readable here."""
    sibling_only = _sibling_only_kinds()
    assert sibling_only
    assert set(registry.node_kinds()).isdisjoint(sibling_only)


def test_every_target_resolves_to_its_own_class(
    registry: Any, subject: ExpressionSubject
) -> None:
    """A stale FQN is a defect, not an artifact that happens to fail at read."""
    from rhosocial.activerecord.backend.expression.core import Parameter

    assert registry.resolve_node("parameter") is Parameter
    for kind, target in _own_expressions(subject).items():
        cls = registry.resolve_node(kind)
        assert f"{cls.__module__}.{cls.__qualname__}" == target
        assert cls.kind() == kind


def test_no_value_kind_is_published(registry: Any) -> None:
    """Values are carried by ``parameter``; every other kind is a node kind."""
    from rhosocial.activerecord.backend.expression.core import Parameter

    answering = [kind for kind in registry.node_kinds() if registry.resolve_node(kind) is Parameter]
    assert answering == ["parameter"]
