# src/rhosocial/activerecord/testsuite/feature/query/connection/test_cte_query_context.py
"""
Test CTEQuery context awareness with connection pool.

These tests verify that CTEQuery correctly uses connection pool
context for backend resolution.
"""
import pytest

from rhosocial.activerecord.backend.dialect.protocols import CTESupport
from rhosocial.activerecord.query import CTEQuery, AsyncCTEQuery
from rhosocial.activerecord.testsuite.utils import requires_protocol
class TestSyncCTEQueryContext:
    """Test synchronous CTEQuery context awareness."""

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_cte_query_backend_without_context(self, sync_pool_and_model):
        """Test CTEQuery.backend() returns constructor backend without context."""
        pool, model = sync_pool_and_model

        original_backend = model.__backend__
        cte = CTEQuery(original_backend)
        cte_backend = cte.backend()
        assert cte_backend is original_backend, "Expected backend to be the constructor backend"

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_cte_query_backend_in_connection_context(self, sync_pool_and_model):
        """Test CTEQuery.backend() returns connection backend in context."""
        pool, model = sync_pool_and_model

        original_backend = model.__backend__

        with pool.connection() as conn_backend:
            cte = CTEQuery(original_backend)
            cte_backend = cte.backend()
            assert cte_backend is conn_backend, "Expected backend to be the connection backend"
            assert cte_backend is not original_backend, "Expected backend to differ from original"

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_cte_query_backend_in_transaction_context(self, sync_pool_and_model):
        """Test CTEQuery.backend() returns transaction backend in context."""
        pool, model = sync_pool_and_model

        original_backend = model.__backend__

        with pool.transaction() as tx_backend:
            cte = CTEQuery(original_backend)
            cte_backend = cte.backend()
            assert cte_backend is tx_backend, "Expected backend to be the transaction backend"
            assert cte_backend is not original_backend, "Expected backend to differ from original"

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_nested_connection_contexts_reuse(self, sync_pool_and_model):
        """Test nested connection contexts reuse for CTE query."""
        pool, model = sync_pool_and_model

        original_backend = model.__backend__

        with pool.connection() as outer_conn:
            outer_cte = CTEQuery(original_backend)
            assert outer_cte.backend() is outer_conn, "Expected outer CTE to use outer conn"

            with pool.connection() as inner_conn:
                inner_cte = CTEQuery(original_backend)
                assert inner_cte.backend() is outer_conn, "Expected inner CTE to reuse outer"
                assert inner_conn is outer_conn, "Expected inner conn to be the same as outer"

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_nested_transaction_contexts_reuse(self, sync_pool_and_model):
        """Test nested transaction contexts reuse for CTE query."""
        pool, model = sync_pool_and_model

        original_backend = model.__backend__

        with pool.transaction() as outer_tx:
            outer_cte = CTEQuery(original_backend)
            assert outer_cte.backend() is outer_tx, "Expected outer CTE to use outer tx"

            with pool.transaction() as inner_tx:
                inner_cte = CTEQuery(original_backend)
                assert inner_cte.backend() is outer_tx, "Expected inner CTE to reuse outer"
                assert inner_tx is outer_tx, "Expected inner tx to be the same as outer"

    @requires_protocol(CTESupport, "supports_basic_cte")
    def test_cte_query_from_model_in_context(self, sync_pool_and_model):
        """Test CTEQuery created from model query in context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            query = model.query()
            # The query's backend should be the context backend
            assert query.backend() is conn_backend, "Expected query backend to be the context backend"