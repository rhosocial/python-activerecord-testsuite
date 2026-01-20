"""
Set operation query tests for testing UNION, INTERSECT, and EXCEPT operations.

This module tests the SetOperationQuery and AsyncSetOperationQuery classes
to ensure they properly handle set operations between queries and validate
backend compatibility.
"""

import pytest
from unittest.mock import Mock
from rhosocial.activerecord.query.set_operation import SetOperationQuery, AsyncSetOperationQuery
from rhosocial.activerecord.backend.impl.dummy.backend import DummyBackend, AsyncDummyBackend
from rhosocial.activerecord.interface import IQuery, IAsyncQuery


class MockSyncQuery(IQuery):
    """Mock synchronous query for testing SetOperationQuery."""

    def __init__(self, backend):
        self._backend = backend

    def backend(self):
        return self._backend

    def to_sql(self):
        return ("SELECT * FROM mock", ())

    def where(self, condition):
        return self

    def all(self):
        return []


class MockAsyncQuery(IAsyncQuery):
    """Mock asynchronous query for testing AsyncSetOperationQuery."""

    def __init__(self, backend):
        self._backend = backend

    def backend(self):
        return self._backend

    def to_sql(self):
        return ("SELECT * FROM mock_async", ())

    async def where(self, condition):
        return self

    async def all(self):
        return []


