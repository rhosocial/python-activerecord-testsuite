# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_active_record_crud.py
"""
Test ActiveRecord CRUD operations with connection pool.

These tests verify that CRUD operations work correctly within
connection pool contexts.
"""
import pytest


class TestSyncActiveRecordCRUD:
    """Test synchronous ActiveRecord CRUD with connection pool."""

    def test_create_in_transaction(self, sync_pool_for_crud):
        """Test model create() in transaction context."""
        pool, model = sync_pool_for_crud

        with pool.transaction() as backend:
            # Insert data
            instance = model(name="Alice", email="alice@test.com")
            instance.save()

        # Verify committed
        with pool.connection() as backend:
            result = backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 1
            assert result[0]['name'] == "Alice"

    def test_update_in_transaction(self, sync_pool_for_crud):
        """Test model update in transaction context."""
        pool, model = sync_pool_for_crud

        # Create user first
        with pool.connection() as backend:
            backend.execute("INSERT INTO test_users (name, email) VALUES ('Bob', 'bob@test.com')")

        # Update in transaction
        with pool.transaction() as backend:
            backend.execute("UPDATE test_users SET name = 'Robert' WHERE name = 'Bob'")

        # Verify updated
        with pool.connection() as backend:
            result = backend.fetch_all("SELECT * FROM test_users WHERE name = 'Robert'")
            assert len(result) == 1

    def test_delete_in_transaction(self, sync_pool_for_crud):
        """Test model delete in transaction context."""
        pool, model = sync_pool_for_crud

        # Create user first
        with pool.connection() as backend:
            backend.execute("INSERT INTO test_users (name, email) VALUES ('Charlie', 'charlie@test.com')")

        # Delete in transaction
        with pool.transaction() as backend:
            backend.execute("DELETE FROM test_users WHERE name = 'Charlie'")

        # Verify deleted
        with pool.connection() as backend:
            result = backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 0

    def test_transaction_rollback_on_create(self, sync_pool_for_crud):
        """Test that create is rolled back on error."""
        pool, model = sync_pool_for_crud

        try:
            with pool.transaction() as backend:
                backend.execute("INSERT INTO test_users (name, email) VALUES ('Dave', 'dave@test.com')")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify rollback
        with pool.connection() as backend:
            result = backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 0

    def test_nested_transaction_reuses_connection(self, sync_pool_for_crud):
        """Test that nested transactions reuse the same connection."""
        pool, model = sync_pool_for_crud

        with pool.transaction() as outer_tx:
            outer_backend = model.backend()

            # Nested transaction should reuse connection
            with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                assert inner_backend is outer_backend

                inner_backend.execute("INSERT INTO test_users (name, email) VALUES ('Eve', 'eve@test.com')")

        # Verify committed
        with pool.connection() as backend:
            result = backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 1


class TestAsyncActiveRecordCRUD:
    """Test asynchronous ActiveRecord CRUD with connection pool."""

    @pytest.mark.asyncio
    async def test_create_in_transaction(self, async_pool_for_crud):
        """Test async model create() in transaction context."""
        pool, model = async_pool_for_crud

        async with pool.transaction() as backend:
            await backend.execute("INSERT INTO test_users (name, email) VALUES ('Alice', 'alice@test.com')")

        # Verify committed
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_create(self, async_pool_for_crud):
        """Test that async create is rolled back on error."""
        pool, model = async_pool_for_crud

        try:
            async with pool.transaction() as backend:
                await backend.execute("INSERT INTO test_users (name, email) VALUES ('Dave', 'dave@test.com')")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify rollback
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_nested_transaction_reuses_connection(self, async_pool_for_crud):
        """Test that nested async transactions reuse the same connection."""
        pool, model = async_pool_for_crud

        async with pool.transaction() as outer_tx:
            outer_backend = model.backend()

            async with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                assert inner_backend is outer_backend

                await inner_backend.execute("INSERT INTO test_users (name, email) VALUES ('Eve', 'eve@test.com')")

        # Verify committed
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 1
