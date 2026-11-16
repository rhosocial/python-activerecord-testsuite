# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/operations.py
"""What each fixture table asks of a dialect, and how the operations run.

Two halves, deliberately kept apart:

* the **registry** says, per table, which DDL/DML operations the fixture
  performs and which dialect switches each of them requires to be on or off.
  It answers a question the DDL derivation cannot yet answer for itself:
  core does not expose "this declaration needs the json concept". Until it
  does, the requirement is stated here, next to the model that creates it.
* the **operations** execute statements. They do not decide, skip or probe:
  a caller has already evaluated the registry and knows whether the operation
  is expected to work. An assertion inside an operation would make a
  capability question look like a defect.

Switch names resolve through a fixed order, because the dialect answers
capability questions through two channels that do not overlap (measured: on
SQLite ``supports_json_type`` is a method that is not a key of
``supports_data_types()``, and ``json`` is a key with no method):

1. a zero-argument boolean method of that name on the dialect -- the shape
   ``pytest_plugin.requirements`` already answers strictly;
2. a key of ``supports_data_types()`` -- the storage-concept table;
3. neither: :class:`MissingRequirementError`, naming the dialect and the
   switch.

The third outcome is a failure, never a skip. A dialect that never answered
the question cannot be said to have answered "no".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence, Tuple

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.base.derivation import (
    build_create_index_statements,
    build_create_table_statement,
    build_drop_table_statement,
)

from rhosocial.activerecord.testsuite.pytest_plugin.requirements import (
    MissingRequirementError,
    answer,
)

__all__ = [
    "DDL",
    "Operation",
    "TableFixture",
    "create_schema",
    "drop_schema",
    "operation_reason",
    "reload",
    "seed",
    "switch_answer",
    "table_reason",
]

#: Every statement this module executes is DDL or DML; naming it once keeps
#: the backend from guessing from the text of the statement.
DDL = ExecutionOptions(stmt_type=StatementType.DDL)


@dataclass(frozen=True)
class Operation:
    """One thing the fixture does to a table, and what it needs to work.

    ``name`` is the fixture's own word for it (``"create_table"``,
    ``"insert"``, ``"drop_table"``), so a skip reason can name the operation
    the reader is looking at rather than the assertion that failed.

    ``column`` narrows the requirement to one column. The complex group needs
    this: a bare ``dict`` column cannot be inserted on a dialect whose
    value-family table answers ``None`` for ``dict``, while the rest of the
    row is fine.
    """

    name: str
    requires_on: Tuple[str, ...] = ()
    requires_off: Tuple[str, ...] = ()
    column: Optional[str] = None

    def describe(self) -> str:
        if self.column is None:
            return self.name
        return "{} on column {}".format(self.name, self.column)


@dataclass(frozen=True)
class TableFixture:
    """A fixture table: what creates it, and what is done to it.

    ``source`` is the model the DDL is derived from. It is ``None`` for a
    projection -- a model bound to a table another fixture creates -- because
    a projection has no columns of its own to derive.
    """

    table: str
    source: Optional[type]
    operations: Tuple[Operation, ...] = field(default_factory=tuple)


def switch_answer(dialect: Any, switch: str) -> bool:
    """Ask the dialect one switch, through whichever channel answers it.

    Raises:
        MissingRequirementError: neither channel knows the switch.
    """
    if callable(getattr(dialect, switch, None)):
        return answer(dialect, switch)

    table = _data_type_table(dialect)
    if switch in table:
        return bool(table[switch])

    dialect_name = getattr(dialect, "name", type(dialect).__name__)
    raise MissingRequirementError(
        "{}.{}: the dialect neither implements this method nor names the "
        "concept in supports_data_types(), so it has not answered the "
        "question".format(dialect_name, switch)
    )


def _data_type_table(dialect: Any) -> dict:
    """The dialect's storage-concept table, or an empty one.

    A dialect that does not implement ``supports_data_types`` has answered
    nothing through this channel; whether that is a gap is decided after the
    method channel has also been asked, so an empty table is not itself an
    error here.
    """
    method = getattr(dialect, "supports_data_types", None)
    if not callable(method):
        return {}
    answered = method()
    return answered if isinstance(answered, dict) else {}


def operation_reason(dialect: Any, operation: Operation) -> Optional[str]:
    """Why *operation* cannot run on *dialect*, or ``None`` when it can."""
    for switch in operation.requires_on:
        if not switch_answer(dialect, switch):
            return _refused(dialect, operation, switch, "answer yes")
    for switch in operation.requires_off:
        if switch_answer(dialect, switch):
            return _refused(dialect, operation, switch, "answer no")
    return None


def table_reason(dialect: Any, fixture: TableFixture) -> Optional[str]:
    """Why no operation of *fixture* can run on *dialect*, or ``None``."""
    for operation in fixture.operations:
        why = operation_reason(dialect, operation)
        if why is not None:
            return why
    return None


def _refused(dialect: Any, operation: Operation, switch: str, expected: str) -> str:
    dialect_name = getattr(dialect, "name", type(dialect).__name__)
    return "{} requires {} to {}, but {} answered the opposite".format(
        operation.describe(), switch, expected, dialect_name
    )


def create_schema(backend: Any, fixtures: Iterable[TableFixture]) -> None:
    """Create every table a fixture declares, with its indexes.

    A table without a ``source`` is a projection: something else creates it.
    """
    for fixture in fixtures:
        if fixture.source is None:
            continue
        statement = build_create_table_statement(fixture.source, backend.dialect)
        backend.execute(*statement.to_sql(), options=DDL)
        for index in build_create_index_statements(fixture.source, backend.dialect):
            backend.execute(*index.to_sql(), options=DDL)


def drop_schema(backend: Any, fixtures: Iterable[TableFixture]) -> None:
    """Drop every table this fixture created.

    ``if_exists=False`` because the fixture created the table itself: the
    guess ``IF EXISTS`` would encode is about a table that cannot be missing
    unless the setup already failed.
    """
    for fixture in fixtures:
        if fixture.source is None:
            continue
        statement = build_drop_table_statement(fixture.source, backend.dialect)
        backend.execute(*statement.to_sql(), options=DDL)


def seed(model: type, rows: Sequence[Any]) -> Tuple[Any, ...]:
    """Insert the canonical rows and return the saved instances.

    Each row is a mapping of field names to values, or an instance of
    *model*. Values are passed through untouched: a fixture that has to
    prepare a value differently per backend is describing a backend, not a
    fixture.
    """
    saved = []
    for row in rows:
        instance = row if isinstance(row, model) else model(**row)
        instance.save()
        saved.append(instance)
    return tuple(saved)


def reload(model: type, pk: Any) -> Any:
    """Read one row back by primary key."""
    return model.find_one(pk)
