# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/types_models.py
"""Scalar-type bare/annotated variants for the ``basic/types`` fixture group.

Two variants of one set of Python field types:

* ``TypedUser`` / ``AsyncTypedUser`` (``typed_users``) write only Python type
  annotations.  Storage is whatever the dialect suggests -- the executable
  form of the "write a class and get a table" promise.
* ``TypedUserAnnotated`` / ``AsyncTypedUserAnnotated``
  (``typed_users_annotated``) state every storage concept, constraint, index
  and comment from README section 4, so a test can tell what a declaration
  changed.

Identity is not a variant axis (F11): ``Optional[int]`` plus the framework's
``pk_auto_generated()`` default is the whole primary-key declaration on both
sides.  Sync and async pairs share one field mixin per variant (P4), so a
single declaration cannot drift between the two twins.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import ClassVar, Optional, Tuple

from rhosocial.activerecord.backend.expression.statements import (
    ColumnDefaultConstraint,
    ColumnUniqueConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    BooleanType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    TextType,
    TimestampType,
    TimeType,
    VarCharType,
)
from rhosocial.activerecord.base.field_proxy import FieldProxy
from rhosocial.activerecord.base.fields import UseComment, UseConstraint, UseIndex, UseSqlType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord

try:
    from typing import Annotated
except ImportError:  # pragma: no cover - Python 3.8 baseline
    from typing_extensions import Annotated

from .operations import Operation, TableFixture

__all__ = [
    "TYPES_FIXTURES",
    "TYPED_FIELD_NAMES",
    "TypedUser",
    "TypedUserAnnotated",
    "AsyncTypedUser",
    "AsyncTypedUserAnnotated",
]

#: The one field set both variants declare, in declaration order.  Kept here so
#: the declaration contracts in the tests do not repeat a hand-written list.
TYPED_FIELD_NAMES: Tuple[str, ...] = (
    "id",
    "flag",
    "count",
    "amount",
    "ratio",
    "label",
    "born_on",
    "wakes_at",
    "seen_at",
    "note",
)


class TypedUserFields:
    """Bare fields: Python annotations only, zero ``Annotated`` markers."""

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Optional[int] = None
    flag: bool = False
    count: int = 0
    amount: Decimal = Decimal("0.00")
    ratio: float = 0.0
    label: str = ""
    born_on: date = date(1970, 1, 1)
    wakes_at: time = time(7, 0, 0)
    seen_at: datetime = datetime(1970, 1, 1, 0, 0)
    note: Optional[str] = None


class TypedUserAnnotatedFields:
    """Annotated fields: storage, constraints, index and comment all stated."""

    c: ClassVar[FieldProxy] = FieldProxy()

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    flag: Annotated[
        bool,
        UseSqlType(BooleanType()),
        UseConstraint(ColumnDefaultConstraint, value=False),
    ] = False
    count: Annotated[
        int,
        UseSqlType(IntegerType()),
        UseComment("Occurrences recorded for this row"),
    ] = 0
    amount: Annotated[Decimal, UseSqlType(DecimalType(precision=12, scale=2))] = Decimal("0.00")
    ratio: Annotated[float, UseSqlType(FloatType())] = 0.0
    label: Annotated[
        str,
        UseSqlType(VarCharType(length=64)),
        UseConstraint(ColumnUniqueConstraint, name="uq_typed_users_annotated_label"),
        UseIndex("ix_typed_users_annotated_label"),
    ] = ""
    born_on: Annotated[date, UseSqlType(DateType())] = date(1970, 1, 1)
    wakes_at: Annotated[time, UseSqlType(TimeType())] = time(7, 0, 0)
    # Milliseconds are the shared default; microseconds are a separate
    # capability and are deliberately not requested here (README section 4.1).
    seen_at: Annotated[datetime, UseSqlType(TimestampType(precision=3))] = datetime(1970, 1, 1)
    note: Annotated[Optional[str], UseSqlType(TextType())] = None


class TypedUser(TypedUserFields, ActiveRecord):
    """Bare scalar-type variant, bound to ``typed_users``."""

    @classmethod
    def table_name(cls) -> str:
        return "typed_users"


class AsyncTypedUser(TypedUserFields, AsyncActiveRecord):
    """Async twin of :class:`TypedUser` (P4: same fields, same table)."""

    @classmethod
    def table_name(cls) -> str:
        return "typed_users"


class TypedUserAnnotated(TypedUserAnnotatedFields, ActiveRecord):
    """Fully annotated scalar-type variant, bound to ``typed_users_annotated``."""

    @classmethod
    def table_name(cls) -> str:
        return "typed_users_annotated"


class AsyncTypedUserAnnotated(TypedUserAnnotatedFields, AsyncActiveRecord):
    """Async twin of :class:`TypedUserAnnotated` (P4)."""

    @classmethod
    def table_name(cls) -> str:
        return "typed_users_annotated"


_OPS = (Operation("create_table"), Operation("insert"), Operation("drop_table"))

#: README section 9: the storage concepts the scalar group asks a dialect for.
#: ``datetime`` is the section's switch name for the ``TimestampType`` column.
#: The two twins share a source model, so one registration covers each table.
_COLUMN_SWITCHES = (
    ("id", "integer"),
    ("flag", "boolean"),
    ("count", "integer"),
    ("amount", "decimal"),
    ("ratio", "float"),
    ("label", "varchar"),
    ("born_on", "date"),
    ("wakes_at", "time"),
    ("seen_at", "datetime"),
    ("note", "text"),
)
_COLUMN_OPS = tuple(
    Operation("create_table", requires_on=(switch,), column=column)
    for column, switch in _COLUMN_SWITCHES
)

TYPES_FIXTURES: Tuple[TableFixture, ...] = (
    TableFixture(table="typed_users", source=TypedUser, operations=_OPS + _COLUMN_OPS),
    TableFixture(
        table="typed_users_annotated",
        source=TypedUserAnnotated,
        operations=_OPS + _COLUMN_OPS,
    ),
)
