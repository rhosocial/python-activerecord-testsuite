# src/rhosocial/activerecord/testsuite/feature/basic/crud/test_composite_pk_crud_async.py
"""Async tests for CRUD operations on models with composite primary keys."""
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.errors import RecordNotFound


class TestAsyncCompositePKMeta:
    """Test async composite primary key metadata introspection."""

    async def test_is_composite_pk(self, async_order_item_class):
        """Composite primary key models should report is_composite_pk() as True."""
        assert async_order_item_class.is_composite_pk() is True, \
            "Expected is_composite_pk() to be True"

    async def test_primary_key_columns(self, async_order_item_class):
        """primary_key_columns() should return the column names of the key."""
        assert async_order_item_class.primary_key_columns() == ("order_id", "product_id"), \
            "Expected primary key columns to be order_id and product_id"

    async def test_primary_key_fields(self, async_order_item_class):
        """primary_key_fields() should return the field names of the key."""
        assert async_order_item_class.primary_key_fields() == ("order_id", "product_id"), \
            "Expected primary key fields to be order_id and product_id"

    async def test_primary_key(self, async_order_item_class):
        """primary_key() should return the primary key fields."""
        assert async_order_item_class.primary_key() == ("order_id", "product_id"), \
            "Expected primary key to be order_id and product_id"

    async def test_primary_key_single(self, async_order_class):
        """A single-column primary key should report a plain value rather than a tuple."""
        assert async_order_class.is_composite_pk() is False, \
            "Expected single-column key to be non-composite"
        assert async_order_class.primary_key() == "id", "Expected primary key to be 'id'"
        assert async_order_class.primary_key_columns() == ("id",), \
            "Expected primary key columns to be ('id',)"

    async def test_pk_auto_generated(self, async_order_item_class):
        """Composite keys should not be auto-generated."""
        assert async_order_item_class.__pk_auto_generated__ is False, \
            "Expected composite key to not be auto-generated"

