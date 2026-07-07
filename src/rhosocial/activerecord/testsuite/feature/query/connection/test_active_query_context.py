# src/rhosocial/activerecord/testsuite/feature/query/connection/test_active_query_context.py
"""
Test ActiveQuery context awareness with connection pool.

These tests verify that ActiveQuery correctly uses connection pool
context for backend resolution.
"""
import pytest

from rhosocial.activerecord.query import ActiveQuery, AsyncActiveQuery
class TestSyncActiveQueryContext:
    """Test synchronous ActiveQuery context awareness."""

    def test_query_from_model_backend_without_context(self, sync_pool_and_model):
        """Test ActiveQuery.backend() returns class backend without context."""
        pool, model = sync_pool_and_model

        query = model.query()
        query_backend = query.backend()
        assert query_backend is model.__backend__

    def test_query_from_model_backend_in_connection_context(self, sync_pool_and_model):
        """Test ActiveQuery.backend() returns connection backend in context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            query = model.query()
            query_backend = query.backend()
            assert query_backend is conn_backend
            assert query_backend is not model.__backend__

    def test_query_from_model_backend_in_transaction_context(self, sync_pool_and_model):
        """Test ActiveQuery.backend() returns transaction backend in context."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            query = model.query()
            query_backend = query.backend()
            assert query_backend is tx_backend

    def test_independent_query_backend_without_context(self, sync_pool_and_model):
        """Test independent ActiveQuery.backend() without context."""
        pool, model = sync_pool_and_model

        # Create query independently (not from Model.query())
        query = ActiveQuery(model)
        query_backend = query.backend()
        # Should fallback to model class backend
        assert query_backend is model.__backend__

    def test_independent_query_backend_in_connection_context(self, sync_pool_and_model):
        """Test independent ActiveQuery.backend() in connection context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            # Create query independently
            query = ActiveQuery(model)
            query_backend = query.backend()
            # Should return context backend
            assert query_backend is conn_backend

    def test_nested_connection_contexts_reuse(self, sync_pool_and_model):
        """Test nested connection contexts reuse for query."""
        pool, model = sync_pool_and_model

        with pool.connection() as outer_conn:
            outer_query = model.query()
            assert outer_query.backend() is outer_conn

            with pool.connection() as inner_conn:
                inner_query = model.query()
                assert inner_query.backend() is outer_conn
                assert inner_conn is outer_conn

    def test_nested_transaction_contexts_reuse(self, sync_pool_and_model):
        """Test nested transaction contexts reuse for query."""
        pool, model = sync_pool_and_model

        with pool.transaction() as outer_tx:
            outer_query = model.query()
            assert outer_query.backend() is outer_tx

            with pool.transaction() as inner_tx:
                inner_query = model.query()
                assert inner_query.backend() is outer_tx
                assert inner_tx is outer_tx