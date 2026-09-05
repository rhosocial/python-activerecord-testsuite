# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_active_record_context_async.py
"""
Test ActiveRecord context awareness with connection pool.

These tests verify that ActiveRecord models correctly use connection pool
context for backend resolution.
"""

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

    async def test_backend_without_context_returns_class_backend(self, async_pool_and_model):
        """Test that backend() returns class backend without context."""
        pool, model = async_pool_and_model

        backend = model.backend()
        assert backend is model.__backend__, \
            "Expected backend() to return the model's class backend outside any context"

    async def test_backend_in_connection_context(self, async_pool_and_model):
        """Test that backend() returns connection backend in async connection context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            model_backend = model.backend()
            assert model_backend is conn_backend, \
                "Expected backend() to return the connection backend inside an async context"

            # Verify context functions
            assert get_current_async_backend() is conn_backend, \
                "Expected get_current_async_backend() to return the connection backend"
            assert get_current_async_connection_backend() is conn_backend, \
                "Expected get_current_async_connection_backend() to return the connection backend"

    async def test_backend_in_transaction_context(self, async_pool_and_model):
        """Test that backend() returns transaction backend in async transaction context."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            model_backend = model.backend()
            assert model_backend is tx_backend, \
                "Expected backend() to return the transaction backend inside an async context"

            # Verify context functions
            assert get_current_async_backend() is tx_backend, \
                "Expected get_current_async_backend() to return the transaction backend"
            assert get_current_async_transaction_backend() is tx_backend, \
                "Expected get_current_async_transaction_backend() to return the transaction backend"

    async def test_nested_connection_contexts(self, async_pool_and_model):
        """Test nested async connection contexts reuse same backend."""
        pool, model = async_pool_and_model

        async with pool.connection() as outer_conn:
            outer_backend = model.backend()
            assert outer_backend is outer_conn, \
                "Expected backend() to return the outer connection backend"

            async with pool.connection() as inner_conn:
                inner_backend = model.backend()
                assert inner_backend is outer_backend, \
                    "Expected inner backend to reuse the outer connection backend"
                assert inner_conn is outer_conn, \
                    "Expected the nested connection to be the same as the outer one"

    async def test_nested_transaction_contexts(self, async_pool_and_model):
        """Test nested async transaction contexts reuse same backend."""
        pool, model = async_pool_and_model

        async with pool.transaction() as outer_tx:
            outer_backend = model.backend()
            assert outer_backend is outer_tx, \
                "Expected backend() to return the outer transaction backend"

            async with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                assert inner_backend is outer_backend, \
                    "Expected inner backend to reuse the outer transaction backend"
                assert inner_tx is outer_tx, \
                    "Expected the nested transaction to be the same as the outer one"

    async def test_connection_nested_in_transaction(self, async_pool_and_model):
        """Test async connection nested in transaction reuses transaction backend."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            tx_model_backend = model.backend()
            assert tx_model_backend is tx_backend, \
                "Expected backend() to return the transaction backend"

            async with pool.connection() as conn_backend:
                conn_model_backend = model.backend()
                assert conn_model_backend is tx_backend, \
                    "Expected connection backend to reuse the transaction backend"
                assert conn_backend is tx_backend, \
                    "Expected the nested connection to be the same as the transaction"

    async def test_transaction_nested_in_connection(self, async_pool_and_model):
        """Async transaction nested in a connection reuses the connection backend.

        Mirrors the sync test_transaction_nested_in_connection: opening a transaction
        inside an active connection context must reuse the same connection backend
        rather than acquiring a new one.
        """
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            conn_model_backend = model.backend()
            assert conn_model_backend is conn_backend, \
                "Expected backend() to return the connection backend"

            async with pool.transaction() as tx_backend:
                tx_model_backend = model.backend()
                # Transaction inside a connection reuses the same connection backend
                assert tx_model_backend is conn_backend, \
                    "Expected transaction backend to reuse the connection backend"
                assert tx_backend is conn_backend, \
                    "Expected the nested transaction to reuse the connection backend"

    async def test_deeply_nested_contexts(self, async_pool_and_model):
        """Async deeply nested contexts all resolve to the outermost backend.

        Mirrors the sync test_deeply_nested_contexts: a chain of
        connection -> connection -> transaction -> connection must keep resolving
        to the outermost backend at every level.
        """
        pool, model = async_pool_and_model

        async with pool.connection() as level1:
            assert model.backend() is level1, \
                "Expected backend() to return the level1 backend"

            async with pool.connection() as level2:
                assert model.backend() is level1, \
                    "Expected backend() to still return the outermost level1 backend"
                assert level2 is level1, "Expected level2 to reuse the level1 backend"

                async with pool.transaction() as level3:
                    assert model.backend() is level1, \
                        "Expected backend() to still return the level1 backend"
                    assert level3 is level1, "Expected level3 to reuse the level1 backend"

                    async with pool.connection() as level4:
                        assert model.backend() is level1, \
                            "Expected backend() to still return the level1 backend"
                        assert level4 is level1, "Expected level4 to reuse the level1 backend"

    async def test_sync_backend_without_context_is_none(self):
        """Test that get_current_backend() returns None without context."""
        assert get_current_backend() is None, \
            "Expected get_current_backend() to return None outside any context"

    async def test_async_backend_without_context_is_none(self):
        """Test that get_current_async_backend() returns None without context."""
        assert get_current_async_backend() is None, \
            "Expected get_current_async_backend() to return None outside any context"


