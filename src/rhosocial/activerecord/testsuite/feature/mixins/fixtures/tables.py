# src/rhosocial/activerecord/testsuite/feature/mixins/fixtures/tables.py
"""Fixture declarations for the mixins feature's models.

Each function builds a ``CreateTableStatement`` from backend expressions.  The
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
    ColumnNotNullConstraint,
    ColumnPrimaryKeyConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    TimestampType,
    BooleanType,
    FloatType,
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


def _short_text(dialect):
    """A short, comparable string column.

    Firebird's TEXT is a BLOB, and a BLOB has no value equality: DISTINCT,
    GROUP BY and ORDER BY treat equal BLOBs as unrelated values.  Columns the
    tests group on therefore stay a real VARCHAR on Firebird.
    """
    if str(getattr(dialect, "name", "")).lower().startswith("firebird"):
        return VarCharType(dialect, 255)
    return _text(dialect)


def _drop_if_exists(dialect) -> bool:
    """Whether this dialect can spell DROP TABLE IF EXISTS.

    Firebird -- among others -- cannot, so teardown asks for a plain DROP
    TABLE there.  The directory owns its tables, so they are present whenever
    teardown runs after a successful prepare.
    """
    probe = getattr(dialect, "supports_if_exists_table", None)
    return True if probe is None else bool(probe())


def _timestamp_storage(dialect):
    """Column type for created-at / updated-at fields (see the basic fixtures)."""
    if str(getattr(dialect, "name", "")).lower().startswith("firebird"):
        return TimestampType(dialect)
    return _text(dialect)


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


def _primary_key(dialect):
    return ColumnConstraint(
        dialect,
        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
    )


def timestamped_posts_table(dialect, table_name="timestamped_posts"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect, "id", IntegerType(dialect), constraints=[_primary_key(dialect)]
            ),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "content", _long_text(dialect)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def versioned_products_table(dialect, table_name="versioned_products"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect, "id", IntegerType(dialect), constraints=[_primary_key(dialect)]
            ),
            ColumnDefinition(
                dialect,
                "name",
                _text(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect, branch=ColumnNotNullConstraint(dialect)
                    )
                ],
            ),
            ColumnDefinition(dialect, "price", FloatType(dialect)),
            ColumnDefinition(dialect, "version", IntegerType(dialect)),
        ],
    )


def tasks_table(dialect, table_name="tasks"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect, "id", IntegerType(dialect), constraints=[_primary_key(dialect)]
            ),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "is_completed", BooleanType(dialect)),
            ColumnDefinition(dialect, "deleted_at", _timestamp_storage(dialect)),
        ],
    )


def combined_articles_table(dialect, table_name="combined_articles"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect, "id", IntegerType(dialect), constraints=[_primary_key(dialect)]
            ),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "content", _long_text(dialect)),
            ColumnDefinition(dialect, "status", _short_text(dialect)),
            ColumnDefinition(dialect, "version", IntegerType(dialect)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "deleted_at", _timestamp_storage(dialect)),
        ],
    )


MIXINS_TABLES = {
    "timestamped_posts": timestamped_posts_table,
    "versioned_products": versioned_products_table,
    "tasks": tasks_table,
    "combined_articles": combined_articles_table,
}
