# src/rhosocial/activerecord/testsuite/feature/composite_pk/test_activerecord.py
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.errors import RecordNotFound
class TestAsyncCompositePKMeta:
    @pytest.mark.asyncio
    async def test_is_composite_pk(self, order_item_class):
        assert order_item_class.is_composite_pk() is True

    @pytest.mark.asyncio

    async def test_primary_key_columns(self, order_item_class):
        assert order_item_class.primary_key_columns() == ("order_id", "product_id")

    @pytest.mark.asyncio

    async def test_primary_key_fields(self, order_item_class):
        assert order_item_class.primary_key_fields() == ("order_id", "product_id")

    @pytest.mark.asyncio

    async def test_primary_key(self, order_item_class):
        assert order_item_class.primary_key() == ("order_id", "product_id")

    @pytest.mark.asyncio

    async def test_primary_key_single(self, order_class):
        assert order_class.is_composite_pk() is False
        assert order_class.primary_key() == "id"
        assert order_class.primary_key_columns() == ("id",)

    @pytest.mark.asyncio

    async def test_pk_auto_generated(self, order_item_class):
        assert order_item_class.__pk_auto_generated__ is False

class TestAsyncCompositePKInsert:
    @pytest.mark.asyncio
    async def test_insert_and_is_new_record(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        assert item.is_new_record is True
        rows = await item.save()
        assert rows == 1
        assert item.is_new_record is False

    @pytest.mark.asyncio

    async def test_insert_duplicate_pk(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=1)
        await item.save()
        dup = order_item_class(order_id=1, product_id=101, quantity=2)
        from rhosocial.activerecord.backend.errors import IntegrityError
        with pytest.raises(IntegrityError):
            await dup.save()

    @pytest.mark.asyncio

    async def test_missing_pk_field_raises(self, order_item_class):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            order_item_class(order_id=1, quantity=3)

    @pytest.mark.asyncio

    async def test_backward_compat_single_pk(self, order_class):
        order = order_class(total=Decimal("99.99"))
        await order.save()
        assert order.id is not None
        assert order.is_new_record is False

    @pytest.mark.asyncio

    async def test_is_new_record_any_pk_none(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        item.order_id = None
        assert item.is_new_record is True

class TestAsyncCompositePKFind:
    @pytest.fixture
    async def seeded_items(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    @pytest.mark.asyncio

    async def test_find_one_dict(self, seeded_items, order_item_class):
        found = await order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None
        assert found.order_id == 1
        assert found.product_id == 101
        assert found.quantity == 2

    @pytest.mark.asyncio

    async def test_find_one_tuple(self, seeded_items, order_item_class):
        found = await order_item_class.find_one((1, 101))
        assert found is not None
        assert found.order_id == 1
        assert found.product_id == 101

    @pytest.mark.asyncio

    async def test_find_one_not_found(self, order_item_class):
        result = await order_item_class.find_one({"order_id": 999, "product_id": 999})
        assert result is None

    @pytest.mark.asyncio

    async def test_find_one_or_fail_not_found(self, order_item_class):
        with pytest.raises(RecordNotFound):
            await order_item_class.find_one_or_fail({"order_id": 999, "product_id": 999})

    @pytest.mark.asyncio

    async def test_find_all_dict_list(self, seeded_items, order_item_class):
        results = await order_item_class.find_all([
            {"order_id": 1, "product_id": 101},
            {"order_id": 2, "product_id": 101},
        ])
        assert len(results) == 2

    @pytest.mark.asyncio

    async def test_find_all_tuple_list(self, seeded_items, order_item_class):
        results = await order_item_class.find_all([(1, 101), (2, 101)])
        assert len(results) == 2

    @pytest.mark.asyncio

    async def test_find_one_scalar_on_composite_pk_raises(self, order_item_class):
        order_item_class(order_id=1, product_id=101, quantity=1).save()
        with pytest.raises(TypeError):
            await order_item_class.find_one(1)

    @pytest.mark.asyncio

    async def test_backward_compat_find_one_scalar(self, order_class):
        order = order_class(total=Decimal("50.00"))
        await order.save()
        found = await order_class.find_one(order.id)
        assert found is not None
        assert found.total == Decimal("50.00")

class TestAsyncCompositePKUpdateDelete:
    @pytest.fixture
    async def seeded_item(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        await item.save()
        return item

    @pytest.mark.asyncio

    async def test_update_non_pk_field(self, seeded_item, order_item_class):
        item = seeded_item
        item.quantity = 10
        await item.save()
        found = await order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found.quantity == 10

    @pytest.mark.asyncio

    async def test_delete(self, seeded_item, order_item_class):
        item = seeded_item
        rows = await item.delete()
        assert rows == 1
        found = await order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is None

    @pytest.mark.asyncio

    async def test_delete_then_save_inserts(self, seeded_item, order_item_class):
        item = seeded_item
        await item.delete()
        item.order_id = 1
        item.product_id = 101
        item.quantity = 5
        rows = await item.save()
        assert rows == 1
        found = await order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None
        assert found.quantity == 5

class TestAsyncCompositePKMethods:
    @pytest.mark.asyncio
    async def test_get_pk_value(self, order_item_class):
        item = order_item_class(order_id=1, product_id=101, quantity=3)
        pk = item._get_pk_value()
        assert pk == {"order_id": 1, "product_id": 101}

    @pytest.mark.asyncio

    async def test_build_pk_where_predicate(self, order_item_class):
        predicate = order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        from rhosocial.activerecord.backend.expression import SQLPredicate
        assert isinstance(predicate, SQLPredicate)

    @pytest.mark.asyncio

    async def test_build_pk_where_predicate_none_raises(self, order_item_class):
        with pytest.raises(ValueError):
            order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": None})

    @pytest.mark.asyncio

    async def test_build_pk_where_predicate_missing_col(self, order_item_class):
        with pytest.raises(ValueError):
            order_item_class._build_pk_where_predicate({"order_id": 1})

class TestAsyncCompositePKBulk:
    @pytest.fixture
    async def seeded_items(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    @pytest.mark.asyncio

    async def test_bulk_delete(self, seeded_items, order_item_class):
        to_delete = await order_item_class.find_all([(1, 101), (1, 102)])
        order_item_class.bulk_delete(to_delete)
        remaining = await order_item_class.find_all()
        assert len(remaining) == 1

    @pytest.mark.asyncio

    async def test_bulk_update(self, seeded_items, order_item_class):
        items = await order_item_class.find_all([(1, 101), (2, 101)])
        for item in items:
            item.quantity = 99
        order_item_class.bulk_update(items, fields=["quantity"])
        refreshed = await order_item_class.find_all([(1, 101), (2, 101)])
        for r in refreshed:
            assert r.quantity == 99

    @pytest.mark.asyncio

    async def test_bulk_empty_list(self, order_item_class):
        order_item_class.bulk_delete([])
        order_item_class.bulk_update([], fields=["quantity"])

class TestAsyncCompositePKWithColumnMapping:
    """Test composite primary key with UseColumn field-to-column mapping."""

    @pytest.mark.asyncio

    async def test_meta_is_composite_pk(self, mapped_order_item_class):
        assert mapped_order_item_class.is_composite_pk() is True

    @pytest.mark.asyncio

    async def test_meta_primary_key_columns(self, mapped_order_item_class):
        assert mapped_order_item_class.primary_key_columns() == ("order_id", "product_id")

    @pytest.mark.asyncio

    async def test_meta_primary_key_fields(self, mapped_order_item_class):
        assert mapped_order_item_class.primary_key_fields() == ("order_ref", "product_ref")

    @pytest.mark.asyncio

    async def test_meta_primary_key_field(self, mapped_order_item_class):
        assert mapped_order_item_class.primary_key_field() == ("order_ref", "product_ref")

    @pytest.mark.asyncio

    async def test_meta_pk_auto_generated(self, mapped_order_item_class):
        assert mapped_order_item_class.__pk_auto_generated__ is False

    @pytest.mark.asyncio

    async def test_insert_and_is_new_record(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=1, product_ref=101, quantity=3,
                                       unit_price=Decimal("19.99"))
        assert item.is_new_record is True
        rows = await item.save()
        assert rows == 1
        assert item.is_new_record is False

    @pytest.mark.asyncio

    async def test_insert_duplicate_pk_raises(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=1, product_ref=101, quantity=1)
        await item.save()
        dup = mapped_order_item_class(order_ref=1, product_ref=101, quantity=2)
        from rhosocial.activerecord.backend.errors import IntegrityError
        with pytest.raises(IntegrityError):
            await dup.save()

    @pytest.mark.asyncio

    async def test_find_one_by_field_names(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=10, product_ref=201, quantity=4,
                                       unit_price=Decimal("5.00"))
        await item.save()
        found = await mapped_order_item_class.find_one({"order_ref": 10, "product_ref": 201})
        assert found is not None
        assert found.order_ref == 10
        assert found.product_ref == 201
        assert found.quantity == 4

    @pytest.mark.asyncio

    async def test_find_one_by_column_names(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=20, product_ref=301, quantity=2,
                                       unit_price=Decimal("8.00"))
        await item.save()
        found = await mapped_order_item_class.find_one({"order_id": 20, "product_id": 301})
        assert found is not None
        assert found.order_ref == 20
        assert found.product_ref == 301

    @pytest.mark.asyncio

    async def test_find_one_tuple(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=30, product_ref=401, quantity=5,
                                       unit_price=Decimal("3.00"))
        await item.save()
        found = await mapped_order_item_class.find_one((30, 401))
        assert found is not None
        assert found.order_ref == 30
        assert found.product_ref == 401

    @pytest.mark.asyncio

    async def test_find_one_not_found(self, mapped_order_item_class):
        result = await mapped_order_item_class.find_one({"order_ref": 999, "product_ref": 999})
        assert result is None

    @pytest.mark.asyncio

    async def test_find_all_by_field_names(self, mapped_order_item_class):
        items = [
            mapped_order_item_class(order_ref=40, product_ref=501, quantity=2,
                                    unit_price=Decimal("1.00")),
            mapped_order_item_class(order_ref=40, product_ref=502, quantity=3,
                                    unit_price=Decimal("2.00")),
        ]
        mapped_order_item_class.bulk_create(items)
        results = await mapped_order_item_class.find_all([
            {"order_ref": 40, "product_ref": 501},
            {"order_ref": 40, "product_ref": 502},
        ])
        assert len(results) == 2

    @pytest.mark.asyncio

    async def test_find_all_by_column_names(self, mapped_order_item_class):
        items = [
            mapped_order_item_class(order_ref=50, product_ref=601, quantity=1,
                                    unit_price=Decimal("10.00")),
            mapped_order_item_class(order_ref=50, product_ref=602, quantity=2,
                                    unit_price=Decimal("20.00")),
        ]
        mapped_order_item_class.bulk_create(items)
        results = await mapped_order_item_class.find_all([
            {"order_id": 50, "product_id": 601},
            {"order_id": 50, "product_id": 602},
        ])
        assert len(results) == 2

    @pytest.mark.asyncio

    async def test_find_all_tuple_list(self, mapped_order_item_class):
        items = [
            mapped_order_item_class(order_ref=60, product_ref=701, quantity=1,
                                    unit_price=Decimal("5.00")),
            mapped_order_item_class(order_ref=60, product_ref=702, quantity=2,
                                    unit_price=Decimal("6.00")),
        ]
        mapped_order_item_class.bulk_create(items)
        results = await mapped_order_item_class.find_all([(60, 701), (60, 702)])
        assert len(results) == 2

    @pytest.mark.asyncio

    async def test_update_non_pk_field(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=70, product_ref=801, quantity=3,
                                       unit_price=Decimal("7.00"))
        await item.save()
        item.quantity = 99
        await item.save()
        found = await mapped_order_item_class.find_one({"order_ref": 70, "product_ref": 801})
        assert found is not None
        assert found.quantity == 99

    @pytest.mark.asyncio

    async def test_delete(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=80, product_ref=901, quantity=1,
                                       unit_price=Decimal("15.00"))
        await item.save()
        rows = await item.delete()
        assert rows == 1
        found = await mapped_order_item_class.find_one((80, 901))
        assert found is None

    @pytest.mark.asyncio

    async def test_get_pk_value_uses_column_names(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=90, product_ref=1001, quantity=3)
        pk = item._get_pk_value()
        assert pk == {"order_id": 90, "product_id": 1001}

    @pytest.mark.asyncio

    async def test_find_one_scalar_raises(self, mapped_order_item_class):
        with pytest.raises(TypeError):
            await mapped_order_item_class.find_one(1)

    @pytest.mark.asyncio

    async def test_missing_pk_field_raises(self, mapped_order_item_class):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            mapped_order_item_class(order_ref=1, quantity=3)

    @pytest.mark.asyncio

    async def test_is_new_record_any_pk_none(self, mapped_order_item_class):
        item = mapped_order_item_class(order_ref=100, product_ref=1101, quantity=3)
        await item.save()
        item.order_ref = None
        assert item.is_new_record is True