class TestAsyncCompositePKInsert:
    """Test async inserting records with composite primary keys."""

    async def test_insert_and_is_new_record(self, async_order_item_class):
        """A new composite-key record should be marked new before save and not after."""
        item = async_order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        assert item.is_new_record is True, "Expected the record to be new before save"
        rows = await item.save()
        assert rows == 1, "Expected save() to affect 1 row"
        assert item.is_new_record is False, "Expected the record to no longer be new after save"

    async def test_insert_duplicate_pk(self, async_order_item_class):
        """Inserting a duplicate composite key should raise IntegrityError."""
        item = async_order_item_class(order_id=1, product_id=101, quantity=1)
        await item.save()
        dup = async_order_item_class(order_id=1, product_id=101, quantity=2)
        from rhosocial.activerecord.backend.errors import IntegrityError
        with pytest.raises(IntegrityError):
            await dup.save()

    async def test_missing_pk_field_raises(self, async_order_item_class):
        """Omitting a composite key field should raise a ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            async_order_item_class(order_id=1, quantity=3)

    async def test_backward_compat_single_pk(self, async_order_class):
        """A single-column primary key model should still save and load correctly."""
        order = async_order_class(total=Decimal("99.99"))
        await order.save()
        assert order.id is not None, "Expected the primary key to be assigned after save"
        assert order.is_new_record is False, "Expected the record to not be new after save"

    async def test_is_new_record_any_pk_none(self, async_order_item_class):
        """Setting any composite key field to None should mark the record as new."""
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        await item.save()
        item.order_id = None
        assert item.is_new_record is True, \
            "Expected the record to be new after clearing a key field"

class TestAsyncCompositePKFind:
    """Test async finding records by composite primary keys."""

    @pytest.fixture
    async def seeded_items(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        return items

    async def test_find_one_dict(self, seeded_items, async_order_item_class):
        """find_one() should accept a dict keyed by field names."""
        found = await async_order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None, "Expected to find the record"
        assert found.order_id == 1, "Expected order_id to be 1"
        assert found.product_id == 101, "Expected product_id to be 101"
        assert found.quantity == 2, "Expected quantity to be 2"

    async def test_find_one_tuple(self, seeded_items, async_order_item_class):
        """find_one() should accept a tuple of key values in column order."""
        found = await async_order_item_class.find_one((1, 101))
        assert found is not None, "Expected to find the record"
        assert found.order_id == 1, "Expected order_id to be 1"
        assert found.product_id == 101, "Expected product_id to be 101"

    async def test_find_one_not_found(self, async_order_item_class):
        """find_one() should return None when no record matches."""
        result = await async_order_item_class.find_one({"order_id": 999, "product_id": 999})
        assert result is None, "Expected find_one() to return None for missing key"

    async def test_find_one_or_fail_not_found(self, async_order_item_class):
        """find_one_or_fail() should raise RecordNotFound for a missing key."""
        with pytest.raises(RecordNotFound):
            await async_order_item_class.find_one_or_fail({"order_id": 999, "product_id": 999})

    async def test_find_all_dict_list(self, seeded_items, async_order_item_class):
        """find_all() should accept a list of dict keys."""
        results = await async_order_item_class.find_all([
            {"order_id": 1, "product_id": 101},
            {"order_id": 2, "product_id": 101},
        ])
        assert len(results) == 2, "Expected 2 records to be found"

    async def test_find_all_tuple_list(self, seeded_items, async_order_item_class):
        """find_all() should accept a list of tuple keys."""
        results = await async_order_item_class.find_all([(1, 101), (2, 101)])
        assert len(results) == 2, "Expected 2 records to be found"

    async def test_find_one_scalar_on_composite_pk_raises(self, async_order_item_class):
        """Passing a scalar to find_one() on a composite key should raise TypeError."""
        await async_order_item_class(order_id=1, product_id=101, quantity=1).save()
        with pytest.raises(TypeError):
            await async_order_item_class.find_one(1)

    async def test_backward_compat_find_one_scalar(self, async_order_class):
        """find_one() with a scalar should work for single-column keys."""
        order = async_order_class(total=Decimal("50.00"))
        await order.save()
        found = await async_order_class.find_one(order.id)
        assert found is not None, "Expected to find the record"
        assert found.total == Decimal("50.00"), "Expected the total to be preserved"

class TestAsyncCompositePKUpdateDelete:
    """Test async updating and deleting records with composite primary keys."""

    @pytest.fixture
    async def seeded_item(self, async_order_item_class):
        item = async_order_item_class(order_id=1, product_id=101, quantity=3, unit_price=Decimal("19.99"))
        await item.save()
        return item

    async def test_update_non_pk_field(self, seeded_item, async_order_item_class):
        """Updating a non-key field should not require changes to the key."""
        item = seeded_item
        item.quantity = 10
        await item.save()
        found = await async_order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found.quantity == 10, "Expected quantity to be updated to 10"

    async def test_delete(self, seeded_item, async_order_item_class):
        """Deleting a composite-key record should remove it from the database."""
        item = seeded_item
        rows = await item.delete()
        assert rows == 1, "Expected delete() to affect 1 row"
        found = await async_order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is None, "Expected the record to be gone after delete"

    async def test_delete_then_save_inserts(self, seeded_item, async_order_item_class):
        """Saving a deleted composite-key record should re-insert it."""
        item = seeded_item
        await item.delete()
        item.order_id = 1
        item.product_id = 101
        item.quantity = 5
        rows = await item.save()
        assert rows == 1, "Expected save() after delete to insert 1 row"
        found = await async_order_item_class.find_one({"order_id": 1, "product_id": 101})
        assert found is not None, "Expected the record to be re-inserted"
        assert found.quantity == 5, "Expected quantity to be 5 after re-insert"

class TestAsyncCompositePKMethods:
    """Test async composite primary key helper methods."""

    async def test_get_pk_value(self, async_order_item_class):
        """_get_pk_value() should return a dict keyed by field names."""
        item = async_order_item_class(order_id=1, product_id=101, quantity=3)
        pk = item._get_pk_value()
        assert pk == {"order_id": 1, "product_id": 101}, "Expected a dict of key fields"

    async def test_build_pk_where_predicate(self, async_order_item_class):
        """_build_pk_where_predicate() should build an SQLPredicate."""
        predicate = async_order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        from rhosocial.activerecord.backend.expression import SQLPredicate
        assert isinstance(predicate, SQLPredicate), "Expected an SQLPredicate instance"

    async def test_build_pk_where_predicate_none_raises(self, async_order_item_class):
        """A None key value should raise ValueError."""
        with pytest.raises(ValueError):
            async_order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": None})

    async def test_build_pk_where_predicate_missing_col(self, async_order_item_class):
        """A missing key field should raise ValueError."""
        with pytest.raises(ValueError):
            async_order_item_class._build_pk_where_predicate({"order_id": 1})

class TestAsyncCompositePKBulk:
    """Test async bulk operations on composite-key records."""

    @pytest.fixture
    async def seeded_items(self, async_order_item_class):
        items = [
            async_order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            async_order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            async_order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        await async_order_item_class.bulk_create(items)
        return items

    async def test_bulk_delete(self, seeded_items, async_order_item_class):
        """bulk_delete() should remove the specified records."""
        to_delete = await async_order_item_class.find_all([(1, 101), (1, 102)])
        await async_order_item_class.bulk_delete(to_delete)
        remaining = await async_order_item_class.find_all()
        assert len(remaining) == 1, "Expected 1 record to remain after bulk delete"

    async def test_bulk_update(self, seeded_items, async_order_item_class):
        """bulk_update() should update the specified fields on the records."""
        items = await async_order_item_class.find_all([(1, 101), (2, 101)])
        for item in items:
            item.quantity = 99
        await async_order_item_class.bulk_update(items, fields=["quantity"])
        refreshed = await async_order_item_class.find_all([(1, 101), (2, 101)])
        for r in refreshed:
            assert r.quantity == 99, "Expected quantity to be updated to 99"

    async def test_bulk_empty_list(self, async_order_item_class):
        """Bulk operations with an empty list should be no-ops."""
        await async_order_item_class.bulk_delete([])
        await async_order_item_class.bulk_update([], fields=["quantity"])

class TestAsyncCompositePKWithColumnMapping:
    """Test async composite primary key with UseColumn field-to-column mapping."""

    async def test_meta_is_composite_pk(self, async_mapped_order_item_class):
        """is_composite_pk() should be True for mapped composite keys."""
        assert async_mapped_order_item_class.is_composite_pk() is True, \
            "Expected is_composite_pk() to be True"

    async def test_meta_primary_key_columns(self, async_mapped_order_item_class):
        """primary_key_columns() should return the underlying column names."""
        assert async_mapped_order_item_class.primary_key_columns() == ("order_id", "product_id"), \
            "Expected column names to be order_id and product_id"

    async def test_meta_primary_key_fields(self, async_mapped_order_item_class):
        """primary_key_fields() should return the mapped field names."""
        assert async_mapped_order_item_class.primary_key_fields() == ("order_ref", "product_ref"), \
            "Expected field names to be order_ref and product_ref"

    async def test_meta_primary_key_field(self, async_mapped_order_item_class):
        """primary_key_field() should return the mapped field names."""
        assert async_mapped_order_item_class.primary_key_field() == ("order_ref", "product_ref"), \
            "Expected primary key fields to be order_ref and product_ref"

    async def test_meta_pk_auto_generated(self, async_mapped_order_item_class):
        """Mapped composite keys should not be auto-generated."""
        assert async_mapped_order_item_class.__pk_auto_generated__ is False, \
            "Expected the key to not be auto-generated"

    async def test_insert_and_is_new_record(self, async_mapped_order_item_class):
        """A mapped composite-key record should save and transition out of new state."""
        item = async_mapped_order_item_class(order_ref=1, product_ref=101, quantity=3,
                                       unit_price=Decimal("19.99"))
        assert item.is_new_record is True, "Expected the record to be new before save"
        rows = await item.save()
        assert rows == 1, "Expected save() to affect 1 row"
        assert item.is_new_record is False, "Expected the record to no longer be new after save"

    async def test_insert_duplicate_pk_raises(self, async_mapped_order_item_class):
        """Inserting a duplicate mapped composite key should raise IntegrityError."""
        item = async_mapped_order_item_class(order_ref=1, product_ref=101, quantity=1)
        await item.save()
        dup = async_mapped_order_item_class(order_ref=1, product_ref=101, quantity=2)
        from rhosocial.activerecord.backend.errors import IntegrityError
        with pytest.raises(IntegrityError):
            await dup.save()

    async def test_find_one_by_field_names(self, async_mapped_order_item_class):
        """find_one() should accept field names for a mapped composite key."""
        item = async_mapped_order_item_class(order_ref=10, product_ref=201, quantity=4,
                                       unit_price=Decimal("5.00"))
        await item.save()
        found = await async_mapped_order_item_class.find_one({"order_ref": 10, "product_ref": 201})
        assert found is not None, "Expected to find the record"
        assert found.order_ref == 10, "Expected order_ref to be 10"
        assert found.product_ref == 201, "Expected product_ref to be 201"
        assert found.quantity == 4, "Expected quantity to be 4"

    async def test_find_one_by_column_names(self, async_mapped_order_item_class):
        """find_one() should accept column names for a mapped composite key."""
        item = async_mapped_order_item_class(order_ref=20, product_ref=301, quantity=2,
                                       unit_price=Decimal("8.00"))
        await item.save()
        found = await async_mapped_order_item_class.find_one({"order_id": 20, "product_id": 301})
        assert found is not None, "Expected to find the record"
        assert found.order_ref == 20, "Expected order_ref to be 20"
        assert found.product_ref == 301, "Expected product_ref to be 301"

    async def test_find_one_tuple(self, async_mapped_order_item_class):
        """find_one() should accept a tuple of mapped key values in column order."""
        item = async_mapped_order_item_class(order_ref=30, product_ref=401, quantity=5,
                                       unit_price=Decimal("3.00"))
        await item.save()
        found = await async_mapped_order_item_class.find_one((30, 401))
        assert found is not None, "Expected to find the record"
        assert found.order_ref == 30, "Expected order_ref to be 30"
        assert found.product_ref == 401, "Expected product_ref to be 401"

    async def test_find_one_not_found(self, async_mapped_order_item_class):
        """find_one() should return None when no mapped record matches."""
        result = await async_mapped_order_item_class.find_one({"order_ref": 999, "product_ref": 999})
        assert result is None, "Expected find_one() to return None for missing key"

    async def test_find_all_by_field_names(self, async_mapped_order_item_class):
        """find_all() should accept a list of dict keys using field names."""
        items = [
            async_mapped_order_item_class(order_ref=40, product_ref=501, quantity=2,
                                    unit_price=Decimal("1.00")),
            async_mapped_order_item_class(order_ref=40, product_ref=502, quantity=3,
                                    unit_price=Decimal("2.00")),
        ]
        await async_mapped_order_item_class.bulk_create(items)
        results = await async_mapped_order_item_class.find_all([
            {"order_ref": 40, "product_ref": 501},
            {"order_ref": 40, "product_ref": 502},
        ])
        assert len(results) == 2, "Expected 2 records to be found"

    async def test_find_all_by_column_names(self, async_mapped_order_item_class):
        """find_all() should accept a list of dict keys using column names."""
        items = [
            async_mapped_order_item_class(order_ref=50, product_ref=601, quantity=1,
                                    unit_price=Decimal("10.00")),
            async_mapped_order_item_class(order_ref=50, product_ref=602, quantity=2,
                                    unit_price=Decimal("20.00")),
        ]
        await async_mapped_order_item_class.bulk_create(items)
        results = await async_mapped_order_item_class.find_all([
            {"order_id": 50, "product_id": 601},
            {"order_id": 50, "product_id": 602},
        ])
        assert len(results) == 2, "Expected 2 records to be found"

    async def test_find_all_tuple_list(self, async_mapped_order_item_class):
        """find_all() should accept a list of tuples for a mapped composite key."""
        items = [
            async_mapped_order_item_class(order_ref=60, product_ref=701, quantity=1,
                                    unit_price=Decimal("5.00")),
            async_mapped_order_item_class(order_ref=60, product_ref=702, quantity=2,
                                    unit_price=Decimal("6.00")),
        ]
        await async_mapped_order_item_class.bulk_create(items)
        results = await async_mapped_order_item_class.find_all([(60, 701), (60, 702)])
        assert len(results) == 2, "Expected 2 records to be found"

    async def test_update_non_pk_field(self, async_mapped_order_item_class):
        """Updating a non-key field on a mapped model should persist."""
        item = async_mapped_order_item_class(order_ref=70, product_ref=801, quantity=3,
                                       unit_price=Decimal("7.00"))
        await item.save()
        item.quantity = 99
        await item.save()
        found = await async_mapped_order_item_class.find_one({"order_ref": 70, "product_ref": 801})
        assert found is not None, "Expected to find the record"
        assert found.quantity == 99, "Expected quantity to be updated to 99"

    async def test_delete(self, async_mapped_order_item_class):
        """Deleting a mapped composite-key record should remove it."""
        item = async_mapped_order_item_class(order_ref=80, product_ref=901, quantity=1,
                                       unit_price=Decimal("15.00"))
        await item.save()
        rows = await item.delete()
        assert rows == 1, "Expected delete() to affect 1 row"
        found = await async_mapped_order_item_class.find_one((80, 901))
        assert found is None, "Expected the record to be gone after delete"

    async def test_get_pk_value_uses_column_names(self, async_mapped_order_item_class):
        """_get_pk_value() should return a dict keyed by column names."""
        item = async_mapped_order_item_class(order_ref=90, product_ref=1001, quantity=3)
        pk = item._get_pk_value()
        assert pk == {"order_id": 90, "product_id": 1001}, \
            "Expected the pk dict to be keyed by column names"

    async def test_find_one_scalar_raises(self, async_mapped_order_item_class):
        """Passing a scalar to find_one() on a mapped composite key should raise TypeError."""
        with pytest.raises(TypeError):
            await async_mapped_order_item_class.find_one(1)

    async def test_missing_pk_field_raises(self, async_mapped_order_item_class):
        """Omitting a mapped composite key field should raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            async_mapped_order_item_class(order_ref=1, quantity=3)

    async def test_is_new_record_any_pk_none(self, async_mapped_order_item_class):
        """Clearing a mapped key field should mark the record as new."""
        item = async_mapped_order_item_class(order_ref=100, product_ref=1101, quantity=3)
        await item.save()
        item.order_ref = None
        assert item.is_new_record is True, \
            "Expected the record to be new after clearing a key field"