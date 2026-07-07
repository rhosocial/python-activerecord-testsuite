# src/rhosocial/activerecord/testsuite/feature/composite_pk/test_active_query.py
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression import ComparisonPredicate, Literal
class TestAsyncActiveQueryCompositePK:
    @pytest.mark.asyncio
    async def test_async_where_pk_predicate(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        predicate = async_order_item_class._build_pk_where_predicate(
            {"order_id": 1, "product_id": 101}
        )
        result = await async_order_item_class.query().where(predicate).one()
        assert result is not None
        assert result.order_id == 1
        assert result.product_id == 101

    @pytest.mark.asyncio
    async def test_async_count(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2),
            async_order_item_class(order_id=1, product_id=102, quantity=1),
        ]
        await async_order_item_class.bulk_create(items)
        count = await async_order_item_class.query().count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_async_where_single_column(self, async_order_item_class):
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
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_async_where_and_condition(self, async_order_item_class):
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
        assert len(results) == 1
        assert results[0].product_id == 101

    @pytest.mark.asyncio
    async def test_async_order_limit(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=103, quantity=3, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        results = await async_order_item_class.query().order_by("product_id").limit(2).all()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_async_explain(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
        ]
        await async_order_item_class.bulk_create(items)
        result = await async_order_item_class.query().explain().aggregate()
        assert isinstance(result, list)
        assert len(result) > 0