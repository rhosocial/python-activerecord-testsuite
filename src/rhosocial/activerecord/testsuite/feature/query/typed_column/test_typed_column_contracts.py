# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_typed_column_contracts.py
"""Type-narrowed columns must behave identically on every backend.

The point of narrowing a column by its field's Python annotation is that the
*same model code* behaves the same everywhere. A backend that renamed a class,
returned a different base, or rendered different SQL would break that
promise while still passing its own dialect tests, so these contracts run
against every backend.

Nothing here needs a live database: every assertion is on the expression tree
or on SQL produced from a dialect that was never connected to.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_typed_column_contracts.py
import datetime
import decimal
import uuid
from typing import Optional

import pytest

from rhosocial.activerecord.backend.expression import (
    ArrayColumn,
    BinaryColumn,
    BooleanColumn,
    Column,
    ColumnBase,
    DateTimeColumn,
    JSONColumn,
    NumericColumn,
    StringColumn,
    UUIDColumn,
    build_json_path,
)
from rhosocial.activerecord.base.column_dispatch import build_column, column_class_for


@pytest.fixture
def dialect(request):
    """The dialect under test, taken from a provider-configured model.

    Read off ``__backend__`` rather than calling ``Model.backend()``. The
    latter resolves the *currently active* backend and raises "No backend
    configured" on shards that have no live connection, which is exactly the
    case here: every assertion below is on an expression tree or on SQL from a
    dialect that was never connected. ``__backend__`` is the provider's
    configured instance and needs no connection.

    The model is requested through ``getfixturevalue`` so the existing fixture
    keeps ownership of scenario setup and teardown.
    """
    model = request.getfixturevalue("json_user_fixture")
    return model.__backend__.dialect


# ---------------------------------------------------------------------------
# Class identity is backend-independent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (str, StringColumn),
        (int, NumericColumn),
        (float, NumericColumn),
        (decimal.Decimal, NumericColumn),
        (bool, BooleanColumn),
        (bytes, BinaryColumn),
        (dict, JSONColumn),
        (list, ArrayColumn),
        (datetime.datetime, DateTimeColumn),
        (datetime.date, DateTimeColumn),
        (uuid.UUID, UUIDColumn),
    ],
    ids=lambda v: getattr(v, "__name__", str(v)),
)
def test_typed_column_class_is_backend_independent(dialect, annotation, expected):
    """The annotation decides the class, never the dialect.

    This is the contract that makes a model portable: if a backend could
    return a different class here, the same field would offer different
    operators depending on where it ran.
    """
    assert column_class_for(annotation) is expected
    assert type(build_column(dialect, "f", annotation)) is expected


@pytest.mark.parametrize(
    "annotation", [Optional[str], Optional[dict], Optional[int]]
)
def test_optional_is_transparent(dialect, annotation):
    """``Optional[T]`` must narrow exactly as ``T`` does."""
    inner = {
        Optional[str]: StringColumn,
        Optional[dict]: JSONColumn,
        Optional[int]: NumericColumn,
    }[annotation]
    assert type(build_column(dialect, "f", annotation)) is inner


@pytest.mark.parametrize(
    "column_class",
    [
        Column,
        StringColumn,
        NumericColumn,
        DateTimeColumn,
        BooleanColumn,
        BinaryColumn,
        UUIDColumn,
        JSONColumn,
        ArrayColumn,
    ],
    ids=lambda c: c.__name__,
)
def test_every_column_class_shares_one_base(dialect, column_class):
    """The eight isinstance() consumers test for ColumnBase, so all must match.

    A class that slipped out of the hierarchy would be silently rejected by
    whichever consumer met it first — a RETURNING clause, an UPDATE SET, an
    upsert — and the symptom would look like an unrelated backend bug.
    """
    assert isinstance(column_class(dialect, "c"), ColumnBase)


def test_the_permissive_column_stays_permissive(dialect):
    """The hand-built ``Column`` is the escape hatch and must not narrow."""
    col = Column(dialect, "anything")
    for operation in ("like", "ilike", "json_path", "__add__", "__mul__"):
        assert hasattr(col, operation), f"Column lost {operation}"


def test_narrowing_actually_narrows(dialect):
    """The narrowed classes must not leak operations they cannot support."""
    assert hasattr(build_column(dialect, "s", str), "like")
    assert not hasattr(build_column(dialect, "s", str), "__add__")

    assert hasattr(build_column(dialect, "n", int), "__add__")
    assert not hasattr(build_column(dialect, "n", int), "like")

    assert hasattr(build_column(dialect, "j", dict), "json_path")
    assert not hasattr(build_column(dialect, "j", dict), "like")
    assert not hasattr(build_column(dialect, "j", dict), "__add__")


# ---------------------------------------------------------------------------
# Rendering is unchanged by narrowing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "column_class",
    [
        Column,
        StringColumn,
        NumericColumn,
        DateTimeColumn,
        BooleanColumn,
        BinaryColumn,
        UUIDColumn,
        JSONColumn,
        ArrayColumn,
    ],
    ids=lambda c: c.__name__,
)
def test_rendering_is_identical_across_column_classes(dialect, column_class):
    """Narrowing changed the API surface, not the SQL."""
    col = column_class(dialect, "settings", table="t", schema_name="s")
    assert col.to_sql() == (f'{dialect.format_identifier("s")}.'
                            f'{dialect.format_identifier("t")}.'
                            f'{dialect.format_identifier("settings")}', ())


def test_qualified_and_aliased_forms(dialect):
    ident = dialect.format_identifier
    assert Column(dialect, "c").to_sql() == (ident("c"), ())
    assert Column(dialect, "c", table="t").to_sql() == (
        f'{ident("t")}.{ident("c")}',
        (),
    )
    assert Column(dialect, "c", alias="a").to_sql() == (
        f'{ident("c")} AS {ident("a")}',
        (),
    )


# ---------------------------------------------------------------------------
# JSON path building is one shared implementation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "keys, expected",
    [
        (("a",), "$.a"),
        (("a", "b"), "$.a.b"),
        (("tags", 0), "$.tags[0]"),
        (("a", 0, "b"), "$.a[0].b"),
        (("tags", "[0]"), "$.tags[0]"),
    ],
    ids=lambda v: str(v),
)
def test_json_path_is_built_the_same_everywhere(keys, expected):
    """Path syntax must not vary per backend — it is one function."""
    assert build_json_path(*keys) == expected


def test_int_index_and_str_key_stay_distinct():
    """``"0"`` names a key; only an int is an index.

    ``$.tags.0`` matches nothing, so the distinction rides on the type rather
    than the spelling.
    """
    assert build_json_path("tags", "0") == "$.tags.0"
    assert build_json_path("tags", 0) == "$.tags[0]"


def test_bool_is_rejected_as_a_path_segment():
    """bool subclasses int, so True would silently become index 1."""
    with pytest.raises(TypeError, match="bool"):
        build_json_path("a", True)


def test_json_chaining_does_not_renest_the_path(dialect):
    """Chaining accumulates into one path per step, never ``$``-anchored again.

    Re-anchoring would make ``col.json_value("a").json_value("b")`` read
    ``b`` from the document root instead of from ``a``.
    """
    col = build_column(dialect, "settings", dict)
    chained = col.json_value("a").json_value("b").to_sql()[0]
    assert chained.count("$") == 2
    assert "$." not in chained.replace("$.a", "").replace("$.b", "")