class TestSyncSetOperationQuery:
    """Test class for synchronous SetOperationQuery functionality."""

    def test_sync_set_operation_query_with_sync_backends(self):
        """Test SetOperationQuery with synchronous backends."""
        # Create dummy backends for testing
        backend1 = DummyBackend()
        backend2 = DummyBackend()

        # Create mock queries with sync backends
        query1 = MockSyncQuery(backend1)
        query2 = MockSyncQuery(backend2)

        # Create SetOperationQuery - should work with sync backends
        set_op_query = SetOperationQuery(query1, query2, "UNION")

        # Verify the query was created successfully
        assert set_op_query is not None
        assert set_op_query.left == query1
        assert set_op_query.right == query2
        assert set_op_query.operation == "UNION"

    def test_sync_set_operation_query_with_async_backend_left_raises_error(self):
        """Test SetOperationQuery rejects async backend on left operand."""
        # Create sync and async backends
        sync_backend = DummyBackend()
        async_backend = AsyncDummyBackend()

        # Create mock queries
        sync_query = MockSyncQuery(sync_backend)
        async_query = MockAsyncQuery(async_backend)

        # Creating SetOperationQuery with async and sync backends should raise TypeError
        with pytest.raises(TypeError, match="does not support async backends"):
            SetOperationQuery(async_query, sync_query, "UNION")

    def test_sync_set_operation_query_with_async_backend_right_raises_error(self):
        """Test SetOperationQuery rejects async backend on right operand."""
        # Create sync and async backends
        sync_backend = DummyBackend()
        async_backend = AsyncDummyBackend()

        # Create mock queries
        sync_query = MockSyncQuery(sync_backend)
        async_query = MockAsyncQuery(async_backend)

        # Creating SetOperationQuery with sync and async backends should raise TypeError
        with pytest.raises(TypeError, match="does not support async backends"):
            SetOperationQuery(sync_query, async_query, "UNION")

    def test_sync_set_operation_query_with_different_backends_raises_error(self):
        """Test SetOperationQuery rejects different backend types."""
        # Create different types of backends to test the validation
        from rhosocial.activerecord.backend.impl.dummy.backend import DummyBackend
        from rhosocial.activerecord.backend.impl.sqlite.backend import SQLiteBackend

        # Create a mock SQLiteBackend since we can't easily instantiate a real one without DB connection
        sqlite_backend = Mock(spec=SQLiteBackend)
        sqlite_backend.dialect = Mock(__class__=type('MockSQLiteDialect', (), {})())

        dummy_backend = DummyBackend()

        # Create mock queries with different backend types
        query1 = MockSyncQuery(dummy_backend)
        query2 = MockSyncQuery(sqlite_backend)

        # Creating SetOperationQuery with different backend types should raise ValueError
        with pytest.raises(ValueError, match="Different dialect types for left"):
            SetOperationQuery(query1, query2, "UNION")

    def test_sync_set_operation_query_union_method(self):
        """Test SetOperationQuery union method."""
        backend = DummyBackend()
        query1 = MockSyncQuery(backend)
        query2 = MockSyncQuery(backend)

        # Create initial set operation
        initial_set_op = SetOperationQuery(query1, query2, "INTERSECT")

        # Create another query for union
        query3 = MockSyncQuery(backend)

        # Test union method
        union_result = initial_set_op.union(query3)
        assert isinstance(union_result, SetOperationQuery)
        assert union_result.operation == "UNION"

    def test_sync_set_operation_query_intersect_method(self):
        """Test SetOperationQuery intersect method."""
        backend = DummyBackend()
        query1 = MockSyncQuery(backend)
        query2 = MockSyncQuery(backend)

        # Create initial set operation
        initial_set_op = SetOperationQuery(query1, query2, "UNION")

        # Create another query for intersect
        query3 = MockSyncQuery(backend)

        # Test intersect method
        intersect_result = initial_set_op.intersect(query3)
        assert isinstance(intersect_result, SetOperationQuery)
        assert intersect_result.operation == "INTERSECT"

    def test_sync_set_operation_query_except_method(self):
        """Test SetOperationQuery except_ method."""
        backend = DummyBackend()
        query1 = MockSyncQuery(backend)
        query2 = MockSyncQuery(backend)

        # Create initial set operation
        initial_set_op = SetOperationQuery(query1, query2, "UNION")

        # Create another query for except
        query3 = MockSyncQuery(backend)

        # Test except_ method
        except_result = initial_set_op.except_(query3)
        assert isinstance(except_result, SetOperationQuery)
        assert except_result.operation == "EXCEPT"

    def test_sync_set_operation_query_operator_overloading(self):
        """Test SetOperationQuery operator overloading."""
        backend = DummyBackend()
        query1 = MockSyncQuery(backend)
        query2 = MockSyncQuery(backend)

        # Create initial set operation
        initial_set_op = SetOperationQuery(query1, query2, "INTERSECT")

        # Create another query for operators
        query3 = MockSyncQuery(backend)

        # Test union operator (__or__)
        union_result = initial_set_op | query3
        assert isinstance(union_result, SetOperationQuery)
        assert union_result.operation == "UNION"

        # Test intersect operator (__and__)
        intersect_result = initial_set_op & query3
        assert isinstance(intersect_result, SetOperationQuery)
        assert intersect_result.operation == "INTERSECT"

        # Test except operator (__sub__)
        except_result = initial_set_op - query3
        assert isinstance(except_result, SetOperationQuery)
        assert except_result.operation == "EXCEPT"


