# src/rhosocial/activerecord/testsuite/feature/basic/ddl/test_create_table_layout_contract.py
"""The create-table layout suggestion: every backend that implements the
protocol must answer a frozen, self-consistent value.

Backends that do not implement the protocol are structurally skipped (no false
requirement), mirroring the other suggestion contracts.
"""
import dataclasses

import pytest

from rhosocial.activerecord.backend.suggestion.protocols import (
    CreateTableLayoutSuggestionSupport,
)


def test_layout_suggestion_is_frozen_value(ddl_dialect):
    if not isinstance(ddl_dialect, CreateTableLayoutSuggestionSupport):
        pytest.skip("dialect has no create-table layout suggestion protocol")
    layout = ddl_dialect.suggest_create_table_layout()
    assert dataclasses.is_dataclass(layout)
    assert layout.state in ("actions", "unsupported", "no-action", "no-protocol")
    assert layout.strategy in ("single", "split")


def test_layout_flags_consistent_with_strategy(ddl_dialect):
    if not isinstance(ddl_dialect, CreateTableLayoutSuggestionSupport):
        pytest.skip("dialect has no create-table layout suggestion protocol")
    layout = ddl_dialect.suggest_create_table_layout()
    if layout.state != "actions":
        return
    # A "single" layout must actually allow inlining both optional clauses;
    # a "split" layout reports at least one of them as non-inline.
    if layout.strategy == "single":
        assert layout.inline_index is True
        assert layout.inline_comment is True
    else:
        assert not (layout.inline_index and layout.inline_comment)


def test_layout_matches_capability_switches(ddl_dialect):
    """The suggestion must agree with the dialect's rendering capability gates."""
    if not isinstance(ddl_dialect, CreateTableLayoutSuggestionSupport):
        pytest.skip("dialect has no create-table layout suggestion protocol")
    layout = ddl_dialect.suggest_create_table_layout()
    if layout.state != "actions":
        return
    inline_idx = getattr(ddl_dialect, "supports_inline_index", None)
    inline_cmt = getattr(ddl_dialect, "supports_table_comment", None)
    if callable(inline_idx):
        assert layout.inline_index == inline_idx()
    if callable(inline_cmt):
        assert layout.inline_comment == inline_cmt()
