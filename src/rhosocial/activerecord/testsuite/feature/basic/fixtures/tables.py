# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/tables.py
"""Fixture declarations for the basic feature's models.

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
    TablePrimaryKeyConstraint,
)
from rhosocial.activerecord.backend.expression.types import (
    ArrayType,
    BigIntType,
    BlobType,
    BooleanType,
    DecimalType,
    DateType,
    DoubleType,
    FloatType,
    IntegerType,
    JsonBType,
    SmallIntType,
    TextType,
    TimeType,
    TimestampTzType,
    TimestampType,
    TinyIntType,
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


def _is_postgres(dialect) -> bool:
    return str(getattr(dialect, "name", "")).lower().startswith("postgres")


def _is_firebird(dialect) -> bool:
    return str(getattr(dialect, "name", "")).lower().startswith("firebird")


def _native_temporal(dialect) -> bool:
    return str(getattr(dialect, "name", "")).lower().startswith(
        ("postgres", "oracle", "firebird")
    )


def _date_type(dialect):
    return DateType(dialect) if _native_temporal(dialect) else _text(dialect)


def _timestamp_type(dialect):
    if _is_firebird(dialect):
        # Firebird has no generic ``timestamptz``; its TIMESTAMP is the
        # without-time-zone type, which is what the models declare.
        return TimestampType(dialect)
    return TimestampTzType(dialect) if _native_temporal(dialect) else _text(dialect)


def _time_type(dialect):
    return TimeType(dialect) if _is_firebird(dialect) else _text(dialect)


def _json_type(dialect):
    return JsonBType(dialect) if _is_postgres(dialect) else TextType(dialect)


def _int_array_type(dialect):
    if _is_postgres(dialect):
        return ArrayType(dialect, element_type=IntegerType(dialect))
    return TextType(dialect)


def _text_array_type(dialect):
    if _is_postgres(dialect):
        return ArrayType(dialect, element_type=TextType(dialect))
    return TextType(dialect)


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
    return DropTableStatement(
        dialect, Table(dialect, table_name), if_exists=_drop_if_exists(dialect)
    )


def users_table(dialect, table_name="users"):
    """The users table; it carries the union of the basic and mapped models."""
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "username", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
            ColumnDefinition(dialect, "age", IntegerType(dialect)),
            ColumnDefinition(dialect, "balance", FloatType(dialect)),
            ColumnDefinition(dialect, "is_active", BooleanType(dialect)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def posts_table(dialect, table_name="posts"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "author", IntegerType(dialect)),
            ColumnDefinition(dialect, "title", _text(dialect)),
            ColumnDefinition(dialect, "content", _long_text(dialect)),
            ColumnDefinition(dialect, "published_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "published", BooleanType(dialect)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def comments_table(dialect, table_name="comments"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "post_ref", IntegerType(dialect)),
            ColumnDefinition(dialect, "author", IntegerType(dialect)),
            ColumnDefinition(dialect, "text", _text(dialect)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "approved", BooleanType(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def type_cases_table(dialect, table_name="type_cases"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                VarCharType(dialect, 64),
                constraints=[
                    ColumnConstraint(dialect, branch=ColumnPrimaryKeyConstraint(dialect))
                ],
            ),
            ColumnDefinition(dialect, "username", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
            ColumnDefinition(dialect, "tiny_int", TinyIntType(dialect)),
            ColumnDefinition(dialect, "small_int", SmallIntType(dialect)),
            ColumnDefinition(dialect, "big_int", BigIntType(dialect)),
            ColumnDefinition(dialect, "float_val", FloatType(dialect)),
            ColumnDefinition(dialect, "double_val", DoubleType(dialect)),
            ColumnDefinition(dialect, "decimal_val", DecimalType(dialect, 10, 4)),
            ColumnDefinition(dialect, "char_val", _text(dialect)),
            ColumnDefinition(dialect, "varchar_val", _text(dialect)),
            ColumnDefinition(dialect, "text_val", _long_text(dialect)),
            ColumnDefinition(dialect, "date_val", _date_type(dialect)),
            ColumnDefinition(dialect, "time_val", _time_type(dialect)),
            ColumnDefinition(dialect, "timestamp_val", _timestamp_type(dialect)),
            ColumnDefinition(dialect, "blob_val", BlobType(dialect)),
            ColumnDefinition(dialect, "json_val", _json_type(dialect)),
            ColumnDefinition(dialect, "array_val", _int_array_type(dialect)),
            ColumnDefinition(dialect, "is_active", BooleanType(dialect)),
        ],
    )


def type_tests_table(dialect, table_name="type_tests"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                VarCharType(dialect, 64),
                constraints=[
                    ColumnConstraint(dialect, branch=ColumnPrimaryKeyConstraint(dialect))
                ],
            ),
            ColumnDefinition(dialect, "string_field", _text(dialect)),
            ColumnDefinition(dialect, "int_field", IntegerType(dialect)),
            ColumnDefinition(dialect, "float_field", FloatType(dialect)),
            ColumnDefinition(dialect, "decimal_field", DecimalType(dialect, 12, 4)),
            ColumnDefinition(dialect, "bool_field", BooleanType(dialect)),
            ColumnDefinition(dialect, "datetime_field", _timestamp_type(dialect)),
            ColumnDefinition(dialect, "json_field", _text(dialect)),
            ColumnDefinition(dialect, "nullable_field", _text(dialect)),
        ],
    )


def validated_field_users_table(dialect, table_name="validated_field_users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "username", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
            ColumnDefinition(dialect, "age", IntegerType(dialect)),
            ColumnDefinition(dialect, "balance", FloatType(dialect)),
            ColumnDefinition(dialect, "credit_score", IntegerType(dialect)),
            ColumnDefinition(
                dialect,
                "status",
                VarCharType(dialect, 32),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnDefaultConstraint(dialect, "active"),
                    )
                ],
            ),
            ColumnDefinition(dialect, "is_active", BooleanType(dialect)),
        ],
    )


def validated_users_table(dialect, table_name="validated_users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "username", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
            ColumnDefinition(dialect, "age", IntegerType(dialect)),
        ],
    )


def pydantic_validated_models_table(
    dialect, table_name="pydantic_validated_models"
):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "code", _text(dialect)),
            ColumnDefinition(dialect, "quantity", IntegerType(dialect)),
            ColumnDefinition(dialect, "step_count", IntegerType(dialect)),
            ColumnDefinition(dialect, "price", DecimalType(dialect, 12, 4)),
            ColumnDefinition(dialect, "start_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "end_at", _timestamp_storage(dialect)),
            ColumnDefinition(
                dialect,
                "status",
                VarCharType(dialect, 32),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnDefaultConstraint(dialect, "draft"),
                    )
                ],
            ),
            ColumnDefinition(dialect, "normalized_name", _text(dialect)),
            ColumnDefinition(
                dialect,
                "created_token",
                VarCharType(dialect, 128),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnDefaultConstraint(dialect, "generated-token"),
                    )
                ],
            ),
        ],
    )


def type_adapter_tests_table(dialect, table_name="type_adapter_tests"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(
                dialect,
                "name",
                _text(dialect),
                constraints=[
                    ColumnConstraint(dialect, branch=ColumnNotNullConstraint(dialect))
                ],
            ),
            ColumnDefinition(dialect, "optional_name", _text(dialect)),
            ColumnDefinition(dialect, "optional_age", IntegerType(dialect)),
            ColumnDefinition(dialect, "last_login", _text(dialect)),
            ColumnDefinition(dialect, "is_premium", BooleanType(dialect)),
            ColumnDefinition(dialect, "unsupported_union", _text(dialect)),
            ColumnDefinition(dialect, "custom_bool", _text(dialect)),
            ColumnDefinition(dialect, "optional_custom_bool", _text(dialect)),
        ],
    )


def column_mapping_items_table(dialect, table_name="column_mapping_items"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(dialect, "item_total", IntegerType(dialect)),
            ColumnDefinition(dialect, "remarks", _text(dialect)),
        ],
    )


def mixed_annotation_items_table(dialect, table_name="mixed_annotation_items"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "name", _text(dialect)),
            # ``tags`` is a list serialized by ``ListToStringAdapter`` into a
            # string column, so it must stay text even where the dialect has a
            # native array type.
            ColumnDefinition(dialect, "tags", _long_text(dialect)),
            ColumnDefinition(dialect, "meta", _text(dialect)),
            ColumnDefinition(dialect, "description", _long_text(dialect)),
            ColumnDefinition(
                dialect,
                "status",
                VarCharType(dialect, 32),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnDefaultConstraint(dialect, "active"),
                    )
                ],
            ),
        ],
    )


def bulk_users_table(dialect, table_name="bulk_users"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(
                dialect,
                "age",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(dialect, branch=ColumnDefaultConstraint(dialect, 0))
                ],
            ),
            ColumnDefinition(dialect, "email", _text(dialect)),
        ],
    )


def orders_table(dialect, table_name="orders"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "total", DecimalType(dialect, 12, 4)),
            ColumnDefinition(dialect, "created_at", _timestamp_storage(dialect)),
            ColumnDefinition(dialect, "updated_at", _timestamp_storage(dialect)),
        ],
    )


def order_items_table(dialect, table_name="order_items"):
    """Composite-key order item owned by the basic topic."""
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(dialect, "order_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "product_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "quantity", IntegerType(dialect)),
            ColumnDefinition(dialect, "unit_price", DecimalType(dialect, 12, 4)),
        ],
        table_constraints=[
            TableConstraint(
                dialect,
                branch=TablePrimaryKeyConstraint(
                    dialect, ["order_id", "product_id"]
                ),
            )
        ],
    )


def product_table(dialect, table_name="product"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(dialect, "price", FloatType(dialect)),
            ColumnDefinition(dialect, "quantity", IntegerType(dialect)),
        ],
    )


def store_inventory_table(dialect, table_name="store_inventory"):
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(dialect, "store_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "product_id", IntegerType(dialect)),
            ColumnDefinition(dialect, "batch_id", VarCharType(dialect, 64)),
            ColumnDefinition(
                dialect,
                "stock",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(dialect, branch=ColumnDefaultConstraint(dialect, 0))
                ],
            ),
        ],
        table_constraints=[
            TableConstraint(
                dialect,
                branch=TablePrimaryKeyConstraint(
                    dialect, ["store_id", "product_id", "batch_id"]
                ),
            )
        ],
    )


def test_users_table(dialect, table_name="test_users"):
    """The connection-pool tests' table."""
    return CreateTableStatement(
        dialect=dialect,
        table=Table(dialect, table_name),
        columns=[
            ColumnDefinition(
                dialect,
                "id",
                IntegerType(dialect),
                constraints=[
                    ColumnConstraint(
                        dialect,
                        branch=ColumnPrimaryKeyConstraint(dialect, is_auto_increment=True),
                    )
                ],
            ),
            ColumnDefinition(dialect, "name", _text(dialect)),
            ColumnDefinition(dialect, "email", _text(dialect)),
        ],
    )


BASIC_TABLES = {
    "users": users_table,
    "test_users": test_users_table,
    "type_cases": type_cases_table,
    "type_tests": type_tests_table,
    "validated_field_users": validated_field_users_table,
    "validated_users": validated_users_table,
    "pydantic_validated_models": pydantic_validated_models_table,
    "type_adapter_tests": type_adapter_tests_table,
    "posts": posts_table,
    "comments": comments_table,
    "column_mapping_items": column_mapping_items_table,
    "mixed_annotation_items": mixed_annotation_items_table,
    "bulk_users": bulk_users_table,
    "orders": orders_table,
    "order_items": order_items_table,
    "product": product_table,
    "store_inventory": store_inventory_table,
}
