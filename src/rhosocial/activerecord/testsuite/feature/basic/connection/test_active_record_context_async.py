# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_active_record_context_async.py
"""
Test ActiveRecord context awareness with connection pool.

These tests verify that ActiveRecord models correctly use connection pool
context for backend resolution.
"""
import pytest

from rhosocial.activerecord.connection.pool import (
    get_current_backend,
    get_current_async_backend,
    get_current_transaction_backend,
    get_current_async_transaction_backend,
    get_current_connection_backend,
    get_current_async_connection_backend,
)
class TestAsyncActiveRecordContext:
    """Test asynchronous ActiveRecord context awareness."""

    @pytest.mark.asyncio
    async def test_backend_without_context_returns_class_backend(self, async_pool_and_model):
        """Test that backend() returns class backend without context."""
        pool, model = async_pool_and_model

        backend = model.backend()
        assert backend is model.__backend__

    @pytest.mark.asyncio
    async def test_backend_in_connection_context(self, async_pool_and_model):
        """Test that backend() returns connection backend in async connection context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            model_backend = model.backend()
            assert model_backend is conn_backend

            # Verify context functions
            assert get_current_async_backend() is conn_backend
            assert get_current_async_connection_backend() is conn_backend

    @pytest.mark.asyncio
    async def test_backend_in_transaction_context(self, async_pool_and_model):
        """Test that backend() returns transaction backend in async transaction context."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            model_backend = model.backend()
            assert model_backend is tx_backend

            # Verify context functions
            assert get_current_async_backend() is tx_backend
            assert get_current_async_transaction_backend() is tx_backend

    @pytest.mark.asyncio
    async def test_nested_connection_contexts(self, async_pool_and_model):
        """Test nested async connection contexts reuse same backend."""
        pool, model = async_pool_and_model

        async with pool.connection() as outer_conn:
            outer_backend = model.backend()
            assert outer_backend is outer_conn

            async with pool.connection() as inner_conn:
                inner_backend = model.backend()
                assert inner_backend is outer_backend
                assert inner_conn is outer_conn

    @pytest.mark.asyncio
    async def test_nested_transaction_contexts(self, async_pool_and_model):
        """Test nested async transaction contexts reuse same backend."""
        pool, model = async_pool_and_model

        async with pool.transaction() as outer_tx:
            outer_backend = model.backend()
            assert outer_backend is outer_tx

            async with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                assert inner_backend is outer_backend
                assert inner_tx is outer_tx

    @pytest.mark.asyncio
    async def test_connection_nested_in_transaction(self, async_pool_and_model):
        """Test async connection nested in transaction reuses transaction backend."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            tx_model_backend = model.backend()
            assert tx_model_backend is tx_backend

            async with pool.connection() as conn_backend:
                conn_model_backend = model.backend()
                assert conn_model_backend is tx_backend
                assert conn_backend is tx_backend

    @pytest.mark.asyncio
    async def test_transaction_nested_in_connection(self, async_pool_and_model):
        """Async transaction nested in a connection reuses the connection backend.

        Mirrors the sync test_transaction_nested_in_connection: opening a transaction
        inside an active connection context must reuse the same connection backend
        rather than acquiring a new one.
        """
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            conn_model_backend = model.backend()
            assert conn_model_backend is conn_backend

            async with pool.transaction() as tx_backend:
                tx_model_backend = model.backend()
                # Transaction inside a connection reuses the same connection backend
                assert tx_model_backend is conn_backend
                assert tx_backend is conn_backend

    @pytest.mark.asyncio
    async def test_deeply_nested_contexts(self, async_pool_and_model):
        """Async deeply nested contexts all resolve to the outermost backend.

        Mirrors the sync test_deeply_nested_contexts: a chain of
        connection -> connection -> transaction -> connection must keep resolving
        to the outermost backend at every level.
        """
        pool, model = async_pool_and_model

        async with pool.connection() as level1:
            assert model.backend() is level1

            async with pool.connection() as level2:
                assert model.backend() is level1
                assert level2 is level1

                async with pool.transaction() as level3:
                    assert model.backend() is level1
                    assert level3 is level1

                    async with pool.connection() as level4:
                        assert model.backend() is level1
                        assert level4 is level1

class TestSyncAsyncIsolation:
    """Test that sync and async contexts are properly isolated."""

    def test_sync_backend_without_context_is_none(self):
        """Test that get_current_backend() returns None without context."""
        assert get_current_backend() is None

    @pytest.mark.asyncio
    async def test_async_backend_without_context_is_none(self):
        """Test that get_current_async_backend() returns None without context."""
        assert get_current_async_backend() is None