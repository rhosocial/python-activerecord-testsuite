# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/test_mixed_schema_qualifiers.py
"""Qualifier-form contract for schema-bound models under plain and joined ranges."""
import re

from rhosocial.activerecord.testsuite.utils import requires_protocol


def _norm(sql: str) -> str:
    """Normalise rendered SQL: strip identifier quotes, fold case/space."""
    cleaned = sql.replace('"', "").replace("`", "").replace("[", "").replace("]", "")
    return re.sub(r"\s+", " ", cleaned).lower()


@requires_protocol("SchemaSupport", "supports_schema")
def test_schema_model_qualifies_range_not_columns(mixed_schema_fixtures):
    """A schema-bound model qualifies its FROM range, never three-part cols."""
    _, _, MixedSchemaOrder = mixed_schema_fixtures

    sql, _ = (
        MixedSchemaOrder.query()
        .select(MixedSchemaOrder.c.order_number)
        .to_sql()
    )
    normed = _norm(sql)
    # Range keeps the namespace...
    assert "from ar_crm.orders" in normed
    # ...while column references never grow a third (schema) part.
    assert "ar_crm.orders.order_number" not in normed


@requires_protocol("JoinSupport", "supports_inner_join")
def test_schema_join_columns_stay_two_part(mixed_schema_fixtures):
    """Even joined against default-schema tables, schema-model columns stay
    two-part (TABLE.COLUMN) in ON/WHERE positions."""
    User, _, MixedSchemaOrder = mixed_schema_fixtures

    sql, _ = (
        MixedSchemaOrder.query()
        .join(User, on=MixedSchemaOrder.c.user_id == User.c.id)
        .select(MixedSchemaOrder.c.order_number)
        .where(User.c.username == "nobody")
        .to_sql()
    )
    normed = _norm(sql)
    assert "from ar_crm.orders" in normed
    assert "ar_crm.orders.user_id" not in normed
    assert "orders.user_id = users.id" in normed