class TestAsyncSetOperationQuery:
    """Test class for asynchronous AsyncSetOperationQuery functionality."""

    def test_async_set_operation_query_with_async_backends(self):
        """Test AsyncSetOperationQuery with async backends."""
        # Create async backends for testing
        async_backend1 = AsyncDummyBackend()
        async_backend2 = AsyncDummyBackend()

        # Create mock async queries
        async_query1 = MockAsyncQuery(async_backend1)
        async_query2 = MockAsyncQuery(async_backend2)

        # Create AsyncSetOperationQuery - should work with async backends
        async_set_op_query = AsyncSetOperationQuery(async_query1, async_query2, "UNION")

        # Verify the query was created successfully
        assert async_set_op_query is not None
        assert async_set_op_query.left == async_query1
        assert async_set_op_query.right == async_query2
        assert async_set_op_query.operation == "UNION"

    def test_async_set_operation_query_with_sync_backend_left_raises_error(self):
        """Test AsyncSetOperationQuery rejects sync backend on left operand."""
        # Create sync and async backends
        sync_backend = DummyBackend()
        async_backend = AsyncDummyBackend()

        # Create mock queries
        sync_query = MockSyncQuery(sync_backend)
        async_query = MockAsyncQuery(async_backend)

        # Creating AsyncSetOperationQuery with sync and async backends should raise TypeError
        with pytest.raises(TypeError, match="requires async backends"):
            AsyncSetOperationQuery(sync_query, async_query, "UNION")

    def test_async_set_operation_query_with_sync_backend_right_raises_error(self):
        """Test AsyncSetOperationQuery rejects sync backend on right operand."""
        # Create sync and async backends
        sync_backend = DummyBackend()
        async_backend = AsyncDummyBackend()

        # Create mock queries
        sync_query = MockSyncQuery(sync_backend)
        async_query = MockAsyncQuery(async_backend)

        # Creating AsyncSetOperationQuery with async and sync backends should raise TypeError
        with pytest.raises(TypeError, match="requires async backends"):
            AsyncSetOperationQuery(async_query, sync_query, "UNION")

    def test_async_set_operation_query_with_different_backends_raises_error(self):
        """Test AsyncSetOperationQuery rejects different backend types."""
        # Create different types of async backends to test the validation
        from rhosocial.activerecord.backend.impl.dummy.backend import AsyncDummyBackend
        from rhosocial.activerecord.backend.base import AsyncStorageBackend

        # Create a mock backend with a different dialect type to test validation
        # We'll create a mock backend with a custom dialect class
        class MockCustomDialect:
            pass

        async_backend1 = AsyncDummyBackend()
        # Create a mock backend with different dialect type
        async_backend2 = Mock(spec=AsyncStorageBackend)
        async_backend2.dialect = MockCustomDialect()

        # Create mock queries with different backend types
        async_query1 = MockAsyncQuery(async_backend1)
        async_query2 = MockAsyncQuery(async_backend2)

        # Creating AsyncSetOperationQuery with different backend types should raise ValueError
        with pytest.raises(ValueError, match="Different dialect types for left"):
            AsyncSetOperationQuery(async_query1, async_query2, "UNION")

    def test_async_set_operation_query_union_method(self):
        """Test AsyncSetOperationQuery union method."""
        # Create async backends
        async_backend = AsyncDummyBackend()

        # Create mock async queries
        async_query1 = MockAsyncQuery(async_backend)
        async_query2 = MockAsyncQuery(async_backend)

        # Create initial async set operation
        initial_async_set_op = AsyncSetOperationQuery(async_query1, async_query2, "INTERSECT")

        # Create another mock query for union
        async_query3 = MockAsyncQuery(async_backend)

        # Test union method
        union_result = initial_async_set_op.union(async_query3)
        assert isinstance(union_result, AsyncSetOperationQuery)
        assert union_result.operation == "UNION"

    def test_async_set_operation_query_intersect_method(self):
        """Test AsyncSetOperationQuery intersect method."""
        # Create async backends
        async_backend = AsyncDummyBackend()

        # Create mock async queries
        async_query1 = MockAsyncQuery(async_backend)
        async_query2 = MockAsyncQuery(async_backend)

        # Create initial async set operation
        initial_async_set_op = AsyncSetOperationQuery(async_query1, async_query2, "UNION")

        # Create another mock query for intersect
        async_query3 = MockAsyncQuery(async_backend)

        # Test intersect method
        intersect_result = initial_async_set_op.intersect(async_query3)
        assert isinstance(intersect_result, AsyncSetOperationQuery)
        assert intersect_result.operation == "INTERSECT"

    def test_async_set_operation_query_except_method(self):
        """Test AsyncSetOperationQuery except_ method."""
        # Create async backends
        async_backend = AsyncDummyBackend()

        # Create mock async queries
        async_query1 = MockAsyncQuery(async_backend)
        async_query2 = MockAsyncQuery(async_backend)

        # Create initial async set operation
        initial_async_set_op = AsyncSetOperationQuery(async_query1, async_query2, "UNION")

        # Create another mock query for except
        async_query3 = MockAsyncQuery(async_backend)

        # Test except_ method
        except_result = initial_async_set_op.except_(async_query3)
        assert isinstance(except_result, AsyncSetOperationQuery)
        assert except_result.operation == "EXCEPT"

    def test_async_set_operation_query_operator_overloading(self):
        """Test AsyncSetOperationQuery operator overloading."""
        # Create async backends
        async_backend = AsyncDummyBackend()

        # Create mock async queries
        async_query1 = MockAsyncQuery(async_backend)
        async_query2 = MockAsyncQuery(async_backend)

        # Create initial async set operation
        initial_async_set_op = AsyncSetOperationQuery(async_query1, async_query2, "INTERSECT")

        # Create another mock query for operators
        async_query3 = MockAsyncQuery(async_backend)

        # Test union operator (__or__)
        union_result = initial_async_set_op | async_query3
        assert isinstance(union_result, AsyncSetOperationQuery)
        assert union_result.operation == "UNION"

        # Test intersect operator (__and__)
        intersect_result = initial_async_set_op & async_query3
        assert isinstance(intersect_result, AsyncSetOperationQuery)
        assert intersect_result.operation == "INTERSECT"

        # Test except operator (__sub__)
        except_result = initial_async_set_op - async_query3
        assert isinstance(except_result, AsyncSetOperationQuery)
        assert except_result.operation == "EXCEPT"


