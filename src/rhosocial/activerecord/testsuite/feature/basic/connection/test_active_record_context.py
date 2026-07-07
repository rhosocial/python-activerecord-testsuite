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
        assert backend is model.__backend__

    def test_backend_in_connection_context(self, sync_pool_and_model):
        """Test that backend() returns connection backend in connection context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            model_backend = model.backend()
            assert model_backend is conn_backend
            assert model_backend is not model.__backend__

            # Verify context functions
            assert get_current_backend() is conn_backend
            assert get_current_connection_backend() is conn_backend

    def test_backend_in_transaction_context(self, sync_pool_and_model):
        """Test that backend() returns transaction backend in transaction context."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            model_backend = model.backend()
            assert model_backend is tx_backend

            # Verify context functions
            assert get_current_backend() is tx_backend
            assert get_current_transaction_backend() is tx_backend

    def test_nested_connection_contexts(self, sync_pool_and_model):
        """Test nested connection contexts reuse same backend."""
        pool, model = sync_pool_and_model

        with pool.connection() as outer_conn:
            outer_backend = model.backend()
            assert outer_backend is outer_conn

            with pool.connection() as inner_conn:
                inner_backend = model.backend()
                # Should reuse the same connection
                assert inner_backend is outer_backend
                assert inner_conn is outer_conn

    def test_nested_transaction_contexts(self, sync_pool_and_model):
        """Test nested transaction contexts reuse same backend."""
        pool, model = sync_pool_and_model

        with pool.transaction() as outer_tx:
            outer_backend = model.backend()
            assert outer_backend is outer_tx

            with pool.transaction() as inner_tx:
                inner_backend = model.backend()
                # Should reuse the same transaction
                assert inner_backend is outer_backend
                assert inner_tx is outer_tx

    def test_connection_nested_in_transaction(self, sync_pool_and_model):
        """Test connection nested in transaction reuses transaction backend."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            tx_model_backend = model.backend()
            assert tx_model_backend is tx_backend

            with pool.connection() as conn_backend:
                conn_model_backend = model.backend()
                # Connection inside transaction should reuse transaction backend
                assert conn_model_backend is tx_backend
                assert conn_backend is tx_backend

    def test_transaction_nested_in_connection(self, sync_pool_and_model):
        """Test transaction nested in connection."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            conn_model_backend = model.backend()
            assert conn_model_backend is conn_backend

            with pool.transaction() as tx_backend:
                tx_model_backend = model.backend()
                # Transaction should use the same connection
                assert tx_model_backend is conn_backend
                assert tx_backend is conn_backend

    def test_deeply_nested_contexts(self, sync_pool_and_model):
        """Test deeply nested contexts."""
        pool, model = sync_pool_and_model

        with pool.connection() as level1:
            assert model.backend() is level1

            with pool.connection() as level2:
                assert model.backend() is level1
                assert level2 is level1

                with pool.transaction() as level3:
                    assert model.backend() is level1
                    assert level3 is level1

                    with pool.connection() as level4:
                        assert model.backend() is level1
                        assert level4 is level1