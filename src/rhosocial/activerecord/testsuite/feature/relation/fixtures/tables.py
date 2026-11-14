# src/rhosocial/activerecord/testsuite/feature/relation/fixtures/tables.py
"""Fixture declarations for the relation feature's models.

Each function builds a ``CreateTableStatement`` from backend expressions. The
environment renders it through the scenario's dialect, so no SQL text is
involved.
"""
from rhosocial.activerecord.backend.expression import (
    ColumnConstraint,
    ColumnDefinition,
    CreateTableStatement,
    DropTableStatement,
)
from rhosocial.activerecord.backend.expression.objects import Table
from rhosocial.activerecord.backend.expression.statements import (
    ColumnPrimaryKeyConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    IntegerType,
    TextType,
    VarCharType,
)


def _text(dialect):
    """Short text as VARCHAR on Oracle (CLOB cannot be compared); TEXT elsewhere."""
    name = str(getattr(dialect, "name", "")).lower()
    if name.startswith("oracle"):
        return VarCharType(dialect, 4000)
    if name.startswith("firebird"):
        # Firebird's TEXT is a BLOB, and a BLOB has no value order or equality:
        # ORDER BY / DISTINCT on it silently misbehave.  Keep the column a real
        # comparable VARCHAR; 2000 bytes stays clear of Firebird's 32 KB row
        # limit even in the wide type-case table.
        return VarCharType(dialect, 2000)
    return TextType(dialect)


def _drop_if_exists(dialect) -> bool:
    """Whether this dialect can spell DROP TABLE IF EXISTS.

    Firebird -- among others -- cannot, so teardown asks for a plain DROP
    TABLE there.  The directory owns its tables, so they are present whenever
    teardown runs after a successful prepare.
    """
    probe = getattr(dialect, "supports_if_exists_table", None)
    return True if probe is None else bool(probe())


def _long_text(dialect):
    """Unbounded text payload (CLOB on Oracle, BLOB on Firebird).

    Payload columns are never compared or sorted, so they can use the
    backend's large-object text type; only short identity-like columns need
    the comparable VARCHAR that ``_text`` returns there.
    """
    return TextType(dialect)


def drop_table(dialect, table_name: str):
    """The fixture-owned DROP expression for one of this topic's tables."""
    return DropTableStatement(
        dialect, Table(dialect, table_name), if_exists=_drop_if_exists(dialect)
    )


def _primary_key(dialect, column_name: str):
    return ColumnDefinition(
        dialect,
        column_name,
        IntegerType(dialect),
        constraints=[
            ColumnConstraint(
                dialect,
                branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
            )
        ],
    )


def employees_table(dialect, table_name="employees"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "username", _text(dialect)),
            ColumnDefinition(dialect, "department_id", IntegerType(dialect)),
        ],
    )


def departments_table(dialect, table_name="departments"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(dialect, "description", _long_text(dialect)),
        ],
    )


def authors_table(dialect, table_name="authors"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "name", _text(dialect)),
        ],
    )


def books_table(dialect, table_name="books"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "author_id", IntegerType(dialect)),
        ],
    )


def chapters_table(dialect, table_name="chapters"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "book_id", IntegerType(dialect)),
        ],
    )


def profiles_table(dialect, table_name="profiles"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "bio", _long_text(dialect)),
            ColumnDefinition(dialect, "author_id", IntegerType(dialect)),
        ],
    )


def users_table(dialect, table_name="users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
            ColumnDefinition(dialect, "settings", _long_text(dialect)),
        ],
    )


def posts_table(dialect, table_name="posts"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "body", _text(dialect)),
            ColumnDefinition(dialect, "user_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "view_count", IntegerType(dialect)),
            ColumnDefinition(dialect, "metadata", _text(dialect)),
        ],
    )


def comments_table(dialect, table_name="comments"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "body", _text(dialect)),
            ColumnDefinition(dialect, "post_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "meta", _text(dialect)),
        ],
    )


def boundary_owners_table(dialect, table_name="relation_boundary_owners"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "name", _text(dialect)),
        ],
    )


def boundary_profiles_table(dialect, table_name="relation_boundary_profiles"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "bio", _long_text(dialect)),
            ColumnDefinition(dialect, "owner_id", IntegerType(dialect)),
        ],
    )


def boundary_posts_table(dialect, table_name="relation_boundary_posts"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id"),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "owner_id", IntegerType(dialect)),
        ],
    )


RELATION_TABLES = {
    "employees": employees_table,
    "departments": departments_table,
    "authors": authors_table,
    "books": books_table,
    "chapters": chapters_table,
    "profiles": profiles_table,
    "users": users_table,
    "posts": posts_table,
    "comments": comments_table,
    "relation_boundary_owners": boundary_owners_table,
    "relation_boundary_profiles": boundary_profiles_table,
    "relation_boundary_posts": boundary_posts_table,
}
