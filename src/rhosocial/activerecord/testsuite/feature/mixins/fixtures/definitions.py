# src/rhosocial/activerecord/testsuite/feature/mixins/fixtures/definitions.py
"""L1 fixture definitions for the mixins topic.

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
    ColumnNotNullConstraint as NotNull,
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import (
    BooleanType as Bool,
    FloatType as Float,
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

    def not_null(self, name, sql_type):
        return self.column(
            name,
            sql_type,
            [Constraint(self.dialect, branch=NotNull(self.dialect))],
        )


class TimestampedPostDefinition(Definition):
    """The timestamped_posts table: timestamp mixin."""

    model = resolve("TimestampedPost")
    async_model = resolve("AsyncTimestampedPost")
    table_name = "timestamped_posts"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.longtext("content"),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
        ]


class VersionedProductDefinition(Definition):
    """The versioned_products table: optimistic lock mixin."""

    model = resolve("VersionedProduct")
    async_model = resolve("AsyncVersionedProduct")
    table_name = "versioned_products"

    def columns(self):
        return [
            self.auto_pk(),
            self.not_null("name", short_text(self.dialect)),
            self.column("price", Float(self.dialect)),
            self.column("version", Int(self.dialect)),
        ]


class TaskDefinition(Definition):
    """The tasks table: soft delete mixin."""

    model = resolve("Task")
    async_model = resolve("AsyncTask")
    table_name = "tasks"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.column("is_completed", Bool(self.dialect)),
            self.timestamp("deleted_at"),
        ]


class CombinedArticleDefinition(Definition):
    """The combined_articles table: timestamps + optimistic lock + soft delete."""

    model = resolve("CombinedArticle")
    async_model = resolve("AsyncCombinedArticle")
    table_name = "combined_articles"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.longtext("content"),
            self.text("status"),
            self.column("version", Int(self.dialect)),
            self.timestamp("created_at"),
            self.timestamp("updated_at"),
            self.timestamp("deleted_at"),
        ]
