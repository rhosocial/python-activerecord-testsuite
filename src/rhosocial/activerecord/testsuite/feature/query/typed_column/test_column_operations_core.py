# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_column_operations_core.py
"""What ``Model.c.<field>`` can and cannot do, at the core level.

Each family's column class decides which operations exist (one operation group
per receiver family, attached to both the column and the value side), and this
file exercises that through the field proxy — the entry point a model actually
uses. Both halves are pinned:

* the operations a family offers are reachable and produce expressions;
* the operations it does not offer refuse *at construction*, not in SQL —
  ``created_at + created_at`` used to render ``"created" + "created"`` and
  fail only at the database, which is the failure mode the narrow classes
  exist to remove.

Only core classes are asserted here: no backend-specific wrappers, no rendered
SQL text (``LENGTH`` is ``LEN`` on one backend and ``lengthUTF8`` on another;
the gate is this file's subject, not the spelling). A backend whose table
answers no column class for an annotation — Firebird's ``dict`` is the
recorded case — skips the tests that need it.
"""

# src/rhosocial/activerecord/testsuite/feature/query/typed_column/test_column_operations_core.py
import datetime
from typing import ClassVar

import pytest

from rhosocial.activerecord.backend.expression import functions
from rhosocial.activerecord.backend.expression.core import IntegerValueExpression
from rhosocial.activerecord.backend.expression.operators import BinaryArithmeticExpression
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.model import ActiveRecord


@pytest.fixture
def model(dialect):
    """A model whose fields cover the core common types, bound to *dialect*.

    ``__backend__`` is set directly rather than by connecting: every assertion
    is on expression construction, so no database is needed.
    """

    class Operations(ActiveRecord):
        __table_name__ = "core_column_operations"
        __primary_key__: ClassVar[str] = "id"
        c: ClassVar[FieldProxy] = FieldProxy()

        id: int
        name: str
        age: int
        score: float
        payload: dict
        created: datetime.datetime
        flag: bool
        blob: bytes

    Operations.__backend__ = type("B", (), {"dialect": dialect})()
    return Operations


def _expression(result):
    """Assert *result* is an expression that can render, and hand it back."""
    assert callable(getattr(result, "to_sql", None)), f"{result!r} is not an expression"
    return result


def _skip_without_column_class(dialect, annotation):
    """Skip when this backend's table answers no class for *annotation*.

    A refusal is a legitimate answer (the resolution contract says so), and a
    contract about the core operation surface must not turn it into a failure
    on the backends that refuse.
    """
    if dialect.suggested_column_types().get(annotation) is None:
        pytest.skip(f"this backend answers no column class for {annotation!r}")


# ---------------------------------------------------------------------------
# The operations each family offers are reachable
# ---------------------------------------------------------------------------


def test_string_operations(model):
    assert _expression(model.c.name.upper())
    assert _expression(model.c.name.substr(1, 2))
    assert _expression(model.c.name.trim())
    assert _expression(model.c.name.like("%a%"))
    assert _expression(model.c.name.ilike("%a%"))


def test_string_to_integer_is_a_number_that_takes_arithmetic(model):
    """``length`` reads a string and gives a number; the number is an integer.

    And a number is not a string: this is where the old duplicated surface
    produced ``LENGTH(LENGTH(name))``, which constructed and failed only in
    SQL. The integer result offers arithmetic and comparison instead.
    """
    length = model.c.name.length()
    assert isinstance(length, IntegerValueExpression)
    assert _expression(length + 1)
    assert _expression(length * 2)
    assert _expression(length > 3)


def test_numeric_operations(model):
    assert _expression(model.c.age + 1)
    assert _expression(model.c.age * 2)
    assert _expression(model.c.age % 2)
    assert _expression(model.c.age.abs())
    assert _expression(model.c.age > 18)
    assert _expression(model.c.score.sqrt())
    assert _expression(model.c.score.round(2))
    assert _expression(model.c.score.exp())


def test_json_operations(model, dialect):
    _skip_without_column_class(dialect, dict)
    assert _expression(model.c.payload.json_path("a"))
    assert _expression(model.c.payload.json_value("a"))


def test_temporal_operations_and_interval_arithmetic(model, dialect):
    assert _expression(model.c.created.date_trunc("month"))
    assert _expression(model.c.created.extract("year"))
    assert _expression(model.c.created.date_add(1, "day"))
    one_day = functions.interval(dialect, 1, "day")
    shifted = model.c.created + one_day
    assert isinstance(shifted, BinaryArithmeticExpression)
    assert isinstance(model.c.created - model.c.created, BinaryArithmeticExpression)


def test_boolean_operations(model):
    assert _expression(model.c.flag.is_true())
    assert _expression(model.c.flag.is_false())


def test_binary_operations(model):
    assert _expression(model.c.blob == b"bytes")
    assert _expression(model.c.blob.is_not_null())


# ---------------------------------------------------------------------------
# The operations a family does not offer refuse at construction
# ---------------------------------------------------------------------------


def test_operations_of_another_family_are_missing(model):
    """A missing operation is an ``AttributeError``, the package's vocabulary."""
    with pytest.raises(AttributeError):
        model.c.age.like("%1%")  # LIKE belongs to strings
    with pytest.raises(AttributeError):
        model.c.age.upper()
    with pytest.raises(AttributeError, match="no sum"):
        model.c.created + model.c.created  # two points in time have no sum


def test_a_number_result_carries_no_string_operations(model):
    """``length`` returns a number, and the number is where the chain stops."""
    with pytest.raises(AttributeError):
        model.c.name.length().length()
    with pytest.raises(AttributeError):
        model.c.name.length().upper()


def test_arithmetic_a_string_never_declared_is_a_type_error(model):
    """String carries no arithmetic at all, so the interpreter refuses first.

    A family whose refusal is *declared* on the class raises
    ``AttributeError`` with a message (the temporal case above); a family
    that simply has no operator is refused by Python, which reports
    ``TypeError``. Both are construction-time refusals; the difference is
    which layer owns the message, and that is what the two tests pin.
    """
    with pytest.raises(TypeError):
        model.c.name + 1
