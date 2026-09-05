# src/rhosocial/activerecord/testsuite/feature/query/cte/test_composite_pk_cte_async.py
"""Tests for async CTE query operations on models with composite primary keys."""
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
class TestAsyncCTEQueryCompositePK:
    """Test async CTE query operations against models with composite primary keys."""

    async def test_cte_aggregate(self, async_order_item_class):
        """An async CTE wrapping the base composite-key query should aggregate over filtered rows."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_basic_cte():
            pytest.skip("Backend does not support CTE")

        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2),
            async_order_item_class(order_id=1, product_id=102, quantity=1),
        ]
        await async_order_item_class.bulk_create(items)

        from rhosocial.activerecord.query import AsyncCTEQuery
        from rhosocial.activerecord.backend.expression import Column

        base = async_order_item_class.query()
        cte = AsyncCTEQuery(backend)
        cte.with_cte("order_summary", base)
        result = await cte.from_cte("order_summary").select(
            Column(dialect, "order_id")
        ).where(Column(dialect, "order_id") == 1).aggregate()
        assert len(result) == 2, "Expected 2 aggregated rows for order_id == 1"

    async def test_cte_pk_filter(self, async_order_item_class):
        """An async CTE built on the composite key predicate should return the matching row."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_basic_cte():
            pytest.skip("Backend does not support CTE")

        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2),
            async_order_item_class(order_id=1, product_id=102, quantity=1),
        ]
        await async_order_item_class.bulk_create(items)

        from rhosocial.activerecord.query import AsyncCTEQuery

        predicate = async_order_item_class._build_pk_where_predicate(
            {"order_id": 1, "product_id": 101}
        )
        base = async_order_item_class.query().where(predicate)
        cte = AsyncCTEQuery(backend)
        cte.with_cte("single_item", base)
        result = await cte.from_cte("single_item").aggregate()
        assert len(result) == 1, "Expected 1 CTE row for the composite key"

    async def test_cte_unsupported_backend(self, async_order_item_class):
        """AsyncCTEQuery should raise UnsupportedFeatureError when the backend lacks CTE."""
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if dialect.supports_basic_cte():
            pytest.skip("Backend supports CTE, can't test unsupported path")

        from rhosocial.activerecord.query import AsyncCTEQuery
        with pytest.raises(UnsupportedFeatureError):
            cte = AsyncCTEQuery(backend)