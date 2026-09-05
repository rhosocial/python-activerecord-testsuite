# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/test_mixed_schema.py
"""Default-schema vs non-default-schema operations for identical tables.

``Order`` (default namespace) and ``MixedSchemaOrder`` (``SCHEMA_A``) share
the same table DDL; only ``__schema_name__`` differs. Providers provision
both namespaces plus the default ``users`` table so joins can span the
schema boundary.
"""
import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("SchemaSupport", "supports_schema")
def test_same_named_tables_coexist(mixed_schema_fixtures):
    """Identical table names in default and SCHEMA_A hold independent rows."""
    User, Order, MixedSchemaOrder = mixed_schema_fixtures

    user = User(username="coexist", email="coexist@example.com", age=30)
    user.save()
    Order(user_id=user.id, order_number="def-1", total_amount=10).save()
    Order(user_id=user.id, order_number="def-2", total_amount=20).save()
    MixedSchemaOrder(user_id=user.id, order_number="sch-1", total_amount=100).save()
    MixedSchemaOrder(user_id=user.id, order_number="sch-2", total_amount=200).save()
    MixedSchemaOrder(user_id=user.id, order_number="sch-3", total_amount=300).save()

    assert Order.query().count() == 2, "Expected 2 rows in default-schema orders"
    assert MixedSchemaOrder.query().count() == 3, "Expected 3 rows in schema-qualified orders"


@requires_protocol("SchemaSupport", "supports_schema")
def test_primary_key_lookup_is_namespace_scoped(mixed_schema_fixtures):
    """The same PK value resolves to different rows per namespace."""
    User, Order, MixedSchemaOrder = mixed_schema_fixtures

    user = User(username="pkcheck", email="pkcheck@example.com", age=30)
    user.save()
    Order(user_id=user.id, order_number="default-row").save()
    MixedSchemaOrder(user_id=user.id, order_number="schema-row").save()

    assert Order.query().where(Order.c.id == 1).one().order_number == "default-row", \
        "Expected default-schema order lookup to return default-row"
    assert (
        MixedSchemaOrder.query().where(MixedSchemaOrder.c.id == 1).one().order_number
        == "schema-row"
    ), "Expected schema-qualified order lookup to return schema-row"


@requires_protocol("SchemaSupport", "supports_schema")
def test_update_all_and_delete_all_stay_scoped(mixed_schema_fixtures):
    """Bulk writes on one namespace never leak into the other."""
    User, Order, MixedSchemaOrder = mixed_schema_fixtures

    user = User(username="scoped", email="scoped@example.com", age=30)
    user.save()
    Order(user_id=user.id, order_number="d1").save()
    MixedSchemaOrder(user_id=user.id, order_number="s1").save()
    MixedSchemaOrder(user_id=user.id, order_number="s2").save()

    MixedSchemaOrder.query().where(MixedSchemaOrder.c.user_id == user.id).update_all(
        {"status": "shipped"}
    )
    assert Order.query().where(Order.c.status == "pending").count() == 1, \
        "Expected the default-schema order to remain pending"
    assert MixedSchemaOrder.query().where(MixedSchemaOrder.c.status == "shipped").count() == 2, \
        "Expected both schema-qualified orders to be shipped"

    MixedSchemaOrder.query().where(MixedSchemaOrder.c.order_number == "s1").delete_all()
    assert MixedSchemaOrder.query().count() == 1, \
        "Expected 1 schema-qualified order remaining after delete"
    assert Order.query().count() == 1, "Expected default-schema count to remain at 1"


@requires_protocol("SchemaSupport", "supports_schema")
def test_join_default_user_with_schema_order(mixed_schema_fixtures):
    """JOIN from the default namespace to a schema-qualified table."""
    User, Order, MixedSchemaOrder = mixed_schema_fixtures

    alice = User(username="alice", email="alice@example.com", age=30)
    bob = User(username="bob", email="bob@example.com", age=30)
    alice.save()
    bob.save()
    MixedSchemaOrder(user_id=alice.id, order_number="j1", total_amount=5).save()
    MixedSchemaOrder(user_id=bob.id, order_number="j2", total_amount=7).save()
    MixedSchemaOrder(user_id=alice.id, order_number="j3", total_amount=9).save()

    rows = (
        MixedSchemaOrder.query()
        .join(User, on=MixedSchemaOrder.c.user_id == User.c.id)
        .select(MixedSchemaOrder.c.order_number, User.c.username.as_("owner"))
        .where(User.c.username == "alice")
        .order_by(MixedSchemaOrder.c.total_amount)
        .aggregate()
    )
    assert [(r["order_number"], r["owner"]) for r in rows] == [("j1", "alice"), ("j3", "alice")], \
        "Expected joined rows for alice to be (j1, 'alice') and (j3, 'alice')"
