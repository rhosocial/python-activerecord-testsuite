# src/rhosocial/activerecord/testsuite/feature/basic/test_bulk_operations.py
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

    @pytest.mark.asyncio
    async def test_basic_bulk_create(self, async_bulk_user_class):
        users = [
            async_bulk_user_class(name="Alice", age=25, email="alice@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="bob@test.com"),
            async_bulk_user_class(name="Charlie", age=35, email="charlie@test.com"),
        ]
        result = await async_bulk_user_class.bulk_create(users)

        assert len(result) == 3
        assert all(u.id is not None for u in result)

        db_users = await async_bulk_user_class.find_all()
        assert len(db_users) == 3

    @pytest.mark.asyncio
    async def test_bulk_create_empty_list(self, async_bulk_user_class):
        result = await async_bulk_user_class.bulk_create([])
        assert result == []

    @pytest.mark.asyncio
    async def test_bulk_create_non_new_record_raises(self, async_bulk_user_class):
        user = async_bulk_user_class(name="Alice", age=25)
        await user.save()

        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_create([user])

    @pytest.mark.asyncio
    async def test_bulk_create_with_batch_size(self, async_bulk_user_class):
        users = [async_bulk_user_class(name=f"User{i}", age=i) for i in range(10)]
        result = await async_bulk_user_class.bulk_create(users, batch_size=3)

        assert len(result) == 10
        db_users = await async_bulk_user_class.find_all()
        assert len(db_users) == 10

    @pytest.mark.asyncio
    async def test_bulk_create_updates_is_new_record(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        result = await async_bulk_user_class.bulk_create(users)
        assert not result[0].is_new_record

    @pytest.mark.asyncio
    async def test_bulk_create_validation_error_raises(self, async_bulk_user_class):
        user = async_bulk_user_class(name="Alice", age=25)
        object.__setattr__(user, "name", None)

        with pytest.raises(BulkValidationError):
            await async_bulk_user_class.bulk_create([user])

class TestAsyncBulkUpdate:

    @pytest.mark.asyncio
    async def test_basic_bulk_update(self, async_bulk_user_class):
        users = [
            async_bulk_user_class(name="Alice", age=25, email="alice@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="bob@test.com"),
        ]
        await async_bulk_user_class.bulk_create(users)

        users[0].age = 26
        users[1].age = 31
        affected = await async_bulk_user_class.bulk_update(users, ["age"])

        assert affected == 2
        reloaded = await async_bulk_user_class.find_all()
        ages = sorted(u.age for u in reloaded)
        assert ages == [26, 31]

    @pytest.mark.asyncio
    async def test_bulk_update_empty_list(self, async_bulk_user_class):
        assert await async_bulk_user_class.bulk_update([], ["name"]) == 0

    @pytest.mark.asyncio
    async def test_bulk_update_empty_fields_raises(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        with pytest.raises(ValueError, match="must not be empty"):
            await async_bulk_user_class.bulk_update(users, [])

    @pytest.mark.asyncio
    async def test_bulk_update_invalid_fields_raises(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        with pytest.raises(ValueError, match="Invalid field names"):
            await async_bulk_user_class.bulk_update(users, ["nonexistent_field"])

    @pytest.mark.asyncio
    async def test_bulk_update_new_record_raises(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_update(users, ["age"])

    @pytest.mark.asyncio
    async def test_bulk_update_multiple_fields(self, async_bulk_user_class):
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

        assert affected == 2
        reloaded = await async_bulk_user_class.find_all()
        names = sorted(u.name for u in reloaded)
        assert names == ["Alice Updated", "Bob Updated"]

    @pytest.mark.asyncio
    async def test_bulk_update_with_batch_size(self, async_bulk_user_class):
        users = [async_bulk_user_class(name=f"User{i}", age=i) for i in range(10)]
        await async_bulk_user_class.bulk_create(users)

        for u in users:
            u.age = u.age + 100
        affected = await async_bulk_user_class.bulk_update(users, ["age"], batch_size=3)

        assert affected == 10

    @pytest.mark.asyncio
    async def test_bulk_update_validation_error_raises(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        object.__setattr__(users[0], "name", None)

        with pytest.raises(BulkValidationError):
            await async_bulk_user_class.bulk_update(users, ["name"])

class TestAsyncBulkDelete:

    @pytest.mark.asyncio
    async def test_basic_bulk_delete(self, async_bulk_user_class):
        users = [
            async_bulk_user_class(name="Alice", age=25),
            async_bulk_user_class(name="Bob", age=30),
            async_bulk_user_class(name="Charlie", age=35),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.bulk_delete(users[:2])
        assert affected == 2
        remaining = await async_bulk_user_class.find_all()
        assert len(remaining) == 1
        assert remaining[0].name == "Charlie"

    @pytest.mark.asyncio
    async def test_bulk_delete_empty_list(self, async_bulk_user_class):
        assert await async_bulk_user_class.bulk_delete([]) == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_new_record_raises(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        with pytest.raises(BulkStateError):
            await async_bulk_user_class.bulk_delete(users)

    @pytest.mark.asyncio
    async def test_bulk_delete_clears_pk(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)
        await async_bulk_user_class.bulk_delete(users)
        assert users[0].id is None

class TestAsyncQueryUpdateAll:

    @pytest.mark.asyncio
    async def test_basic_update_all(self, async_bulk_user_class):
        users = [
            async_bulk_user_class(name="Alice", age=25, email="a@test.com"),
            async_bulk_user_class(name="Bob", age=30, email="b@test.com"),
            async_bulk_user_class(name="Charlie", age=35, email="c@test.com"),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 28
        ).update_all({"email": "updated@test.com"})
        assert affected == 2

        updated = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.email == "updated@test.com"
        ).all()
        assert len(updated) == 2

    @pytest.mark.asyncio
    async def test_update_all_no_where_raises(self, async_bulk_user_class):
        with pytest.raises(ValueError, match="requires a WHERE clause"):
            await async_bulk_user_class.query().update_all({"age": 0})

    @pytest.mark.asyncio
    async def test_update_all_accepts_column_key(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25, email="a@test.com")]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.id == users[0].id
        ).update_all(
            UpdateValues((async_bulk_user_class.c.email, "column@test.com"))
        )

        assert affected == 1
        reloaded = await async_bulk_user_class.find_one(users[0].id)
        assert reloaded.email == "column@test.com"

    @pytest.mark.asyncio
    async def test_update_all_accepts_stringifiable_key(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25, email="a@test.com")]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.id == users[0].id
        ).update_all(
            {ColumnNameKey("email"): "object-key@test.com"}
        )

        assert affected == 1
        reloaded = await async_bulk_user_class.find_one(users[0].id)
        assert reloaded.email == "object-key@test.com"

class TestAsyncQueryDeleteAll:

    @pytest.mark.asyncio
    async def test_basic_delete_all(self, async_bulk_user_class):
        users = [
            async_bulk_user_class(name="Alice", age=25),
            async_bulk_user_class(name="Bob", age=30),
            async_bulk_user_class(name="Charlie", age=35),
        ]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 28
        ).delete_all()
        assert affected == 2

        remaining = await async_bulk_user_class.find_all()
        assert len(remaining) == 1
        assert remaining[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_delete_all_no_where_raises(self, async_bulk_user_class):
        with pytest.raises(ValueError, match="requires a WHERE clause"):
            await async_bulk_user_class.query().delete_all()

    @pytest.mark.asyncio
    async def test_delete_all_no_matches(self, async_bulk_user_class):
        users = [async_bulk_user_class(name="Alice", age=25)]
        await async_bulk_user_class.bulk_create(users)

        affected = await async_bulk_user_class.query().where(
            async_bulk_user_class.c.age > 100
        ).delete_all()
        assert affected == 0
        assert len(await async_bulk_user_class.find_all()) == 1