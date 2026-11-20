# src/rhosocial/activerecord/testsuite/feature/basic/expressions/expression_support.py
"""DB-free probe tables and helpers shared by the paired expression tests.

Everything here reads a dialect's static column-class answer or builds an
expression tree; nothing opens a connection. Kept in one module so the sync
and async halves cannot drift in what they assert (P4).
"""

from datetime import datetime
from decimal import Decimal

import pytest
from rhosocial.activerecord.backend.adapters import Geometry, MacAddress, Vector
from rhosocial.activerecord.backend.expression import Literal

#: X1: (family, column-class table key, existing model, field). The key is the
#: framework family in ``suggested_column_types()``; a field whose Python type
#: is a subclass (Point -> Geometry) names its family key here. ``None`` answers
#: are handled at runtime by :func:`column_class_for`.
X1_CASES = (
    ("integer", int, "TypedUser", "count"),
    ("string", str, "TypedUser", "label"),
    ("timestamp", datetime, "TypedUser", "seen_at"),
    ("number", Decimal, "TypedUser", "amount"),
    ("boolean", bool, "TypedUser", "flag"),
    ("json", dict, "ComplexRow", "payload"),
    ("array", list, "ComplexRow", "tags"),
    ("geometry", Geometry, "ComplexRow", "location"),
    ("vector", Vector, "ComplexRowAnnotated", "heading"),
    ("mac", MacAddress, "ComplexRow", "nic"),
)

#: X2: one renderable operation per value family. ``kind`` selects how the
#: expression is built from the class the dialect answered.
OPERATIONS = (
    ("integer", int, "arithmetic"),
    ("string", str, "like"),
    ("timestamp", datetime, "comparison"),
    ("json", dict, "json_path"),
    ("array", list, "element"),
    ("geometry", Geometry, "first"),
    ("vector", Vector, "first"),
)

#: X5: sync/async twins from the existing fixture models, sharing one field mixin.
TWINS = (
    ("count", "TypedUser", "AsyncTypedUser"),
    ("label", "TypedUser", "AsyncTypedUser"),
    ("seen_at", "TypedUser", "AsyncTypedUser"),
    ("payload", "ComplexRow", "AsyncComplexRow"),
    ("tags", "ComplexRow", "AsyncComplexRow"),
    ("location", "ComplexRow", "AsyncComplexRow"),
    ("heading", "ComplexRowAnnotated", "AsyncComplexRowAnnotated"),
    ("markup", "ComplexRowAnnotated", "AsyncComplexRowAnnotated"),
)

#: Candidates for a family's "first operation", specific before generic. The
#: surface-only classes (geometry, vector, ...) land on ``is_null``; a backend
#: that models a richer class gets the first family operation it offers.
_FIRST_OP_CANDIDATES = (
    ("array_length", ()),
    ("unnest", ()),
    ("json_path", ("k",)),
    ("like", ("%probe%",)),
    ("is_null", ()),
)


def column_class_for(dialect, key, family):
    """The dialect's answered column class, with X6's two cases made explicit.

    A missing key is a dialect gap and fails; a present key answered ``None``
    means "no operation class" and skips with a reason that names both the
    dialect and the value family (README sections 9 and 12, X6).
    """
    table = dialect.suggested_column_types()
    if key not in table:
        pytest.fail(
            "{} 的 suggested_column_types() 漏答 {}（键 {!r}）：漏答是失败，不是跳过".format(
                getattr(dialect, "name", type(dialect).__name__), family, key
            )
        )
    column_class = table[key]
    if column_class is None:
        pytest.skip(
            "{} 对 {} 没有运算类".format(getattr(dialect, "name", type(dialect).__name__), family)
        )
    return column_class


def first_renderable(column, dialect):
    """The first operation on *column* that produces renderable SQL."""
    for name, args in _FIRST_OP_CANDIDATES:
        operation = getattr(column, name, None)
        if not callable(operation):
            continue
        try:
            expression = operation(*args)
        except Exception:  # an op that needs different arguments is not offered
            continue
        if callable(getattr(expression, "to_sql", None)):
            return name, expression
    raise AssertionError("{} offers no renderable operation".format(type(column).__name__))


def _require_json_path(dialect):
    """Skip when the dialect cannot render a JSON path at all.

    A dialect may answer a column class for the json/array families while its
    server has no path function -- in that case the column's ``json_path``
    renders by raising UnsupportedFeatureError, which is an answered refusal,
    not a defect.  Ask the same switch that refusal consults.
    """
    switch = getattr(dialect, "supports_json_path", None)
    if callable(switch) and not switch():
        pytest.skip(
            "{} 不支持 JSON path 运算".format(
                getattr(dialect, "name", type(dialect).__name__)
            )
        )


def positive_expression(kind, column, dialect):
    """Build the X2 operation of *kind* on *column*, using *dialect* for literals."""
    if kind == "arithmetic":
        return column + Literal(dialect, 1)
    if kind == "like":
        return column.like("%probe%")
    if kind == "comparison":
        return column < Literal(dialect, "2100-01-01")
    if kind == "json_path":
        _require_json_path(dialect)
        return column.json_path("k")
    if kind == "element":
        # A native array exposes array operations; a backend with no array
        # type answers list with JSONColumn, whose element access is a path.
        if hasattr(column, "array_length"):
            return column.array_length()
        if hasattr(column, "unnest"):
            return column.unnest()
        if hasattr(column, "json_path"):
            _require_json_path(dialect)
            return column.json_path(0)
        raise AssertionError("{} has no element operation".format(type(column).__name__))
    if kind == "first":
        return first_renderable(column, dialect)[1]
    raise AssertionError("unknown operation kind: {}".format(kind))
