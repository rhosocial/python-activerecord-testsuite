# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_typed_column_contracts.py
"""Type-narrowed columns must behave identically on every backend.

The point of narrowing a column by its field's Python annotation is that the
*same model code* behaves the same everywhere. A backend that renamed a class,
returned a different base, or rendered different SQL would break that
promise while still passing its own dialect tests, so these contracts run
against every backend.

Nothing here needs a live database: every assertion is on the expression tree
or on SQL produced from a dialect that was never connected to.

Two contracts, not one
----------------------
Which column class an annotation means is the **backend's answer** (through
the ``ColumnTypeSupport`` tables), so "the class is backend-independent" holds
only for explicit declarations:

* an **explicit** ``UseColumnType(SomeColumn)`` is backend-independent by
  contract -- naming a class is a statement about operations, and the
  operations are the same everywhere. A backend that disagreed here would be
  changing what a column class *means*, which the typed_column contracts
  forbid everywhere;
* **inference** is per backend. Each dialect's ``suggested_column_types()`` is
  the authority, and what the selection builds must equal that table's answer
  for the annotation. A backend that suggests ``ArrayColumn`` for ``list``
  where another suggests ``JSONColumn`` is not breaking a contract -- it is
  reporting a real difference in what those servers can do.

The inference cases below use *exact* table keys (``str`` is the ``str``
entry), so comparing against the table by key does not restate the
normalisation rules.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_typed_column_contracts.py
import datetime
import decimal
import uuid
from typing import Any, Optional

import pytest

from rhosocial.activerecord.backend.expression import (
    ArrayColumn,
    BinaryColumn,
    BooleanColumn,
    Column,
    ColumnBase,
    DateTimeColumn,
    IntegerColumn,
    JSONColumn,
    NumericColumn,
    StringColumn,
    UUIDColumn,
    build_json_path,
)
from rhosocial.activerecord.base.fields import UseColumnType

from rhosocial.activerecord.testsuite.feature.query.typed_column.column_helpers import (
    build_column,
)


def _class_or_skip(dialect, annotation, column_name):
    """The class this dialect answers for *annotation*, or a skip when it refuses.

    ``None`` is a legitimate answer -- the backend genuinely has no column for
    the value, and the field needs an explicit declaration -- so a test about
    the class *surface* skips rather than fails. A *missing* key is different:
    that is an omission, whatever the reason, and it fails here.

    The annotation is used as an exact table key (``str`` is the ``str``
    entry); these callers pass the very types the table is keyed by.
    """
    table = dialect.suggested_column_types()
    assert annotation in table, (
        f"{type(dialect).__name__}.suggested_column_types() does not answer "
        f"for {annotation!r}; every common entry must be answered (see "
        f"test_protocol_guarantees.py)."
    )
    if table[annotation] is None:
        pytest.skip(f"{type(dialect).__name__} reports no column class for {annotation!r}")
    return build_column(dialect, column_name, annotation)


# ---------------------------------------------------------------------------
# Contract 1: an explicit declaration is backend-independent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "annotation, column_class",
    [
        (str, StringColumn),
        (int, IntegerColumn),
        (dict, JSONColumn),
        (list, ArrayColumn),
        (uuid.UUID, UUIDColumn),
        (datetime.datetime, DateTimeColumn),
    ],
    ids=lambda v: getattr(v, "__name__", str(v)),
)
def test_an_explicit_declaration_is_the_same_class_everywhere(dialect, annotation, column_class):
    """``UseColumnType(X)`` means ``X`` on every backend, whatever the annotation.

    This is the contract that makes a model portable, and it survives the move
    of inference onto the backend's tables: naming a class says which operations
    the value carries, and those are the same on every backend. A backend that
    answered anything else here would be redefining a column class rather than
    reporting what it can do -- and the annotation is deliberately *not* the one
    the class belongs to, so nothing about the backend's table can leak into the
    answer.
    """
    declared = UseColumnType(column_class)
    assert type(build_column(dialect, "f", annotation, column_type=declared)) is column_class


def test_a_declaration_overrides_an_annotation_the_backend_cannot_place(dialect):
    """The escape hatch works even where the backend's own answer is absent.

    Declaring is the route past a table answering ``None``, so it has to reach
    resolution before the table is consulted -- which is also what makes it
    usable for a backend that has no native column for the annotation.
    """
    declared = UseColumnType(JSONColumn)
    assert type(build_column(dialect, "f", dict, column_type=declared)) is JSONColumn


# ---------------------------------------------------------------------------
# Contract 2: inference follows this backend's own table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "annotation",
    [
        str,
        int,
        float,
        decimal.Decimal,
        bool,
        bytes,
        dict,
        list,
        datetime.datetime,
        datetime.date,
        uuid.UUID,
    ],
    ids=lambda v: getattr(v, "__name__", str(v)),
)
def test_inference_matches_this_backends_own_table(dialect, annotation):
    """What a model builds is what this dialect's table says, not a fixed class.

    The assertion is table-relative on purpose. Pinning each annotation to one
    class across all backends was the old contract, and it was wrong: seven
    backends carry ``list`` as a JSON document while PostgreSQL has a real array
    type, and both are correct answers to "what can this value do here". What is
    *not* negotiable is that the selection and the table agree -- otherwise the
    table is documentation rather than the source of the answer.
    """
    table = dialect.suggested_column_types()
    assert annotation in table, (
        f"{type(dialect).__name__}.suggested_column_types() does not answer "
        f"for {annotation!r}; every common entry must be answered (see "
        f"test_protocol_guarantees.py)."
    )

    expected = table[annotation]
    if expected is None:
        pytest.skip(f"{type(dialect).__name__} reports no column class for {annotation!r}")

    assert type(build_column(dialect, "f", annotation)) is expected


@pytest.mark.parametrize("annotation", [Optional[str], Optional[dict], Optional[int]])
def test_optional_is_transparent(dialect, annotation):
    """``Optional[T]`` must resolve exactly as ``T`` does on this backend.

    Compared against the same dialect's own answer for ``T`` rather than against
    a class, for the same reason the inference contract above is: the answer may
    legitimately vary by backend, and what must not vary is the *effect* of
    wrapping the annotation in ``Optional``.
    """
    inner = {
        Optional[str]: str,
        Optional[dict]: dict,
        Optional[int]: int,
    }[annotation]
    resolved = _class_or_skip(dialect, inner, "f")
    assert type(build_column(dialect, "f", annotation)) is type(resolved)


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
    """The hand-built ``Column`` is the escape hatch and must not narrow.

    Retiring it as the framework's *fallback* did not retire the class: a caller
    with a bare column name still reaches for it, and it is now reachable through
    a declaration rather than by accident.
    """
    col = Column(dialect, "anything")
    for operation in ("like", "ilike", "json_path", "__add__", "__mul__"):
        assert hasattr(col, operation), f"Column lost {operation}"

    # ...and a model that declares it gets it, narrow nothing implied.
    declared = build_column(dialect, "anything", Any, column_type=UseColumnType(Column))
    assert type(declared) is Column


def test_narrowing_actually_narrows(dialect):
    """The narrowed classes must not leak operations they cannot support.

    Built through the backend's own table, so this also says the operations
    follow from the class the backend chose rather than from the annotation: a
    backend that suggests ``StringColumn`` for an ``int`` field would offer
    ``like()`` on it, and that is a fact about the pairing, not about this
    contract.
    """
    string_column = _class_or_skip(dialect, str, "s")
    assert hasattr(string_column, "like")
    assert not hasattr(string_column, "__add__")

    integer_column = _class_or_skip(dialect, int, "n")
    assert hasattr(integer_column, "__add__")
    assert not hasattr(integer_column, "like")

    json_column = _class_or_skip(dialect, dict, "j")
    assert hasattr(json_column, "json_path")
    assert not hasattr(json_column, "like")
    assert not hasattr(json_column, "__add__")


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
    """Narrowing changed the API surface, not the SQL.

    Compared against a plain Column on the same dialect rather than against a
    hardcoded string: how a backend qualifies a name is its own business, and
    BigQuery renders a path as one quoted identifier where most render three.
    The invariant under test is that the typed layers render exactly what the
    untyped one does.
    """
    typed = column_class(dialect, "settings", table="t", schema_name="s")
    plain = Column(dialect, "settings", table="t", schema_name="s")
    assert typed.to_sql() == plain.to_sql()


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
    col = _class_or_skip(dialect, dict, "settings")
    chained = col.json_value("a").json_value("b").to_sql()[0]
    assert chained.count("$") == 2
    assert "$." not in chained.replace("$.a", "").replace("$.b", "")
