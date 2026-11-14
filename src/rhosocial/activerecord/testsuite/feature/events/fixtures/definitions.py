# src/rhosocial/activerecord/testsuite/feature/events/fixtures/definitions.py
"""L1 fixture definitions for the events topic.

A definition class holds the test model classes together with the DDL
expression instances they need.  It receives only a ``dialect`` and never a
backend; composing and executing the environment belongs to the L2 fixtures.

The model classes come from the sibling model modules.  ``resolve`` picks the
newest versioned module the running interpreter supports, so a definition is
bound to the same class a fixture delivers.

Expression names are imported under short aliases so the definitions stay
readable.
"""

from rhosocial.activerecord.backend.expression import (
    ColumnConstraint as Constraint,
    ColumnDefinition as Column,
    CreateTableStatement as CreateTable,
    DropTableStatement as DropTable,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import (
    IntegerType as Int,
)
from rhosocial.activerecord.testsuite.core.fixture_types import (
    long_text,
    short_text,
    timestamp_type,
)

from . import resolve


class Definition:
    """Base class for this topic's table definitions."""

    model = None
    async_model = None
    table_name = ""

    def __init__(self, dialect, table_name=None):
        self.dialect = dialect
        self.name = table_name or type(self).table_name
        self.create_table = CreateTable(
            dialect,
            table=Table(dialect, self.name),
            columns=self.columns(),
        )
        self.drop_table = DropTable(dialect, table=Table(dialect, self.name))

    def columns(self):
        raise NotImplementedError

    def column(self, name, sql_type, constraints=None):
        return Column(self.dialect, name, sql_type, constraints=constraints or [])

    def auto_pk(self, name="id"):
        return self.column(
            name,
            Int(self.dialect),
            [
                Constraint(
                    self.dialect,
                    branch=PrimaryKey(self.dialect, is_auto_increment=True),
                )
            ],
        )

    def text(self, name):
        return self.column(name, short_text(self.dialect))

    def longtext(self, name):
        return self.column(name, long_text(self.dialect))

    def timestamp(self, name):
        return self.column(name, timestamp_type(self.dialect))


class EventTestDefinition(Definition):
    """The event_tests table: lifecycle and handler events."""

    model = resolve("EventTestModel")
    async_model = resolve("AsyncEventTestModel")
    table_name = "event_tests"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.text("status"),
            self.column("revision", Int(self.dialect)),
            self.longtext("content"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class EventTrackingDefinition(Definition):
    """The event_tracking_models table: tracked reads."""

    model = resolve("EventTrackingModel")
    async_model = resolve("AsyncEventTrackingModel")
    table_name = "event_tracking_models"

    def columns(self):
        return [
            self.text("title"),
            self.longtext("content"),
            self.column("view_count", Int(self.dialect)),
            self.timestamp("last_viewed_at"),
        ]
