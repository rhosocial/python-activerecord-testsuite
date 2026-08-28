# src/rhosocial/activerecord/testsuite/feature/query/connection/test_cte_query_context_async.py
"""
Test CTEQuery context awareness with connection pool.

These tests verify that CTEQuery correctly uses connection pool
context for backend resolution.
"""

from rhosocial.activerecord.backend.dialect.protocols import CTESupport
from rhosocial.activerecord.query import CTEQuery, AsyncCTEQuery
from rhosocial.activerecord.testsuite.utils import requires_protocol
class TestAsyncCTEQueryContext:
    """Test asynchronous CTEQuery context awareness."""

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_cte_query_backend_without_context(self, async_pool_and_model):
        """Test AsyncCTEQuery.backend() returns constructor backend without context."""
        pool, model = async_pool_and_model

        original_backend = model.__backend__
        cte = AsyncCTEQuery(original_backend)
        cte_backend = cte.backend()
        assert cte_backend is original_backend

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_cte_query_backend_in_connection_context(self, async_pool_and_model):
        """Test AsyncCTEQuery.backend() returns connection backend in context."""
        pool, model = async_pool_and_model

        original_backend = model.__backend__

        async with pool.connection() as conn_backend:
            cte = AsyncCTEQuery(original_backend)
            cte_backend = cte.backend()
            assert cte_backend is conn_backend
            assert cte_backend is not original_backend

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_cte_query_backend_in_transaction_context(self, async_pool_and_model):
        """Test AsyncCTEQuery.backend() returns transaction backend in context."""
        pool, model = async_pool_and_model

        original_backend = model.__backend__

        async with pool.transaction() as tx_backend:
            cte = AsyncCTEQuery(original_backend)
            cte_backend = cte.backend()
            assert cte_backend is tx_backend
            assert cte_backend is not original_backend

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_nested_connection_contexts_reuse(self, async_pool_and_model):
        """Test nested async connection contexts reuse for CTE query."""
        pool, model = async_pool_and_model

        original_backend = model.__backend__

        async with pool.connection() as outer_conn:
            outer_cte = AsyncCTEQuery(original_backend)
            assert outer_cte.backend() is outer_conn

            async with pool.connection() as inner_conn:
                inner_cte = AsyncCTEQuery(original_backend)
                assert inner_cte.backend() is outer_conn
                assert inner_conn is outer_conn

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_nested_transaction_contexts_reuse(self, async_pool_and_model):
        """Test nested async transaction contexts reuse for CTE query."""
        pool, model = async_pool_and_model

        original_backend = model.__backend__

        async with pool.transaction() as outer_tx:
            outer_cte = AsyncCTEQuery(original_backend)
            assert outer_cte.backend() is outer_tx

            async with pool.transaction() as inner_tx:
                inner_cte = AsyncCTEQuery(original_backend)
                assert inner_cte.backend() is outer_tx
                assert inner_tx is outer_tx

    @requires_protocol(CTESupport, "supports_basic_cte")
    async def test_cte_query_from_model_in_context(self, async_pool_and_model):
        """Test AsyncCTEQuery created from model query in context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            query = model.query()
            assert query.backend() is conn_backend

