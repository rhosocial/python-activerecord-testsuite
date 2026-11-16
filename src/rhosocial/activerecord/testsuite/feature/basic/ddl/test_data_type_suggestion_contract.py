# src/rhosocial/activerecord/testsuite/feature/basic/ddl/test_data_type_suggestion_contract.py
"""The suggested-data-type tables: the framework's promise, and the backend's own.

Two tables sit behind a bare field's declaration:

* ``suggested_data_types()`` answers the framework's closed list of modelled
  Python types (``FRAMEWORK_PYTHON_TYPES``). The promise is that a field which
  writes only a Python type always has a declaration, so every entry is
  answered with a ``DataType`` the dialect can spell -- ``None`` is not an
  answer here.
* ``suggested_extra_data_types()`` answers the backend's **own** value classes
  (a hstore, an SDO geometry, an interval wrapper). Its key space is the
  backend's, which is why it may not overlap the framework list: an overlap
  would make "the framework answers this" and "this backend answers this"
  indistinguishable at the call site.

Each call returns a fresh dict: the values are the dialect's read-only
templates, and a caller binds a rendering on a copy of the entry it uses.

The third obligation for an extra entry -- that its key has an adapter, so a
written value comes back -- is asserted in the backend's own suite, where the
adapter registry is reachable from a backend fixture.
"""

from typing import Any

import pytest

from rhosocial.activerecord.base.framework_types import FRAMEWORK_PYTHON_TYPES


def test_every_framework_type_is_answered(ddl_dialect):
    """A hole is a lie told to the model layer, so the list is walked, not read."""
    table = ddl_dialect.suggested_data_types()
    missing = [entry for entry in FRAMEWORK_PYTHON_TYPES if entry not in table]

    assert not missing, (
        f"{type(ddl_dialect).__name__}.suggested_data_types() leaves "
        f"{len(missing)} framework-modelled type(s) unanswered: "
        f"{[getattr(entry, '__name__', entry) for entry in missing]}. "
        f"Answer each with a DataType the dialect renders."
    )


def test_no_framework_type_is_left_without_a_declaration(ddl_dialect):
    """A suggestion is what a bare field gets; ``None`` would take the table
    away from the caller rather than state a limitation."""
    unanswered = [
        getattr(entry, "__name__", entry)
        for entry, suggestion in ddl_dialect.suggested_data_types().items()
        if suggestion is None
    ]

    assert unanswered == [], (
        f"{type(ddl_dialect).__name__} answers None for {unanswered}; a bare field "
        f"must still have a declaration here (a precise spelling is UseSqlType's job)."
    )


def test_every_suggested_declaration_renders(ddl_dialect):
    """A suggestion the renderer cannot keep is worse than none: the caller
    finds out at CREATE TABLE instead of here."""
    for entry, suggestion in ddl_dialect.suggested_data_types().items():
        if suggestion is None:
            continue  # covered by the previous contract, not by this one
        ddl_dialect.format_data_type(suggestion)


def test_each_call_returns_a_new_table(ddl_dialect):
    first = ddl_dialect.suggested_data_types()
    second = ddl_dialect.suggested_data_types()

    assert first is not second
    assert first == second


def test_the_extra_table_is_disjoint_from_the_framework_list(ddl_dialect):
    """The backend's own keys are its own; the framework list is not theirs to
    answer again."""
    extras: Any = ddl_dialect.suggested_extra_data_types()

    assert set(extras).isdisjoint(set(FRAMEWORK_PYTHON_TYPES))


def test_every_extra_answer_is_a_renderable_declaration(ddl_dialect):
    for entry, suggestion in ddl_dialect.suggested_extra_data_types().items():
        assert suggestion is not None, (
            f"{type(ddl_dialect).__name__} declares {getattr(entry, '__name__', entry)!r} "
            f"as an own value class but suggests no declaration for it"
        )
        ddl_dialect.format_data_type(suggestion)


def test_the_extra_table_is_consistent_across_calls(ddl_dialect):
    first = ddl_dialect.suggested_extra_data_types()
    second = ddl_dialect.suggested_extra_data_types()

    assert first is not second
    assert first == second
