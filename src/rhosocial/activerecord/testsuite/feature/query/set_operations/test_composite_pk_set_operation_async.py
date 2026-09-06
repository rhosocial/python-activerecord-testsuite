# src/rhosocial/activerecord/testsuite/feature/query/set_operations/test_composite_pk_set_operation_async.py
"""Async tests for set operations on models with a composite primary key."""

from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError


class TestAsyncSetOperationCompositePK:
    """Async tests for UNION, INTERSECT, and EXCEPT on composite primary key queries."""

    @pytest.fixture
    async def seeded(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
            async_order_item_class(order_id=2, product_id=103, quantity=3, unit_price=Decimal("25.00")),
        ]
        await async_order_item_class.bulk_create(items)
        return items


    async def test_union(self, seeded, async_order_item_class):
        """Test that UNION combines results from composite primary key queries."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_union():
            pytest.skip("Backend does not support UNION")

        q1 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        )
        q2 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 2, "product_id": 101})
        )
        result = await q1.union(q2).aggregate()
        assert len(result) == 2, "expected 2 results"


    async def test_intersect(self, seeded, async_order_item_class):
        """Test that INTERSECT returns overlapping composite primary key results."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_intersect():
            pytest.skip("Backend does not support INTERSECT")

        q1 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        )
        q2 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 2, "product_id": 101})
        )
        result = await q1.intersect(q2).aggregate()
        assert len(result) == 0  # No overlap


    async def test_except_(self, seeded, async_order_item_class):
        """Test that EXCEPT returns the difference of composite primary key queries."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_except():
            pytest.skip("Backend does not support EXCEPT")

        q1 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 2, "product_id": 101})
        )
        q2 = async_order_item_class.query().where(
            async_order_item_class._build_pk_where_predicate({"order_id": 2, "product_id": 101})
        )
        # EXCEPT of same set should yield empty
        result = await q1.except_(q2).aggregate()
        assert len(result) == 0, "expected 0 results"
