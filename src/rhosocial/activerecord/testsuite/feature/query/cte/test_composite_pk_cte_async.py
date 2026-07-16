# src/rhosocial/activerecord/testsuite/feature/query/cte/test_composite_pk_cte_async.py
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
class TestAsyncCTEQueryCompositePK:
    async def test_cte_aggregate(self, async_order_item_class):
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
        assert len(result) == 2

    async def test_cte_pk_filter(self, async_order_item_class):
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
        assert len(result) == 1

    async def test_cte_unsupported_backend(self, async_order_item_class):
        backend = async_order_item_class.backend()
        dialect = backend.dialect
        if dialect.supports_basic_cte():
            pytest.skip("Backend supports CTE, can't test unsupported path")

        from rhosocial.activerecord.query import AsyncCTEQuery
        with pytest.raises(UnsupportedFeatureError):
            cte = AsyncCTEQuery(backend)