def test_convert_to_base_expression_with_invalid_type():
    """Test _convert_to_base_expression with invalid query type."""
    from rhosocial.activerecord.backend.impl.dummy.backend import DummyBackend

    backend = DummyBackend()
    query1 = MockSyncQuery(backend)
    query2 = MockSyncQuery(backend)

    # Create SetOperationQuery
    set_op_query = SetOperationQuery(query1, query2, "UNION")

    # Create a mock query that is neither SetOperationQuery nor IQuery
    invalid_query = Mock()  # This is not an IQuery or SetOperationQuery

    with pytest.raises(TypeError, match="is not supported in set operations"):
        set_op_query._convert_to_base_expression(invalid_query)


def test_async_convert_to_base_expression_with_invalid_type():
    """Test async _convert_to_base_expression with invalid query type."""
    from rhosocial.activerecord.backend.impl.dummy.backend import AsyncDummyBackend

    async_backend = AsyncDummyBackend()
    async_query1 = MockAsyncQuery(async_backend)
    async_query2 = MockAsyncQuery(async_backend)

    # Create AsyncSetOperationQuery
    async_set_op_query = AsyncSetOperationQuery(async_query1, async_query2, "UNION")

    # Create a mock query that is neither AsyncSetOperationQuery nor IAsyncQuery
    invalid_query = Mock()  # This is not an IAsyncQuery or AsyncSetOperationQuery

    with pytest.raises(TypeError, match="is not supported in async set operations"):
        async_set_op_query._convert_to_base_expression(invalid_query)


def test_to_sql_keyword_check():
    """Test to_sql method returns SQL with expected keywords."""
    from rhosocial.activerecord.backend.impl.dummy.backend import DummyBackend

    backend = DummyBackend()

    # Create mock queries
    query1 = MockSyncQuery(backend)
    query2 = MockSyncQuery(backend)

    # Create SetOperationQuery
    set_op_query = SetOperationQuery(query1, query2, "UNION")

    # Get SQL and check for keywords
    sql, params = set_op_query.to_sql()

    # Just check for presence of expected keywords in the SQL
    sql_upper = sql.upper()
    assert "WITH" in sql_upper or "UNION" in sql_upper


def test_async_to_sql_keyword_check():
    """Test async to_sql method returns SQL with expected keywords."""
    from rhosocial.activerecord.backend.impl.dummy.backend import AsyncDummyBackend

    async_backend = AsyncDummyBackend()

    # Create mock async queries
    async_query1 = MockAsyncQuery(async_backend)
    async_query2 = MockAsyncQuery(async_backend)

    # Create AsyncSetOperationQuery
    async_set_op_query = AsyncSetOperationQuery(async_query1, async_query2, "UNION")

    # Get SQL and check for keywords
    sql, params = async_set_op_query.to_sql()

    # Just check for presence of expected keywords in the SQL
    sql_upper = sql.upper()
    assert "WITH" in sql_upper or "UNION" in sql_upper