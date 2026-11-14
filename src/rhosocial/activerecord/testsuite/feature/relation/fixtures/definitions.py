# src/rhosocial/activerecord/testsuite/feature/relation/fixtures/definitions.py
"""L1 fixture definitions for the relation topic.

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


# ── Basic relation tables ────────────────────────────────


class EmployeeDefinition(Definition):
    """The employees table: BelongsTo -> Department."""

    model = resolve("Employee")
    table_name = "employees"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("username"),
            self.column("department_id", Int(self.dialect)),
        ]


class DepartmentDefinition(Definition):
    """The departments table: HasMany -> Employee."""

    model = resolve("Department")
    table_name = "departments"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.longtext("description"),
        ]


class AuthorDefinition(Definition):
    """The authors table: HasMany -> Book and HasOne -> Profile."""

    model = resolve("Author")
    table_name = "authors"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
        ]


class BookDefinition(Definition):
    """The books table: BelongsTo -> Author and HasMany -> Chapter."""

    model = resolve("Book")
    table_name = "books"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.column("author_id", Int(self.dialect)),
        ]


class ChapterDefinition(Definition):
    """The chapters table: BelongsTo -> Book."""

    model = resolve("Chapter")
    table_name = "chapters"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.column("book_id", Int(self.dialect)),
        ]


class ProfileDefinition(Definition):
    """The profiles table: BelongsTo -> Author."""

    model = resolve("Profile")
    table_name = "profiles"

    def columns(self):
        return [
            self.auto_pk(),
            self.longtext("bio"),
            self.column("author_id", Int(self.dialect)),
        ]


# ── Advanced relation tables (FieldProxy, DerivedField, JSON) ──


class UserDefinition(Definition):
    """The users table: HasMany -> Post, JSON settings."""

    model = resolve("User")
    async_model = resolve("AsyncUser")
    table_name = "users"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
            self.text("email"),
            self.longtext("settings"),
        ]


class PostDefinition(Definition):
    """The posts table: BelongsTo -> User and HasMany -> Comment."""

    model = resolve("Post")
    async_model = resolve("AsyncPost")
    table_name = "posts"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.text("body"),
            self.column("user_id", Int(self.dialect)),
            self.column("view_count", Int(self.dialect)),
            self.text("metadata"),
        ]


class CommentDefinition(Definition):
    """The comments table: BelongsTo -> Post."""

    model = resolve("Comment")
    async_model = resolve("AsyncComment")
    table_name = "comments"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("body"),
            self.column("post_id", Int(self.dialect)),
            self.text("meta"),
        ]


# ── Relation boundary tables ─────────────────────────────


class BoundaryOwnerDefinition(Definition):
    """The relation boundary owners table."""

    model = resolve("BoundaryOwner")
    async_model = resolve("AsyncBoundaryOwner")
    table_name = "relation_boundary_owners"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("name"),
        ]


class BoundaryProfileDefinition(Definition):
    """The relation boundary profiles table."""

    model = resolve("BoundaryProfile")
    async_model = resolve("AsyncBoundaryProfile")
    table_name = "relation_boundary_profiles"

    def columns(self):
        return [
            self.auto_pk(),
            self.longtext("bio"),
            self.column("owner_id", Int(self.dialect)),
        ]


class BoundaryPostDefinition(Definition):
    """The relation boundary posts table."""

    model = resolve("BoundaryPost")
    async_model = resolve("AsyncBoundaryPost")
    table_name = "relation_boundary_posts"

    def columns(self):
        return [
            self.auto_pk(),
            self.text("title"),
            self.column("owner_id", Int(self.dialect)),
        ]
