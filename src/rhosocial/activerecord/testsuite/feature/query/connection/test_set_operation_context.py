# src/rhosocial/activerecord/testsuite/feature/query/connection/test_set_operation_context.py
"""
Test SetOperationQuery context awareness with connection pool.

These tests verify that SetOperationQuery (UNION, INTERSECT, EXCEPT)
correctly uses connection pool context for backend resolution.
"""
import pytest


class TestSyncSetOperationQueryContext:
    """Test synchronous SetOperationQuery context awareness."""

    def test_union_backend_without_context(self, sync_pool_and_model):
        """Test SetOperationQuery.backend() returns left backend without context."""
        pool, model = sync_pool_and_model

        q1 = model.query()
        q2 = model.query()
        union_query = q1.union(q2)
        union_backend = union_query.backend()
        # Should return left query's backend (class backend)
        assert union_backend is model.__backend__

    def test_union_backend_in_connection_context(self, sync_pool_and_model):
        """Test SetOperationQuery.backend() returns connection backend in context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            union_query = q1.union(q2)
            union_backend = union_query.backend()
            assert union_backend is conn_backend

    def test_union_backend_in_transaction_context(self, sync_pool_and_model):
        """Test SetOperationQuery.backend() returns transaction backend in context."""
        pool, model = sync_pool_and_model

        with pool.transaction() as tx_backend:
            q1 = model.query()
            q2 = model.query()
            union_query = q1.union(q2)
            union_backend = union_query.backend()
            assert union_backend is tx_backend

    def test_intersect_backend_in_connection_context(self, sync_pool_and_model):
        """Test INTERSECT backend in connection context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            intersect_query = q1.intersect(q2)
            intersect_backend = intersect_query.backend()
            assert intersect_backend is conn_backend

    def test_except_backend_in_connection_context(self, sync_pool_and_model):
        """Test EXCEPT backend in connection context."""
        pool, model = sync_pool_and_model

        with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            except_query = q1.except_(q2)
            except_backend = except_query.backend()
            assert except_backend is conn_backend

    def test_nested_connection_contexts_reuse(self, sync_pool_and_model):
        """Test nested connection contexts reuse for set operation."""
        pool, model = sync_pool_and_model

        with pool.connection() as outer_conn:
            q1 = model.query()
            q2 = model.query()
            outer_union = q1.union(q2)
            assert outer_union.backend() is outer_conn

            with pool.connection() as inner_conn:
                q3 = model.query()
                q4 = model.query()
                inner_union = q3.union(q4)
                assert inner_union.backend() is outer_conn
                assert inner_conn is outer_conn

    def test_nested_transaction_contexts_reuse(self, sync_pool_and_model):
        """Test nested transaction contexts reuse for set operation."""
        pool, model = sync_pool_and_model

        with pool.transaction() as outer_tx:
            q1 = model.query()
            q2 = model.query()
            outer_union = q1.union(q2)
            assert outer_union.backend() is outer_tx

            with pool.transaction() as inner_tx:
                q3 = model.query()
                q4 = model.query()
                inner_union = q3.union(q4)
                assert inner_union.backend() is outer_tx
                assert inner_tx is outer_tx


class TestAsyncSetOperationQueryContext:
    """Test asynchronous SetOperationQuery context awareness."""

    @pytest.mark.asyncio
    async def test_union_backend_without_context(self, async_pool_and_model):
        """Test AsyncSetOperationQuery.backend() returns left backend without context."""
        pool, model = async_pool_and_model

        q1 = model.query()
        q2 = model.query()
        union_query = q1.union(q2)
        union_backend = union_query.backend()
        assert union_backend is model.__backend__

    @pytest.mark.asyncio
    async def test_union_backend_in_connection_context(self, async_pool_and_model):
        """Test AsyncSetOperationQuery.backend() returns connection backend in context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            union_query = q1.union(q2)
            union_backend = union_query.backend()
            assert union_backend is conn_backend

    @pytest.mark.asyncio
    async def test_union_backend_in_transaction_context(self, async_pool_and_model):
        """Test AsyncSetOperationQuery.backend() returns transaction backend in context."""
        pool, model = async_pool_and_model

        async with pool.transaction() as tx_backend:
            q1 = model.query()
            q2 = model.query()
            union_query = q1.union(q2)
            union_backend = union_query.backend()
            assert union_backend is tx_backend

    @pytest.mark.asyncio
    async def test_intersect_backend_in_connection_context(self, async_pool_and_model):
        """Test async INTERSECT backend in connection context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            intersect_query = q1.intersect(q2)
            intersect_backend = intersect_query.backend()
            assert intersect_backend is conn_backend

    @pytest.mark.asyncio
    async def test_except_backend_in_connection_context(self, async_pool_and_model):
        """Test async EXCEPT backend in connection context."""
        pool, model = async_pool_and_model

        async with pool.connection() as conn_backend:
            q1 = model.query()
            q2 = model.query()
            except_query = q1.except_(q2)
            except_backend = except_query.backend()
            assert except_backend is conn_backend

    @pytest.mark.asyncio
    async def test_nested_connection_contexts_reuse(self, async_pool_and_model):
        """Test nested async connection contexts reuse for set operation."""
        pool, model = async_pool_and_model

        async with pool.connection() as outer_conn:
            q1 = model.query()
            q2 = model.query()
            outer_union = q1.union(q2)
            assert outer_union.backend() is outer_conn

            async with pool.connection() as inner_conn:
                q3 = model.query()
                q4 = model.query()
                inner_union = q3.union(q4)
                assert inner_union.backend() is outer_conn
                assert inner_conn is outer_conn

    @pytest.mark.asyncio
    async def test_nested_transaction_contexts_reuse(self, async_pool_and_model):
        """Test nested async transaction contexts reuse for set operation."""
        pool, model = async_pool_and_model

        async with pool.transaction() as outer_tx:
            q1 = model.query()
            q2 = model.query()
            outer_union = q1.union(q2)
            assert outer_union.backend() is outer_tx

            async with pool.transaction() as inner_tx:
                q3 = model.query()
                q4 = model.query()
                inner_union = q3.union(q4)
                assert inner_union.backend() is outer_tx
                assert inner_tx is outer_tx
