# src/rhosocial/activerecord/testsuite/feature/basic/bulk_crud/test_bulk_operations_async.py
"""Tests for bulk operations (bulk_create, bulk_update, bulk_delete, update_all, delete_all)."""

import pytest

from rhosocial.activerecord.backend.errors import BulkStateError, BulkValidationError


class ColumnNameKey:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

class UpdateValues:
    def __init__(self, *items):
        self._items = items

    def items(self):
        return self._items

class TestAsyncBulkCreate:
    """Test bulk_create in asynchronous mode."""

    async def test_basic_bulk_create(self, async_bulk_user_class):
        """bulk_create should insert multiple new records and return them with assigned ids."""
        users = [
            async_bulk_user_class(name="Alice", age=25, email="alice@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="bob@test.com"),
            async_bulk_user_class(name="Charlie", age=35, email="charlie@test.com"),
        ]
        result = await async_bulk_user_class.bulk_create(users)

        assert len(result) == 3, "Expected 3 records to be returned"
        assert all(u.id is not None for u in result), "Expected every returned record to have an id"

        db_users = await async_bulk_user_class.find_all()
        assert len(db_users) == 3, "Expected 3 records to be persisted"

    async def test_bulk_create_empty_list(self, async_bulk_user_class):
        """bulk_create with an empty list should return an empty list."""
        result = await async_bulk_user_class.bulk_create([])
        assert result == [], "Expected an empty list result for an empty input"

    async def test_bulk_create_non_new_record_raises(self, async_bulk_user_class):
        """bulk_create should reject records that are not new."""
        user = async_bulk_user_class(name="Alice", age=25)
        await user.save()

        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_create([user])

    async def test_bulk_create_with_batch_size(self, async_bulk_user_class):
        """bulk_create should honor the batch_size argument for chunked insertion."""
        users = [async_bulk_user_class(name=f"User{i}", age=i) for i in range(10)]
        result = await async_bulk_user_class.bulk_create(users, batch_size=3)

        assert len(result) == 10, "Expected 10 records to be returned"
        db_users = await async_bulk_user_class.find_all()
        assert len(db_users) == 10, "Expected 10 records to be persisted"

    async def test_bulk_create_updates_is_new_record(self, async_bulk_user_class):
        """bulk_create should mark returned records as no longer new."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        result = await async_bulk_user_class.bulk_create(users)
        assert not result[0].is_new_record, \
            "Expected the record to no longer be new after bulk_create"

    async def test_bulk_create_validation_error_raises(self, async_bulk_user_class):
        """bulk_create should raise BulkValidationError for invalid records."""
        user = async_bulk_user_class(name="Alice", age=25)
        object.__setattr__(user, "name", None)

        with pytest.raises(BulkValidationError):
            await async_bulk_user_class.bulk_create([user])

class TestAsyncBulkUpdate:
    """Test bulk_update in asynchronous mode."""

    async def test_basic_bulk_update(self, async_bulk_user_class):
        """bulk_update should persist updates across multiple records."""
        users = [
            async_bulk_user_class(name="Alice", age=25, email="alice@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="bob@test.com"),
        ]
        await async_bulk_user_class.bulk_create(users)

        users[0].age = 26
        users[1].age = 31
        affected = await async_bulk_user_class.bulk_update(users, ["age"])

        assert affected == 2, "Expected 2 records to be updated"
        reloaded = await async_bulk_user_class.find_all()
        ages = sorted(u.age for u in reloaded)
        assert ages == [26, 31], "Expected reloaded ages to be [26, 31]"

    async def test_bulk_update_empty_list(self, async_bulk_user_class):
        """bulk_update with an empty list should return 0 affected rows."""
        assert await async_bulk_user_class.bulk_update([], ["name"]) == 0, \
            "Expected 0 rows affected"

    async def test_bulk_update_empty_fields_raises(self, async_bulk_user_class):
        """bulk_update should reject an empty fields list."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        with pytest.raises(ValueError, match="must not be empty"):
            await async_bulk_user_class.bulk_update(users, [])

    async def test_bulk_update_invalid_fields_raises(self, async_bulk_user_class):
        """bulk_update should reject fields that are not on the model."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        with pytest.raises(ValueError, match="Invalid field names"):
            await async_bulk_user_class.bulk_update(users, ["nonexistent_field"])

    async def test_bulk_update_new_record_raises(self, async_bulk_user_class):
        """bulk_update should reject records that are still new (unsaved)."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_update(users, ["age"])

    async def test_bulk_update_multiple_fields(self, async_bulk_user_class):
        """bulk_update should accept and apply multiple field names."""
        users = [
            async_bulk_user_class(name="Alice", age=25, email="old@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="old@test.com"),
        ]
        await async_bulk_user_class.bulk_create(users)

        users[0].name = "Alice Updated"
        users[0].email = "new@test.com"
        users[1].name = "Bob Updated"
        users[1].email = "new2@test.com"
        affected = await async_bulk_user_class.bulk_update(users, ["name", "email"])

        assert affected == 2, "Expected 2 records to be updated"
        reloaded = await async_bulk_user_class.find_all()
        names = sorted(u.name for u in reloaded)
        assert names == ["Alice Updated", "Bob Updated"], \
            "Expected updated names to be reflected after bulk_update"

    async def test_bulk_update_with_batch_size(self, async_bulk_user_class):
        """bulk_update should honor the batch_size argument for chunked updates."""
        users = [async_bulk_user_class(name=f"User{i}", age=i) for i in range(10)]
        await async_bulk_user_class.bulk_create(users)

        for u in users:
            u.age = u.age + 100
        affected = await async_bulk_user_class.bulk_update(users, ["age"], batch_size=3)

        assert affected == 10, "Expected 10 records to be updated"

    async def test_bulk_update_validation_error_raises(self, async_bulk_user_class):
        """bulk_update should raise BulkValidationError when a record is invalid."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        object.__setattr__(users[0], "name", None)

        with pytest.raises(BulkValidationError):
            await async_bulk_user_class.bulk_update(users, ["name"])

class TestAsyncBulkDelete:
    """Test bulk_delete in asynchronous mode."""

    async def test_basic_bulk_delete(self, async_bulk_user_class):
        """bulk_delete should remove the specified records and leave the rest."""
        users = [
            async_bulk_user_class(name="Alice", age=25),
            async_bulk_user_class(name="Bob", age=30),
            async_bulk_user_class(name="Charlie", age=35),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.bulk_delete(users[:2])
        assert affected == 2, "Expected 2 records to be deleted"
        remaining = await async_bulk_user_class.find_all()
        assert len(remaining) == 1, "Expected 1 record to remain"
        assert remaining[0].name == "Charlie", "Expected the remaining record to be 'Charlie'"

    async def test_bulk_delete_empty_list(self, async_bulk_user_class):
        """bulk_delete with an empty list should return 0 affected rows."""
        assert await async_bulk_user_class.bulk_delete([]) == 0, "Expected 0 rows affected"

    async def test_bulk_delete_new_record_raises(self, async_bulk_user_class):
        """bulk_delete should reject records that are still new (unsaved)."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_delete(users)

    async def test_bulk_delete_clears_pk(self, async_bulk_user_class):
        """bulk_delete should clear the primary key on the deleted instances."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        await async_bulk_user_class.bulk_delete(users)
        assert users[0].id is None, "Expected the deleted record's id to be cleared"

class TestAsyncQueryUpdateAll:
    """Test QuerySet.update_all in asynchronous mode."""

    async def test_basic_update_all(self, async_bulk_user_class):
        """update_all should update records matching the WHERE clause."""
        users = [
            async_bulk_user_class(name="Alice", age=25, email="a@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="b@test.com"),
            async_bulk_user_class(name="Charlie", age=35, email="c@test.com"),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 28
        ).update_all({"email": "updated@test.com"})
        assert affected == 2, "Expected 2 records to be updated"

        updated = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.email == "updated@test.com"
        ).all()
        assert len(updated) == 2, "Expected 2 records to match the updated email"

    async def test_update_all_no_where_raises(self, async_bulk_user_class):
        """update_all without a WHERE clause should raise ValueError."""
        with pytest.raises(ValueError, match="requires a WHERE clause"):
            await async_bulk_user_class.query().update_all({"age": 0})

    async def test_update_all_accepts_column_key(self, async_bulk_user_class):
        """update_all should accept UpdateValues containing Column references."""
        users = [async_bulk_user_class(name="Alice", age=25, email="a@test.com")]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.id == users[0].id
        ).update_all(
            UpdateValues((async_bulk_user_class.c.email, "column@test.com"))
        )

        assert affected == 1, "Expected 1 record to be updated"
        reloaded = await async_bulk_user_class.find_one(users[0].id)
        assert reloaded.email == "column@test.com", \
            "Expected the email to be updated to 'column@test.com'"

    async def test_update_all_accepts_stringifiable_key(self, async_bulk_user_class):
        """update_all should accept dict keys whose __str__ yields a column name."""
        users = [async_bulk_user_class(name="Alice", age=25, email="a@test.com")]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.id == users[0].id
        ).update_all(
            {ColumnNameKey("email"): "object-key@test.com"}
        )

        assert affected == 1, "Expected 1 record to be updated"
        reloaded = await async_bulk_user_class.find_one(users[0].id)
        assert reloaded.email == "object-key@test.com", \
            "Expected the email to be updated to 'object-key@test.com'"

class TestAsyncQueryDeleteAll:
    """Test QuerySet.delete_all in asynchronous mode."""

    async def test_basic_delete_all(self, async_bulk_user_class):
        """delete_all should remove records matching the WHERE clause."""
        users = [
            async_bulk_user_class(name="Alice", age=25),
            async_bulk_user_class(name="Bob", age=30),
            async_bulk_user_class(name="Charlie", age=35),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 28
        ).delete_all()
        assert affected == 2, "Expected 2 records to be deleted"

        remaining = await async_bulk_user_class.find_all()
        assert len(remaining) == 1, "Expected 1 record to remain"
        assert remaining[0].name == "Alice", "Expected the remaining record to be 'Alice'"

    async def test_delete_all_no_where_raises(self, async_bulk_user_class):
        """delete_all without a WHERE clause should raise ValueError."""
        with pytest.raises(ValueError, match="requires a WHERE clause"):
            await async_bulk_user_class.query().delete_all()

    async def test_delete_all_no_matches(self, async_bulk_user_class):
        """delete_all should return 0 and leave records intact when nothing matches."""
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 100
        ).delete_all()
        assert affected == 0, "Expected 0 records to be deleted"
        assert len(await async_bulk_user_class.find_all()) == 1, \
            "Expected the original record to remain"