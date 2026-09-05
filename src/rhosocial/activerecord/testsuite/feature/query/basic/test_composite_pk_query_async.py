# src/rhosocial/activerecord/testsuite/feature/query/basic/test_composite_pk_query_async.py
"""Tests for async ActiveQuery operations on models with composite primary keys."""
from decimal import Decimal

import pytest

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression import ComparisonPredicate, Literal
class TestAsyncActiveQueryCompositePK:
    """Test async ActiveQuery operations against models with composite primary keys."""

    async def test_where_pk_predicate(self, async_order_item_class):
        """Querying by the full composite key predicate should return the matching record."""
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        predicate = async_order_item_class._build_pk_where_predicate(
            {"order_id": 1, "product_id": 101}
        )
        result = await async_order_item_class.query().where(predicate).one()
        assert result is not None, "Expected to find the record by composite key"
        assert result.order_id == 1, "Expected order_id to be 1"
        assert result.product_id == 101, "Expected product_id to be 101"

    async def test_where_single_column(self, async_order_item_class):
        """Filtering by a single composite key column should return matching rows."""
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        backend = async_order_item_class.backend()
        results = await async_order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).all()
        assert len(results) == 2, "Expected 2 rows with order_id == 1"

    async def test_where_and_condition(self, async_order_item_class):
        """Combining multiple where clauses should apply both filters."""
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        backend = async_order_item_class.backend()
        results = await async_order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).where(
            Column(backend.dialect, "quantity") > 1
        ).all()
        assert len(results) == 1, "Expected 1 row matching both conditions"
        assert results[0].product_id == 101, "Expected product_id to be 101"

    async def test_order_limit(self, async_order_item_class):
        """Ordering with limit should respect the configured row cap."""
        items = [
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=103, quantity=3, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        results = await async_order_item_class.query().order_by("product_id").limit(2).all()
        assert len(results) == 2, "Expected 2 rows after limit"

    async def test_count(self, async_order_item_class):
        """count() should return the total number of seeded records."""
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2),
            async_order_item_class(order_id=1, product_id=102, quantity=1),
        ]
        await async_order_item_class.bulk_create(items)
        count = await async_order_item_class.query().count()
        assert count == 2, "Expected count to be 2"

    async def test_explain(self, async_order_item_class):
        """explain() should return a non-empty plan list when supported."""
        if not async_order_item_class.backend().dialect.supports_explain_plan():
            pytest.skip("Backend dialect does not support explain plan")
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
        ]
        await async_order_item_class.bulk_create(items)
        result = await async_order_item_class.query().explain().aggregate()
        assert isinstance(result, list), "Expected explain() result to be a list"
        assert len(result) > 0, "Expected explain() result to be non-empty"