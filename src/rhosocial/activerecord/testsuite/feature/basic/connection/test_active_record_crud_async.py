# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_active_record_crud.py
"""
Test ActiveRecord CRUD operations with connection pool.

These tests verify that CRUD operations work correctly within
connection pool contexts.
"""
import pytest
from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType


def execute_sql(backend, sql: str, params=None):
    """Helper to execute SQL with proper options."""
    sql_upper = sql.upper().strip()
    if 'CREATE' in sql_upper or 'DROP' in sql_upper or 'ALTER' in sql_upper:
        stmt_type = StatementType.DDL
    elif sql_upper.startswith('SELECT'):
        stmt_type = StatementType.DQL
    else:
        stmt_type = StatementType.DML
    options = ExecutionOptions(stmt_type=stmt_type)
    return backend.execute(sql, params or (), options=options)


async def async_execute_sql(backend, sql: str, params=None):
    """Helper to execute SQL asynchronously with proper options."""
    sql_upper = sql.upper().strip()
    if 'CREATE' in sql_upper or 'DROP' in sql_upper or 'ALTER' in sql_upper:
        stmt_type = StatementType.DDL
    elif sql_upper.startswith('SELECT'):
        stmt_type = StatementType.DQL
    else:
        stmt_type = StatementType.DML
    options = ExecutionOptions(stmt_type=stmt_type)
    return await backend.execute(sql, params or (), options=options)
class TestAsyncActiveRecordCRUD:
    """Test asynchronous ActiveRecord CRUD with connection pool."""

    @pytest.mark.asyncio
    async def test_create_in_transaction(self, async_pool_for_crud):
        """Test async model create() in transaction context."""
        pool, model = async_pool_for_crud

        async with pool.transaction() as backend:
            await async_execute_sql(backend, "INSERT INTO test_users (name, email) VALUES ('Alice', 'alice@test.com')")

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
                await async_execute_sql(backend, "INSERT INTO test_users (name, email) VALUES ('Dave', 'dave@test.com')")
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

                await async_execute_sql(inner_backend, "INSERT INTO test_users (name, email) VALUES ('Eve', 'eve@test.com')")

        # Verify committed
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_in_transaction(self, async_pool_for_crud):
        """Test async model update in transaction context."""
        pool, model = async_pool_for_crud

        # Create user first
        async with pool.connection() as backend:
            await async_execute_sql(backend, "INSERT INTO test_users (name, email) VALUES ('Bob', 'bob@test.com')")

        # Update in transaction
        async with pool.transaction() as backend:
            await async_execute_sql(backend, "UPDATE test_users SET name = 'Robert' WHERE name = 'Bob'")

        # Verify updated
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users WHERE name = 'Robert'")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_in_transaction(self, async_pool_for_crud):
        """Test async model delete in transaction context."""
        pool, model = async_pool_for_crud

        # Create user first
        async with pool.connection() as backend:
            await async_execute_sql(backend, "INSERT INTO test_users (name, email) VALUES ('Charlie', 'charlie@test.com')")

        # Delete in transaction
        async with pool.transaction() as backend:
            await async_execute_sql(backend, "DELETE FROM test_users WHERE name = 'Charlie'")

        # Verify deleted
        async with pool.connection() as backend:
            result = await backend.fetch_all("SELECT * FROM test_users")
            assert len(result) == 0