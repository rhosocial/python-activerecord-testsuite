# src/rhosocial/activerecord/testsuite/core/fixture_types.py
"""Generic column types for shared fixture tables.

The shared suite declares only *generic* type concepts and lets each backend's
dialect render them through its own ``format_data_type_<name>`` formatter.
Nothing in this module inspects a backend's name, and nothing here assumes a
backend-specific behaviour: a difference between servers belongs in that
server's dialect (or in that backend's own tests), never in the shared suite.

Column policy -- one concept per role:

* :func:`short_text` -- ``VARCHAR(255)``: the comparable-text concept used for
  identity-like columns (equality, ``ORDER BY``, ``GROUP BY``, ``DISTINCT``).
  It is a bounded string on purpose: an unbounded text type is not universally
  comparable, and the suite does not silently fall back to one. The dialect
  answers whether it renders ``varchar`` (:func:`require_data_type`); a dialect
  that does not answer is skipped.
* :func:`long_text` -- ``TEXT``: payload text that tests never compare.
* :func:`json_text` -- ``TEXT``: the shared suite carries JSON as text; native
  ``JSON``/``JSONB`` columns are backend-specific topics.
* :func:`array_text` -- ``TEXT``: array columns are backend-specific topics.
* :func:`date_type` / :func:`time_type` / :func:`timestamp_type` -- the generic
  temporal types.  No time-zone variant is used here: time-zone semantics are
  backend-specific topics.

``VARCHAR(255)`` is chosen because a column tests compare must be a bounded
string on every backend the suite runs on, and ten such columns stay inside the
tightest row-width limit the suite meets (MySQL's 65535 bytes at four bytes per
character). The bound belongs to the concept, not to any one server.
"""

from rhosocial.activerecord.backend.expression import (
    ColumnConstraint,
    ColumnDefinition,
    CreateTableStatement,
    DropTableStatement,
    TableConstraint,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnDefaultConstraint,
    ColumnNotNullConstraint,
    ColumnPrimaryKeyConstraint,
    TablePrimaryKeyConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    BlobType,
    BooleanType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    TextType,
    TimeType,
    TimestampType,
    VarCharType,
)

#: Bounded length for comparable text. 255 is chosen because every backend in
#: the suite renders a bounded VARCHAR of that width, and ten such columns stay
#: inside the smallest row-width limit the suite meets (MySQL's 65535 bytes is
#: the tightest at four bytes per character under utf8mb4). The bound is a
#: property of the shared concept, not of any one server.
SHORT_TEXT_LENGTH = 255


def require_data_type(dialect, concept: str) -> None:
    """Ask the dialect whether it supports a generic type concept.

    A dialect declares its supported type concepts through
    ``supports_data_types()`` (a formatter is the declaration of support).
    The shared suite renders only concepts the dialect answers for; a dialect
    that does not answer is skipped with a reason instead of building a column
    the server cannot honour. No backend name is consulted.
    """
    probe = getattr(dialect, "supports_data_types", None)
    if not callable(probe):
        return
    supported = probe() or {}
    if concept not in supported:
        import pytest

        pytest.skip(
            f"{getattr(dialect, 'name', 'this dialect')} does not support "
            f"the generic data type {concept!r}"
        )


#: Portable non-empty text used when a fixture column must have a DEFAULT.
#: The empty string is not portable (some servers store ``''`` as NULL),
#: and any non-empty value works on every server the suite runs on.
PLACEHOLDER_TEXT = "-"


def short_text(dialect):
    """Comparable text for identity-like columns.

    The concept is "a bounded string with equality and order" -- the only
    spelling every backend can honour for a column that tests compare, sort or
    group. An unbounded text type is *not* that concept: Oracle's CLOB and
    Firebird's BLOB have no value comparison, and silently substituting them
    would hide that gap. The dialect answers whether it renders ``varchar``
    (:func:`require_data_type`); a dialect that does not answer is skipped.
    """
    require_data_type(dialect, "varchar")
    return VarCharType(dialect, SHORT_TEXT_LENGTH)


def long_text(dialect):
    """Unbounded text payload; never compared or sorted."""
    return TextType(dialect)


def json_text(dialect):
    """JSON carried as text in the shared suite."""
    return TextType(dialect)


def array_text(dialect):
    """Array-valued fields carried as text in the shared suite."""
    return TextType(dialect)


def array_type(dialect, element_type):
    """The generic ``ARRAY`` type where the dialect renders it.

    ``ARRAY`` is a generic type concept, but not every server renders it: the
    dialect declares which type concepts it supports through
    ``supports_data_types()``.  Where it is not rendered, the column becomes
    the generic text carrier and the model's value adapter handles the
    conversion.  The dialect answers; no backend name is consulted.
    """
    probe = getattr(dialect, "supports_data_types", None)
    supported = probe() if callable(probe) else {}
    if "array" in supported:
        return ArrayType(dialect, element_type=element_type)
    return TextType(dialect)


def date_type(dialect):
    return DateType(dialect)


def time_type(dialect):
    return TimeType(dialect)


def timestamp_type(dialect):
    """Timestamp with microsecond resolution where the server declares it.

    The concept asked for is "a timestamp that keeps microseconds".  Whether
    that is expressible as a column parameter is the dialect's own answer:
    dialects whose server keeps microseconds natively declare it through
    ``supports_microsecond_timestamp()``; the rest get the plain generic
    ``TIMESTAMP`` (their value resolution is the server's documented one).
    No backend name is consulted, and no backend-specific assumption is made.
    """
    probe = getattr(dialect, "supports_microsecond_timestamp", None)
    keeps_microseconds = bool(probe()) if callable(probe) else bool(probe)
    return TimestampType(dialect, precision=6 if keeps_microseconds else None)


def supports_drop_if_exists(dialect) -> bool:
    """Whether this dialect can spell ``DROP TABLE IF EXISTS``.

    The dialect is the authority; a dialect that does not answer keeps the
    historical behaviour (``IF EXISTS``), because the directory owns its tables
    and they are present whenever teardown runs after a successful prepare.
    """
    probe = getattr(dialect, "supports_if_exists_table", None)
    return True if probe is None else bool(probe())


def drop_table(dialect, table_name: str):
    """The fixture-owned DROP expression for one of the shared tables."""
    return DropTableStatement(
        dialect,
        Table(dialect, table_name),
        if_exists=supports_drop_if_exists(dialect),
    )


__all__ = [
    "BlobType",
    "BooleanType",
    "ColumnConstraint",
    "ColumnDefaultConstraint",
    "ColumnDefinition",
    "ColumnNotNullConstraint",
    "ColumnPrimaryKeyConstraint",
    "CreateTableStatement",
    "DateType",
    "DecimalType",
    "DoubleType",
    "FloatType",
    "IntegerType",
    "PLACEHOLDER_TEXT",
    "TableConstraint",
    "TablePrimaryKeyConstraint",
    "TextType",
    "TimeType",
    "TimestampType",
    "VarCharType",
    "array_text",
    "date_type",
    "drop_table",
    "json_text",
    "long_text",
    "short_text",
    "supports_drop_if_exists",
    "time_type",
    "timestamp_type",
]
