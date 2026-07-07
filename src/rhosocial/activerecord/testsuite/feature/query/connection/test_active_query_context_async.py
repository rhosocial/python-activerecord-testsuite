# src/rhosocial/activerecord/testsuite/feature/query/connection/test_active_query_context.py
"""
Test ActiveQuery context awareness with connection pool.

These tests verify that ActiveQuery correctly uses connection pool
context for backend resolution.
"""
import pytest

from rhosocial.activerecord.query import ActiveQuery, AsyncActiveQuery
class TestAsyncActiveQueryContext:
    """Test asynchronous ActiveQuery context awareness."""

    @pytest.mark.asyncio
    async def test_query_from_model_backend_without_context(self, async_pool_and_model):
        """Test AsyncActiveQuery.backend() returns class backend without context."""
        pool, model = async_pool_and_model

        query = model.query()
        query_backend = query.backend()
        assert query_backend is model.__backend__

    @pytest.mark.asyncio
    async def test_query_from_model_backend_in_connection_context(self, async_pool_and_model):
        """Test AsyncActiveQuery.backend() returns connection backend in context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            query = model.query()
            query_backend = query.backend()
            assert query_backend is conn_backend

    @pytest.mark.asyncio
    async def test_query_from_model_backend_in_transaction_context(self, async_pool_and_model):
        """Test AsyncActiveQuery.backend() returns transaction backend in context."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            query = model.query()
            query_backend = query.backend()
            assert query_backend is tx_backend

    @pytest.mark.asyncio
    async def test_independent_query_backend_without_context(self, async_pool_and_model):
        """Test independent AsyncActiveQuery.backend() without context."""
        pool, model = async_pool_and_model

        query = AsyncActiveQuery(model)
        query_backend = query.backend()
        assert query_backend is model.__backend__

    @pytest.mark.asyncio
    async def test_independent_query_backend_in_connection_context(self, async_pool_and_model):
        """Test independent AsyncActiveQuery.backend() in connection context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            # Create query independently
            query = AsyncActiveQuery(model)
            query_backend = query.backend()
            assert query_backend is conn_backend

    @pytest.mark.asyncio
    async def test_nested_connection_contexts_reuse(self, async_pool_and_model):
        """Test nested async connection contexts reuse for query."""
        pool, model = async_pool_and_model

        async with pool.connection() as outer_conn:
            outer_query = model.query()
            assert outer_query.backend() is outer_conn

            async with pool.connection() as inner_conn:
                inner_query = model.query()
                assert inner_query.backend() is outer_conn
                assert inner_conn is outer_conn

    @pytest.mark.asyncio
    async def test_nested_transaction_contexts_reuse(self, async_pool_and_model):
        """Test nested async transaction contexts reuse for query."""
        pool, model = async_pool_and_model

        async with pool.transaction() as outer_tx:
            outer_query = model.query()
            assert outer_query.backend() is outer_tx

            async with pool.transaction() as inner_tx:
                inner_query = model.query()
                assert inner_query.backend() is outer_tx
                assert inner_tx is outer_tx