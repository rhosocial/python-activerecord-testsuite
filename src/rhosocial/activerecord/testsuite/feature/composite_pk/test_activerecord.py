# src/rhosocial/activerecord/testsuite/feature/composite_pk/test_activerecord.py
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.errors import RecordNotFound


class TestCompositePKMeta:
    def test_is_composite_pk(self, order_item_class):
        assert order_item_class.is_composite_pk() is True

    def test_primary_key_columns(self, order_item_class):
        assert order_item_class.primary_key_columns() == ("order_id", "product_id")

    def test_primary_key_fields(self, order_item_class):
        assert order_item_class.primary_key_fields() == ("order_id", "product_id")

    def test_primary_key(self, order_item_class):
        assert order_item_class.primary_key() == ("order_id", "product_id")

    def test_primary_key_single(self, order_class):
        assert order_class.is_composite_pk() is False
        assert order_class.primary_key() == "id"
        assert order_class.primary_key_columns() == ("id",)

    def test_pk_auto_generated(self, order_item_class):
        assert order_item_class.__pk_auto_generated__ is False


class TestCompositePKInsert:
    def test_insert_and_is_new_record(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        assert item.is_new_record is True
        rows = item.save()
        assert rows == 1
        assert item.is_new_record is False

    def test_insert_duplicate_pk(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=1)
        item.save()
        dup = order_item_class(order_id=1, product_id=101, quantity=2)
        from rhosocial.activerecord.backend.errors import IntegrityError
        with pytest.raises(IntegrityError):
            dup.save()

    def test_missing_pk_field_raises(self, order_item_class):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            order_item_class(order_id=1, quantity=3)

    def test_backward_compat_single_pk(self, order_class):
        order = order_class(total=Decimal("99.99"))
        order.save()
        assert order.id is not None
        assert order.is_new_record is False

    def test_is_new_record_any_pk_none(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3)
        item.save()
        item.order_id = None
        assert item.is_new_record is True


class TestCompositePKFind:
    @pytest.fixture
    def seeded_items(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    def test_find_one_dict(self, seeded_items, order_item_class):
        found = order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None
        assert found.order_id == 1
        assert found.product_id == 101
        assert found.quantity == 2

    def test_find_one_tuple(self, seeded_items, order_item_class):
        found = order_item_class.find_one((1, 101))
        assert found is not None
        assert found.order_id == 1
        assert found.product_id == 101

    def test_find_one_not_found(self, order_item_class):
        result = order_item_class.find_one({"order_id": 999, "product_id": 999})
        assert result is None

    def test_find_one_or_fail_not_found(self, order_item_class):
        with pytest.raises(RecordNotFound):
            order_item_class.find_one_or_fail({"order_id": 999, "product_id": 999})

    def test_find_all_dict_list(self, seeded_items, order_item_class):
        results = order_item_class.find_all([
            {"order_id": 1, "product_id": 101},
            {"order_id": 2, "product_id": 101},
        ])
        assert len(results) == 2

    def test_find_all_tuple_list(self, seeded_items, order_item_class):
        results = order_item_class.find_all([(1, 101), (2, 101)])
        assert len(results) == 2

    def test_find_one_scalar_on_composite_pk_raises(self, order_item_class):
        order_item_class(order_id=1, product_id=101, quantity=1).save()
        with pytest.raises(TypeError):
            order_item_class.find_one(1)

    def test_backward_compat_find_one_scalar(self, order_class):
        order = order_class(total=Decimal("50.00"))
        order.save()
        found = order_class.find_one(order.id)
        assert found is not None
        assert found.total == Decimal("50.00")


class TestCompositePKUpdateDelete:
    @pytest.fixture
    def seeded_item(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        item.save()
        return item

    def test_update_non_pk_field(self, seeded_item, order_item_class):
        item = seeded_item
        item.quantity = 10
        item.save()
        found = order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found.quantity == 10

    def test_delete(self, seeded_item, order_item_class):
        item = seeded_item
        rows = item.delete()
        assert rows == 1
        found = order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is None

    def test_delete_then_save_inserts(self, seeded_item, order_item_class):
        item = seeded_item
        item.delete()
        item.order_id = 1
        item.product_id = 101
        item.quantity = 5
        rows = item.save()
        assert rows == 1
        found = order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None
        assert found.quantity == 5


class TestCompositePKMethods:
    def test_get_pk_value(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3)
        pk = item._get_pk_value()
        assert pk == {"order_id": 1, "product_id": 101}

    def test_build_pk_where_predicate(self, order_item_class):
        predicate = order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        from rhosocial.activerecord.backend.expression import SQLPredicate
        assert isinstance(predicate, SQLPredicate)

    def test_build_pk_where_predicate_none_raises(self, order_item_class):
        with pytest.raises(ValueError):
            order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": None})

    def test_build_pk_where_predicate_missing_col(self, order_item_class):
        with pytest.raises(KeyError):
            order_item_class._build_pk_where_predicate({"order_id": 1})


class TestCompositePKBulk:
    @pytest.fixture
    def seeded_items(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    def test_bulk_delete(self, seeded_items, order_item_class):
        to_delete = order_item_class.find_all([(1, 101), (1, 102)])
        order_item_class.bulk_delete(to_delete)
        remaining = order_item_class.find_all()
        assert len(remaining) == 1

    def test_bulk_update(self, seeded_items, order_item_class):
        items = order_item_class.find_all([(1, 101), (2, 101)])
        for item in items:
            item.quantity = 99
        order_item_class.bulk_update(items, fields=["quantity"])
        refreshed = order_item_class.find_all([(1, 101), (2, 101)])
        for r in refreshed:
            assert r.quantity == 99

    def test_bulk_empty_list(self, order_item_class):
        order_item_class.bulk_delete([])
        order_item_class.bulk_update([], fields=["quantity"])


class TestAsyncCompositePKCRUD:
    @pytest.mark.asyncio
    async def test_async_insert(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        assert item.is_new_record is True
        rows = await item.save()
        assert rows == 1
        assert item.is_new_record is False

    @pytest.mark.asyncio
    async def test_async_find_one(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        found = await async_order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None

    @pytest.mark.asyncio
    async def test_async_find_one_tuple(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        found = await async_order_item_class.find_one((1, 101))
        assert found is not None

    @pytest.mark.asyncio
    async def test_async_update(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        item.quantity = 10
        rows = await item.save()
        assert rows == 1
        await item.refresh()
        assert item.quantity == 10

    @pytest.mark.asyncio
    async def test_async_delete(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        rows = await item.delete()
        assert rows == 1
        found = await async_order_item_class.find_one((1, 101))
        assert found is None

    @pytest.mark.asyncio
    async def test_async_is_composite_pk(self, async_order_item_class):
        assert async_order_item_class.is_composite_pk() is True

    @pytest.mark.asyncio
    async def test_async_backward_compat(self, async_order_class):
        order = async_order_class(total=Decimal("99.99"))
        await order.save()
        assert order.id is not None
        found = await async_order_class.find_one(order.id)
        assert found is not None
