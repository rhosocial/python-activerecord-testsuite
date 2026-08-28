# src/rhosocial/activerecord/testsuite/feature/query/cross_schema/test_cross_schema_join.py
"""
Cross-schema ActiveRecord / ActiveQuery tests.

Two models live in two DIFFERENT schema namespaces (see fixtures/schema_models.py):
``ar_crm.customers`` and ``ar_shop.orders``. Every generated statement must
carry the model's own fully-qualified name, so joins, filters and writes work
across schemas without any search_path manipulation.

Backends without schema namespaces skip declaratively:
@requires_protocol(SchemaSupport, "supports_schema").
"""

import pytest

from rhosocial.activerecord.testsuite.utils import requires_protocol


@requires_protocol("SchemaSupport", "supports_schema")
def test_cross_schema_join(schema_fixtures):
    """JOIN across two schemas with WHERE + ORDER BY."""
    Customer, Order = schema_fixtures

    alice = Customer(name="alice")
    bob = Customer(name="bob")
    alice.save()
    bob.save()

    for cust, amount in ((alice, 100), (bob, 200), (alice, 300)):
        Order(customer_id=cust.id, amount=amount).save()

    rows = (
        Order.query()
        .join(Customer, on=Order.c.customer_id == Customer.c.id)
        .select(Order.c.amount, Customer.c.name.as_("customer"))
        .where(Customer.c.name == "alice")
        .order_by(Order.c.amount)
        .aggregate()
    )
    assert [(r["amount"], r["customer"]) for r in rows] == [(100, "alice"), (300, "alice")]


@requires_protocol("SchemaSupport", "supports_schema")
def test_cross_schema_count_with_condition(schema_fixtures):
    """Scalar COUNT over a cross-schema join."""
    Customer, Order = schema_fixtures

    cust = Customer(name="counted")
    cust.save()
    for i in range(3):
        Order(customer_id=cust.id, amount=i).save()

    total = (
        Order.query()
        .join(Customer, on=Order.c.customer_id == Customer.c.id)
        .where(Customer.c.name == "counted")
        .count()
    )
    assert total == 3


@requires_protocol("SchemaSupport", "supports_schema")
def test_cross_schema_writes_are_scoped(schema_fixtures):
    """save() lands in the owning schema; update/delete stay scoped by qualifiers."""
    Customer, Order = schema_fixtures

    cust = Customer(name="writer")
    cust.save()
    order = Order(customer_id=cust.id, amount=42)
    order.save()

    assert Order.query().where(Order.c.id == order.id).count() == 1
    assert Customer.query().where(Customer.c.id == cust.id).count() == 1

    Order.query().where(Order.c.id == order.id).update_all({"amount": 43})
    refreshed = Order.query().where(Order.c.id == order.id).one()
    assert refreshed.amount == 43

    Order.query().where(Order.c.id == order.id).delete_all()
    assert Order.query().where(Order.c.id == order.id).count() == 0
    # The other schema is unaffected.
    assert Customer.query().where(Customer.c.id == cust.id).count() == 1
