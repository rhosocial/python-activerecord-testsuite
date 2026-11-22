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
from rhosocial.activerecord.base.derivation import integer_auto_increment_parts  # noqa: E402

from rhosocial.activerecord.backend.expression import ColumnConstraint as Constraint
from rhosocial.activerecord.backend.expression import ColumnDefinition as Column
from rhosocial.activerecord.backend.expression import CreateTableStatement as CreateTable
from rhosocial.activerecord.backend.expression import DropTableStatement as DropTable
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import ColumnNotNullConstraint as NotNull
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint as PrimaryKey,
)
from rhosocial.activerecord.backend.expression.types import BooleanType as Bool
from rhosocial.activerecord.backend.expression.types import FloatType as Float
from rhosocial.activerecord.backend.expression.types import IntegerType as Int
from rhosocial.activerecord.backend.expression.types import TextType, TimestampType, VarCharType

from . import resolve

# --- Generic column type concepts (local to this group) --------------------
#
# Migrated from the former cross-group type-helpers module.  Each group
# owns the concepts it uses; the dialect renders them, no backend name is read.

_SHORT_TEXT_LENGTH = 255


def _require_data_type(dialect, concept: str) -> None:
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


def short_text(dialect):
    """Comparable text for identity-like columns (a bounded VARCHAR)."""
    _require_data_type(dialect, "varchar")
    return VarCharType(dialect, _SHORT_TEXT_LENGTH)


def long_text(dialect):
    """Unbounded text payload; never compared or sorted."""
    return TextType(dialect)


def timestamp_type(dialect):
    """Timestamp with microsecond resolution where the server declares it."""
    probe = getattr(dialect, "supports_microsecond_timestamp", None)
    keeps_microseconds = bool(probe()) if callable(probe) else bool(probe)
    return TimestampType(dialect, precision=6 if keeps_microseconds else None)


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
        data_type, attributes = integer_auto_increment_parts(self.dialect, Int(self.dialect))
        return Column(
            self.dialect,
            name,
            data_type,
            constraints=[Constraint(self.dialect, branch=PrimaryKey(self.dialect))],
            attributes=attributes,
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
