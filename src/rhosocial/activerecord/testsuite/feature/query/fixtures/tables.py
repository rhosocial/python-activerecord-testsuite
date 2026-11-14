# src/rhosocial/activerecord/testsuite/feature/query/fixtures/tables.py
"""Fixture declarations for the query feature's models.

Each function builds a ``CreateTableStatement`` from backend expressions. The
environment renders it through the scenario's dialect, so no SQL text is
involved.
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
    TableUniqueConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    BooleanType,
    DecimalType,
    FloatType,
    IntegerType,
    TextType,
    TimestampType,
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


def _placeholder_text_default(dialect):
    """The non-null placeholder a caller gets when it omits ``product_name``.

    The value has to survive a ``NOT NULL`` column and stay comparable across
    rows, because the composite-order-item conflict contract relies on two
    inserts colliding on ``(order_id, product_id, product_name)``.

    Oracle has no distinct empty string -- ``''`` *is* ``NULL``, so
    ``DEFAULT ''`` is a parse error there and an empty value would fail the
    ``NOT NULL`` check.  A single space is the smallest value that is still a
    real string on Oracle, and it collides just like ``''`` does elsewhere.
    """
    if str(getattr(dialect, "name", "")).lower().startswith("oracle"):
        return " "
    return ""


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
    """Column type for the timestamp mixin's created-at / updated-at fields.

    Those fields are declared as ``TimestampType`` in the models, so the
    driver receives a ``datetime``.  Firebird's ``TEXT`` is a BLOB and cannot
    bind a datetime, so its tables keep the native TIMESTAMP; every other
    backend keeps the portable text column its adapter already handles.
    """
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
    return DropTableStatement(dialect, Table(dialect, table_name), if_exists=_drop_if_exists(dialect))


def _primary_key(dialect, name, column_type):
    """One auto-incrementing integer primary-key column."""
    return ColumnDefinition(
        dialect,
        name,
        column_type,
        constraints=[
            ColumnConstraint(
                dialect,
                branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
            )
        ],
    )


def _column(dialect, name, column_type):
    """One nullable column."""
    return ColumnDefinition(dialect, name, column_type)


def users_table(dialect, table_name="users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "username", _text(dialect)),
            _column(dialect, "email", _text(dialect)),
            _column(dialect, "age", IntegerType(dialect)),
            _column(dialect, "balance", FloatType(dialect)),
            _column(dialect, "is_active", BooleanType(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def json_users_table(dialect, table_name="json_users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "username", _text(dialect)),
            _column(dialect, "email", _text(dialect)),
            _column(dialect, "age", IntegerType(dialect)),
            _column(dialect, "settings", _long_text(dialect)),
            _column(dialect, "tags", _long_text(dialect)),
            _column(dialect, "profile", _long_text(dialect)),
            _column(dialect, "roles", _long_text(dialect)),
            _column(dialect, "scores", _long_text(dialect)),
            _column(dialect, "subscription", _long_text(dialect)),
            _column(dialect, "preferences", _long_text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def orders_table(dialect, table_name="orders"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "user_id", IntegerType(dialect)),
            _column(dialect, "order_number", _text(dialect)),
            _column(dialect, "total_amount", DecimalType(dialect, 12, 4)),
            _column(dialect, "status", _short_text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def order_items_table(dialect, table_name="order_items"):
    """Superset of the query order item and the basic composite-key item."""
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "order_id", IntegerType(dialect)),
            _column(dialect, "product_id", IntegerType(dialect)),
            ColumnDefinition(
                dialect,
                "product_name",
                VarCharType(dialect, 255),
                constraints=[
                    # Oracle requires DEFAULT before inline constraints (NOT NULL).
                    ColumnConstraint(dialect, branch=ColumnDefaultConstraint(dialect, _placeholder_text_default(dialect))),
                    ColumnConstraint(dialect, branch=ColumnNotNullConstraint(dialect)),
                ],
            ),
            _column(dialect, "quantity", IntegerType(dialect)),
            _column(dialect, "unit_price", DecimalType(dialect, 12, 4)),
            _column(dialect, "subtotal", DecimalType(dialect, 12, 4)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
        table_constraints=[
            TableConstraint(
                dialect,
                branch=TableUniqueConstraint(dialect, ["order_id", "product_id", "product_name"]),
            )
        ],
    )


def posts_table(dialect, table_name="posts"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "user_id", IntegerType(dialect)),
            _column(dialect, "title", _text(dialect)),
            _column(dialect, "content", _long_text(dialect)),
            _column(dialect, "status", _short_text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def comments_table(dialect, table_name="comments"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "user_id", IntegerType(dialect)),
            _column(dialect, "post_id", IntegerType(dialect)),
            _column(dialect, "content", _long_text(dialect)),
            _column(dialect, "is_hidden", BooleanType(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def profiles_table(dialect, table_name="profiles"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "user_id", IntegerType(dialect)),
            _column(dialect, "bio", _long_text(dialect)),
            _column(dialect, "avatar_url", _text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def nodes_table(dialect, table_name="nodes"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "name", _text(dialect)),
            _column(dialect, "parent_id", IntegerType(dialect)),
            _column(dialect, "value", DecimalType(dialect, 12, 4)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def extended_orders_table(dialect, table_name="extended_orders"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "user_id", IntegerType(dialect)),
            _column(dialect, "order_number", _text(dialect)),
            _column(dialect, "total_amount", DecimalType(dialect, 12, 4)),
            _column(dialect, "status", _short_text(dialect)),
            _column(dialect, "priority", _text(dialect)),
            _column(dialect, "region", _text(dialect)),
            _column(dialect, "category", _text(dialect)),
            _column(dialect, "product", _text(dialect)),
            _column(dialect, "department", _text(dialect)),
            _column(dialect, "year", _text(dialect)),
            _column(dialect, "quarter", _text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def extended_order_items_table(dialect, table_name="extended_order_items"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "order_id", IntegerType(dialect)),
            ColumnDefinition(
                dialect,
                "product_name",
                VarCharType(dialect, 255),
                constraints=[
                    # Oracle requires DEFAULT before inline constraints (NOT NULL).
                    ColumnConstraint(dialect, branch=ColumnDefaultConstraint(dialect, _placeholder_text_default(dialect))),
                    ColumnConstraint(dialect, branch=ColumnNotNullConstraint(dialect)),
                ],
            ),
            _column(dialect, "quantity", IntegerType(dialect)),
            _column(dialect, "price", DecimalType(dialect, 12, 4)),
            _column(dialect, "category", _text(dialect)),
            _column(dialect, "region", _text(dialect)),
            _column(dialect, "created_at", _timestamp_storage(dialect)),
            _column(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def searchable_items_table(dialect, table_name="searchable_items"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            _primary_key(dialect, "id", IntegerType(dialect)),
            _column(dialect, "name", _text(dialect)),
            _column(dialect, "tags", _long_text(dialect)),
        ],
    )


QUERY_TABLES = {
    "users": users_table,
    "json_users": json_users_table,
    "orders": orders_table,
    "order_items": order_items_table,
    "posts": posts_table,
    "comments": comments_table,
    "profiles": profiles_table,
    "nodes": nodes_table,
    "extended_orders": extended_orders_table,
    "extended_order_items": extended_order_items_table,
    "searchable_items": searchable_items_table,
}
