# src/rhosocial/activerecord/testsuite/core/fixture_types.py
"""Generic column types for shared fixture tables.

The shared suite declares only *generic* type concepts and lets each backend's
dialect render them through its own ``format_data_type_<name>`` formatter.
Nothing in this module inspects a backend's name, and nothing here assumes a
backend-specific behaviour: a difference between servers belongs in that
server's dialect (or in that backend's own tests), never in the shared suite.

Column policy -- one concept per role:

* :func:`short_text` -- ``VARCHAR(2000)``: identity-like text that is compared,
  sorted or grouped (equality, ``ORDER BY``, ``GROUP BY``, ``DISTINCT``).
* :func:`long_text` -- ``TEXT``: payload text that tests never compare.
* :func:`json_text` -- ``TEXT``: the shared suite carries JSON as text; native
  ``JSON``/``JSONB`` columns are backend-specific topics.
* :func:`array_text` -- ``TEXT``: array columns are backend-specific topics.
* :func:`date_type` / :func:`time_type` / :func:`timestamp_type` -- the generic
  temporal types.  No time-zone variant is used here: time-zone semantics are
  backend-specific topics.

``VARCHAR(2000)`` is chosen because it is renderable by every backend the suite
runs on and fits the smallest row-size limits (Oracle ``VARCHAR2`` caps at 4000
bytes, Firebird rows at 32 KB).  It is a property of the *fixture*, not of any
server.
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

SHORT_TEXT_LENGTH = 2000

#: Portable non-empty text used when a fixture column must have a DEFAULT.
#: The empty string is not portable (some servers store ``''`` as NULL),
#: and any non-empty value works on every server the suite runs on.
PLACEHOLDER_TEXT = "-"


def short_text(dialect):
    """Comparable, bounded text: identity-like columns."""
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
