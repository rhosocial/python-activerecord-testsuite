# src/rhosocial/activerecord/testsuite/feature/derived_field/test_derived_field_async.py
import pytest

from rhosocial.activerecord.backend.expression import Column, Literal


class TestAsyncDerivedFieldQuery:

    async def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        await p.save()
        return p

    @pytest.mark.asyncio
    async def test_find_all_derived_true(self, async_product_class):
        await self._insert(async_product_class, "A", 100.0, 5)
        results = await async_product_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0)
        assert results[0].total_value is None

    @pytest.mark.asyncio
    async def test_find_all_derived_list(self, async_product_class):
        await self._insert(async_product_class, "B", 50.0, 3)
        results = await async_product_class.find_all(derived=["discounted_price", "total_value"])
        assert results[0].discounted_price == pytest.approx(45.0)
        assert results[0].total_value == pytest.approx(150.0)

    @pytest.mark.asyncio
    async def test_find_one_derived(self, async_product_class):
        p = await self._insert(async_product_class, "C", 80.0, 4)
        result = await async_product_class.find_one(p.id, derived=True)
        assert result.discounted_price == pytest.approx(72.0)

    @pytest.mark.asyncio
    async def test_find_one_or_fail_derived(self, async_product_class):
        p = await self._insert(async_product_class, "C2", 80.0, 4)
        result = await async_product_class.find_one_or_fail(p.id, derived=True)
        assert result.discounted_price == pytest.approx(72.0)
        assert result.total_value is None

    @pytest.mark.asyncio
    async def test_find_one_or_fail_derived_list(self, async_product_class):
        p = await self._insert(async_product_class, "C3", 80.0, 4)
        result = await async_product_class.find_one_or_fail(p.id, derived=["discounted_price", "total_value"])
        assert result.discounted_price == pytest.approx(72.0)
        assert result.total_value == pytest.approx(320.0)

    @pytest.mark.asyncio
    async def test_find_all_derived_false(self, async_product_class):
        await self._insert(async_product_class, "D", 60.0, 1)
        results = await async_product_class.find_all()
        assert results[0].discounted_price is None

    @pytest.mark.asyncio
    async def test_extra_derived(self, async_product_class):
        await self._insert(async_product_class, "E", 100.0, 10)
        results = await async_product_class.find_all(
            extra_derived={"triple": lambda d: Column(d, "price") * Literal(d, 3)}
        )
        assert results[0].__dict__["triple"] == pytest.approx(300.0)


class TestAsyncDerivedFieldWithProxy:

    async def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        await p.save()
        return p

    @pytest.mark.asyncio
    async def test_proxy_derived_query(self, async_product_with_proxy_class):
        await self._insert(async_product_with_proxy_class, "P1", 100.0, 4)
        results = await async_product_with_proxy_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0)

    @pytest.mark.asyncio
    async def test_proxy_derived_all_fields(self, async_product_with_proxy_class):
        await self._insert(async_product_with_proxy_class, "P2", 200.0, 3)
        results = await async_product_with_proxy_class.find_all(
            derived=["discounted_price", "total_value"]
        )
        assert results[0].discounted_price == pytest.approx(180.0)
        assert results[0].total_value == pytest.approx(600.0)

    @pytest.mark.asyncio
    async def test_proxy_derived_read_only(self, async_product_with_proxy_class):
        await self._insert(async_product_with_proxy_class, "P3", 80.0, 1)
        instance = (await async_product_with_proxy_class.find_all(derived=True))[0]
        with pytest.raises(AttributeError):
            instance.discounted_price = 123.0


class TestAsyncDerivedFieldWithUseColumnAndAdapter:

    async def _insert(self, Model, name, price, quantity):
        p = Model(name=name, price=price, quantity=quantity)
        await p.save()
        return p

    @pytest.mark.asyncio
    async def test_use_column_alias(self, async_product_with_column_and_adapter_class):
        await self._insert(async_product_with_column_and_adapter_class, "UC1", 100.0, 5)
        results = await async_product_with_column_and_adapter_class.find_all(derived=True)
        assert results[0].discounted_price == pytest.approx(90.0)

    @pytest.mark.asyncio
    async def test_use_adapter_from_database(self, async_product_with_column_and_adapter_class):
        await self._insert(async_product_with_column_and_adapter_class, "UA1", 33.3, 3)
        results = await async_product_with_column_and_adapter_class.find_all(derived=["total_int"])
        assert results[0].total_int == 100
        assert isinstance(results[0].total_int, int)

    @pytest.mark.asyncio
    async def test_both_together(self, async_product_with_column_and_adapter_class):
        await self._insert(async_product_with_column_and_adapter_class, "CA1", 50.0, 4)
        results = await async_product_with_column_and_adapter_class.find_all(
            derived=["discounted_price", "total_int"]
        )
        assert results[0].discounted_price == pytest.approx(45.0)
        assert results[0].total_int == 200
