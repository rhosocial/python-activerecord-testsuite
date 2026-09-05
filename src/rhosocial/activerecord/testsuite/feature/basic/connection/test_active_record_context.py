# src/rhosocial/activerecord/testsuite/feature/basic/connection/test_active_record_context.py
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


class TestSyncActiveRecordContext:
    """Test synchronous ActiveRecord context awareness."""

    def test_backend_without_context_returns_class_backend(self, sync_pool_and_model):
        """Test that backend() returns class backend without context."""
        pool, model = sync_pool_and_model

        # Without context, should return class backend
        backend = model.backend()
        assert backend is model.__backend__, \
            "Expected backend() to return the model's class backend outside any context"

    def test_backend_in_connection_context(self, sync_pool_and_model):
        """Test that backend() returns connection backend in connection context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            model_backend = model.backend()
            assert model_backend is conn_backend, \
                "Expected backend() to return the connection backend inside a connection context"
            assert model_backend is not model.__backend__, \
                "Expected the connection backend to differ from the class backend"

            # Verify context functions
            assert get_current_backend() is conn_backend, \
                "Expected get_current_backend() to return the connection backend"
            assert get_current_connection_backend() is conn_backend, \
                "Expected get_current_connection_backend() to return the connection backend"

    def test_backend_in_transaction_context(self, sync_pool_and_model):
        """Test that backend() returns transaction backend in transaction context."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            model_backend = model.backend()
            assert model_backend is tx_backend, \
                "Expected backend() to return the transaction backend inside a transaction context"

            # Verify context functions
            assert get_current_backend() is tx_backend, \
                "Expected get_current_backend() to return the transaction backend"
            assert get_current_transaction_backend() is tx_backend, \
                "Expected get_current_transaction_backend() to return the transaction backend"

    def test_nested_connection_contexts(self, sync_pool_and_model):
        """Test nested connection contexts reuse same backend."""
        pool, model = sync_pool_and_model

        with pool.connection() as outer_conn:
            outer_backend = model.backend()
            assert outer_backend is outer_conn, \
                "Expected backend() to return the outer connection backend"

            with pool.connection() as inner_conn:
                inner_backend = model.backend()
                # Should reuse the same connection
                assert inner_backend is outer_backend, \
                    "Expected inner backend to reuse the outer connection backend"
                assert inner_conn is outer_conn, \
                    "Expected the nested connection to be the same as the outer one"

    def test_nested_transaction_contexts(self, sync_pool_and_model):
        """Test nested transaction contexts reuse same backend."""
        pool, model = sync_pool_and_model

        with pool.transaction() as outer_tx:
            outer_backend = model.backend()
            assert outer_backend is outer_tx, \
                "Expected backend() to return the outer transaction backend"

            with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                # Should reuse the same transaction
                assert inner_backend is outer_backend, \
                    "Expected inner backend to reuse the outer transaction backend"
                assert inner_tx is outer_tx, \
                    "Expected the nested transaction to be the same as the outer one"

    def test_connection_nested_in_transaction(self, sync_pool_and_model):
        """Test connection nested in transaction reuses transaction backend."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            tx_model_backend = model.backend()
            assert tx_model_backend is tx_backend, \
                "Expected backend() to return the transaction backend"

            with pool.connection() as conn_backend:
                conn_model_backend = model.backend()
                # Connection inside transaction should reuse transaction backend
                assert conn_model_backend is tx_backend, \
                    "Expected connection backend to reuse the transaction backend"
                assert conn_backend is tx_backend, \
                    "Expected the nested connection to be the same as the transaction"

    def test_transaction_nested_in_connection(self, sync_pool_and_model):
        """Transaction nested in a connection reuses the connection backend.

        Mirrors the async test_transaction_nested_in_connection: opening a transaction
        inside an active connection context must reuse the same connection backend
        rather than acquiring a new one.
        """
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            conn_model_backend = model.backend()
            assert conn_model_backend is conn_backend, \
                "Expected backend() to return the connection backend"

            with pool.transaction() as tx_backend:
                tx_model_backend = model.backend()
                # Transaction should use the same connection
                assert tx_model_backend is conn_backend, \
                    "Expected transaction backend to reuse the connection backend"
                assert tx_backend is conn_backend, \
                    "Expected the nested transaction to reuse the connection backend"

    def test_deeply_nested_contexts(self, sync_pool_and_model):
        """Deeply nested contexts all resolve to the outermost backend.

        Mirrors the async test_deeply_nested_contexts: a chain of
        connection -> connection -> transaction -> connection must keep resolving
        to the outermost backend at every level.
        """
        pool, model = sync_pool_and_model

        with pool.connection() as level1:
            assert model.backend() is level1, \
                "Expected backend() to return the level1 backend"

            with pool.connection() as level2:
                assert model.backend() is level1, \
                    "Expected backend() to still return the outermost level1 backend"
                assert level2 is level1, "Expected level2 to reuse the level1 backend"

                with pool.transaction() as level3:
                    assert model.backend() is level1, \
                        "Expected backend() to still return the level1 backend"
                    assert level3 is level1, "Expected level3 to reuse the level1 backend"

                    with pool.connection() as level4:
                        assert model.backend() is level1, \
                            "Expected backend() to still return the level1 backend"
                        assert level4 is level1, "Expected level4 to reuse the level1 backend"

    def test_sync_backend_without_context_is_none(self):
        """Test that get_current_backend() returns None without context."""
        assert get_current_backend() is None, \
            "Expected get_current_backend() to return None outside any context"

    def test_async_backend_without_context_is_none(self):
        """Test that get_current_async_backend() returns None without context."""
        assert get_current_async_backend() is None, \
            "Expected get_current_async_backend() to return None outside any context"