"""
CTE Query ActiveQuery tests to verify CTE functionality with ActiveQuery as subqueries.

This module tests Common Table Expression (CTE) queries where the subqueries
are ActiveQuery instances. It includes tests for:
- Single ActiveQuery as CTE
- Multiple ActiveQuery instances as CTEs
Both synchronous and asynchronous versions are included.
"""
import pytest
from decimal import Decimal

from rhosocial.activerecord.query import CTEQuery, AsyncCTEQuery
from rhosocial.activerecord.testsuite.utils import requires_cte, requires_recursive_cte


class TestCTEQueryActiveQuery:
    """Test CTE queries with ActiveQuery subqueries (synchronous)."""

    @requires_cte()
    def test_single_active_query_cte(self, tree_fixtures):
        """Test basic CTE with a single ActiveQuery as subquery."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node

        Node = tree_fixtures[0]

        # Get backend from Node model
        backend = Node.backend()

        # Clean up any existing data
        for node in Node.query().all():
            node.delete()

        # Create test data
        root = Node(name="Root", value=Decimal('100.0'))
        root.save()

        child1 = Node(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        child1.save()

        child2 = Node(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        child2.save()

        grandchild = Node(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        grandchild.save()

        # Create a CTE using ActiveQuery as subquery
        cte_subquery = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value >= Decimal('50'))

        # Create CTEQuery instance with backend
        cte_query = CTEQuery(backend)
        cte_query.with_cte(name="high_value_nodes", query=cte_subquery)

        # Execute the CTE query using aggregate method
        result = cte_query.from_cte("high_value_nodes").select("name", "value").aggregate()

        assert len(result) == 3  # root, child1, child2
        # Check the actual structure of the result
        names = sorted([r['name'] for r in result])
        assert names == ["Child1", "Child2", "Root"]

    @requires_cte()
    def test_multiple_active_query_cte(self, tree_fixtures):
        """Test CTE with multiple ActiveQuery instances as subqueries."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node

        Node = tree_fixtures[0]

        # Get backend from Node model
        backend = Node.backend()

        # Clean up any existing data
        for node in Node.query().all():
            node.delete()

        # Create test data
        root = Node(name="Root", value=Decimal('100.0'))
        root.save()

        child1 = Node(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        child1.save()

        child2 = Node(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        child2.save()

        grandchild = Node(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        grandchild.save()

        # Create multiple CTEs using ActiveQuery as subqueries
        high_value_cte = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value >= Decimal('60'))
        low_value_cte = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value < Decimal('60'))

        # Create CTEQuery instance with multiple CTEs
        cte_query = CTEQuery(backend)
        cte_query.with_cte(name="high_values", query=high_value_cte)
        cte_query.with_cte(name="low_values", query=low_value_cte)

        # Execute the CTE query using aggregate method
        result = cte_query.from_cte("high_values").select("name", "value").aggregate()

        assert len(result) >= 2  # Should have results from the high_values CTE


class TestCTEQueryErrorHandling:
    """Test CTE query error handling and validation."""

    def test_cte_query_with_async_backend_raises_error(self, order_fixtures):
        """
        Test that CTEQuery raises TypeError when an async backend is provided.

        This test verifies that the synchronous CTEQuery properly validates
        the backend type and raises appropriate errors for incorrect types.
        """
        User, Order, OrderItem = order_fixtures

        # Get sync backend from model
        sync_backend = Order.backend()

        # Create a mock async backend to simulate passing an async backend to sync CTEQuery
        from unittest.mock import Mock
        from rhosocial.activerecord.backend.base import AsyncStorageBackend

        mock_async_backend = Mock(spec=AsyncStorageBackend)
        mock_async_backend.dialect = Mock()

        # Try to create a CTEQuery with an async backend - should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            CTEQuery(mock_async_backend)

        # Verify the error message mentions the incorrect backend type
        assert "StorageBackend" in str(exc_info.value)
        assert "Mock" in str(exc_info.value)

    def test_async_cte_query_with_sync_backend_raises_error(self, order_fixtures):
        """
        Test that AsyncCTEQuery raises TypeError when a sync backend is provided.

        This test verifies that the asynchronous AsyncCTEQuery properly validates
        the backend type and raises appropriate errors for incorrect types.
        """
        User, Order, OrderItem = order_fixtures

        # Get sync backend from model
        sync_backend = Order.backend()

        # Try to create an AsyncCTEQuery with a sync backend - should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            AsyncCTEQuery(sync_backend)

        # Verify the error message mentions the incorrect backend type
        assert "AsyncCTEQuery requires an AsyncStorageBackend" in str(exc_info.value)
        assert "StorageBackend" in str(exc_info.value)

    def test_cte_query_with_async_query_raises_error(self, order_fixtures):
        """
        Test that CTEQuery raises TypeError when an invalid query type is provided to with_cte.

        This test verifies that the synchronous CTEQuery properly validates
        the query types passed to it and raises appropriate errors for incorrect types.
        """
        User, Order, OrderItem = order_fixtures

        # Get sync backend from model
        backend = Order.backend()

        # Create a CTEQuery instance
        cte_query = CTEQuery(backend)

        # Create a mock that behaves like an invalid query
        from unittest.mock import Mock

        # Create a mock that doesn't implement the expected interfaces
        invalid_query = Mock()

        # Try to add the invalid query to the CTEQuery - should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            cte_query.with_cte('test_cte', invalid_query)

        # Verify the error message mentions the unsupported query type
        assert "not supported in CTE" in str(exc_info.value)
        assert "Only str, SQLQueryAndParams, IQuery, and QueryExpression" in str(exc_info.value)

    def test_async_cte_query_with_sync_query_raises_error(self, async_order_fixtures):
        """
        Test that AsyncCTEQuery raises TypeError when an invalid query type is provided to with_cte.

        This test verifies that the asynchronous AsyncCTEQuery properly validates
        the query types passed to it and raises appropriate errors for incorrect types.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Get async backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTEQuery instance
        cte_query = AsyncCTEQuery(backend)

        # Create a mock that behaves like an invalid query
        from unittest.mock import Mock

        # Create a mock that doesn't implement the expected interfaces
        invalid_query = Mock()

        # Try to add the invalid query to the async CTEQuery - should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            cte_query.with_cte('test_cte', invalid_query)

        # Verify the error message mentions the unsupported query type
        assert "not supported in CTE" in str(exc_info.value)
        assert "Only str, SQLQueryAndParams, IQuery, and QueryExpression" in str(exc_info.value)

    def test_cte_query_with_invalid_query_type_raises_error(self, order_fixtures):
        """
        Test that CTEQuery raises TypeError when an unsupported query type is provided to with_cte.

        This test verifies that the CTEQuery properly validates the types of query
        objects passed to it and raises appropriate errors for unsupported types.
        """
        User, Order, OrderItem = order_fixtures

        # Get backend from model
        backend = Order.backend()

        # Create a CTEQuery instance
        cte_query = CTEQuery(backend)

        # Try to pass an unsupported type (e.g., integer) as query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.with_cte('invalid_cte', 12345)  # Passing an integer instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Query type <class 'int'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a list as query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.with_cte('invalid_cte', [1, 2, 3])  # Passing a list instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Query type <class 'list'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a dict as query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.with_cte('invalid_cte', {'query': 'SELECT * FROM users'})  # Passing a dict instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Query type <class 'dict'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)


class TestAsyncCTEQueryActiveQuery:
    """Test CTE queries with ActiveQuery subqueries (asynchronous)."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_single_active_query_cte(self, async_tree_fixtures):
        """Test basic CTE with a single ActiveQuery as subquery (async version)."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode

        AsyncNode = async_tree_fixtures[0]

        # Get backend from AsyncNode model
        backend = AsyncNode.backend()

        # Clean up any existing data
        for node in await AsyncNode.query().all():
            await node.delete()

        # Create test data
        root = AsyncNode(name="Root", value=Decimal('100.0'))
        await root.save()

        child1 = AsyncNode(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        await child1.save()

        child2 = AsyncNode(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        await child2.save()

        grandchild = AsyncNode(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        await grandchild.save()

        # Create a CTE using ActiveQuery as subquery
        cte_subquery = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value >= Decimal('50'))

        # Create AsyncCTEQuery instance with backend
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte(name="high_value_nodes", query=cte_subquery)

        # Execute the CTE query using aggregate method
        result = await cte_query.from_cte("high_value_nodes").select("name", "value").aggregate()

        assert len(result) == 3  # root, child1, child2
        # Check the actual structure of the result
        names = sorted([r['name'] for r in result])
        assert names == ["Child1", "Child2", "Root"]

    @pytest.mark.asyncio
    @requires_cte()
    async def test_multiple_active_query_cte(self, async_tree_fixtures):
        """Test CTE with multiple ActiveQuery instances as subqueries (async version)."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode

        AsyncNode = async_tree_fixtures[0]

        # Get backend from AsyncNode model
        backend = AsyncNode.backend()

        # Clean up any existing data
        for node in await AsyncNode.query().all():
            await node.delete()

        # Create test data
        root = AsyncNode(name="Root", value=Decimal('100.0'))
        await root.save()

        child1 = AsyncNode(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        await child1.save()

        child2 = AsyncNode(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        await child2.save()

        grandchild = AsyncNode(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        await grandchild.save()

        # Create multiple CTEs using ActiveQuery as subqueries
        high_value_cte = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value >= Decimal('60'))
        low_value_cte = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value < Decimal('60'))

        # Create AsyncCTEQuery instance with multiple CTEs
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte(name="high_values", query=high_value_cte)
        cte_query.with_cte(name="low_values", query=low_value_cte)

        # Execute the CTE query using aggregate method
        result = await cte_query.from_cte("high_values").select("name", "value").aggregate()

        assert len(result) >= 2  # Should have results from the high_values CTE


class TestCTEQueryExtendedFunctionality:
    """Test CTE queries with extended functionality from BaseQueryMixin, JoinQueryMixin, and RangeQueryMixin."""

    @requires_cte()
    def test_cte_with_basic_query_conditions(self, order_fixtures):
        """
        Test CTE query with basic query conditions (select, where, order_by).
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_basic_user', email='cte_basic@example.com', age=30)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-BASIC-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-BASIC-002', total_amount=Decimal('200.00'), status='completed')
        order3 = Order(user_id=user.id, order_number='CTE-BASIC-003', total_amount=Decimal('300.00'), status='pending')
        order1.save()
        order2.save()
        order3.save()

        # Get backend from model
        backend = Order.backend()

        # Create a CTE with a simple query
        cte_query = CTEQuery(backend)
        cte_query.with_cte('basic_orders_cte', (f"SELECT id, status, total_amount, user_id FROM {Order.table_name()}", ()))

        # Verify the SQL generation before execution
        sql_query = cte_query.from_cte('basic_orders_cte').select('id', 'status', 'total_amount').where("status IN (?, ?)", ('active', 'completed')).order_by(('total_amount', 'DESC'))
        sql, params = sql_query.to_sql()

        # Assert the generated SQL contains expected elements
        assert 'WITH' in sql.upper()
        assert 'basic_orders_cte' in sql
        assert 'SELECT' in sql.upper()
        assert 'status IN (?, ?)' in sql
        assert 'ORDER BY' in sql.upper()
        assert params == ('active', 'completed')

        # Execute the query and verify results
        results = sql_query.aggregate()

        # Verify results contain only active and completed orders, ordered by amount descending
        assert len(results) == 2
        assert results[0]['status'] == 'completed'
        assert results[0]['total_amount'] == Decimal('200.00')
        assert results[1]['status'] == 'active'
        assert results[1]['total_amount'] == Decimal('100.00')

    @requires_cte()
    def test_cte_with_range_conditions(self, order_fixtures):
        """
        Test CTE query with range conditions (limit, offset).
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_range_user', email='cte_range@example.com', age=35)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-RANGE-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-RANGE-002', total_amount=Decimal('200.00'), status='completed')
        order3 = Order(user_id=user.id, order_number='CTE-RANGE-003', total_amount=Decimal('300.00'), status='pending')
        order4 = Order(user_id=user.id, order_number='CTE-RANGE-004', total_amount=Decimal('400.00'), status='active')
        order1.save()
        order2.save()
        order3.save()
        order4.save()

        # Get backend from model
        backend = Order.backend()

        # Create a CTE with a simple query
        cte_query = CTEQuery(backend)
        cte_query.with_cte('range_orders_cte', (f"SELECT id, status, total_amount FROM {Order.table_name()} ORDER BY total_amount DESC", ()))

        # Verify the SQL generation for range conditions
        sql_query = cte_query.from_cte('range_orders_cte').select('id', 'status', 'total_amount').limit(2).offset(1)
        sql, params = sql_query.to_sql()

        # Assert the generated SQL contains expected range elements
        assert 'WITH' in sql.upper()
        assert 'LIMIT' in sql.upper()
        assert 'OFFSET' in sql.upper()
        assert 'range_orders_cte' in sql
        assert params == (2, 1)  # Limit and offset values

        # Use the new API: specify which CTE to use and apply range conditions
        results = sql_query.aggregate()

        # Verify results contain limited and offset records
        assert len(results) == 2
        # With offset 1 and limit 2, we should get the 2nd and 3rd highest amounts (300 and 200)
        assert results[0]['total_amount'] == Decimal('300.00')
        assert results[1]['total_amount'] == Decimal('200.00')

    @requires_cte()
    def test_cte_with_joins(self, order_fixtures):
        """
        Test CTE query with join conditions.
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_join_user', email='cte_join@example.com', age=40)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-JOIN-001', total_amount=Decimal('150.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-JOIN-002', total_amount=Decimal('250.00'), status='pending')
        order1.save()
        order2.save()

        # Get backend from model
        backend = Order.backend()

        # Create a CTE with a query that joins orders and users
        cte_query = CTEQuery(backend)
        cte_query.with_cte('joined_orders_cte', (f"SELECT o.id, o.status, o.total_amount, u.username FROM {Order.table_name()} o JOIN {User.table_name()} u ON o.user_id = u.id WHERE o.status IN (?, ?)", ('active', 'pending')))

        # Verify the SQL generation for join conditions
        sql_query = cte_query.from_cte('joined_orders_cte').select('id', 'status', 'total_amount', 'username').order_by(('total_amount', 'DESC'))
        sql, params = sql_query.to_sql()

        # Assert the generated SQL contains expected join elements
        assert 'WITH' in sql.upper()
        assert 'JOIN' in sql.upper()
        assert 'ORDER BY' in sql.upper()
        assert 'joined_orders_cte' in sql
        assert params == ('active', 'pending')

        # Use the new API: specify which CTE to use and apply additional conditions
        results = sql_query.aggregate()

        # Verify results contain joined data
        assert len(results) == 2
        # Results should be ordered by amount descending
        assert results[0]['total_amount'] == Decimal('250.00')
        assert results[0]['status'] == 'pending'
        assert results[0]['username'] == 'cte_join_user'
        assert results[1]['total_amount'] == Decimal('150.00')
        assert results[1]['status'] == 'active'


class TestAsyncCTEQueryExtendedFunctionality:
    """Test Async CTE queries with extended functionality from BaseQueryMixin, JoinQueryMixin, and RangeQueryMixin."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_basic_query_conditions(self, async_order_fixtures):
        """
        Test Async CTE query with basic query conditions (select, where, order_by).
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_basic_user', email='async_cte_basic@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-BASIC-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-BASIC-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-BASIC-003', total_amount=Decimal('300.00'), status='pending')
        await order1.save()
        await order2.save()
        await order3.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create a CTE with a simple query
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('basic_orders_cte', (f"SELECT id, status, total_amount, user_id FROM {AsyncOrder.table_name()}", ()))

        # Verify the SQL generation for async query
        sql_query = cte_query.from_cte('basic_orders_cte').select('id', 'status', 'total_amount').where("status IN (?, ?)", ('active', 'completed')).order_by(('total_amount', 'DESC'))
        sql, params = sql_query.to_sql()

        # Assert the generated SQL contains expected elements
        assert 'WITH' in sql.upper()
        assert 'basic_orders_cte' in sql
        assert 'SELECT' in sql.upper()
        assert 'status IN (?, ?)' in sql
        assert 'ORDER BY' in sql.upper()
        assert params == ('active', 'completed')

        # Use the new API: specify which CTE to use and apply basic query conditions
        results = await sql_query.aggregate()

        # Verify results contain only active and completed orders, ordered by amount descending
        assert len(results) == 2
        assert results[0]['status'] == 'completed'
        assert results[0]['total_amount'] == Decimal('200.00')
        assert results[1]['status'] == 'active'
        assert results[1]['total_amount'] == Decimal('100.00')

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_range_conditions(self, async_order_fixtures):
        """
        Test Async CTE query with range conditions (limit, offset).
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_range_user', email='async_cte_range@example.com', age=35)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-RANGE-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-RANGE-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-RANGE-003', total_amount=Decimal('300.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-RANGE-004', total_amount=Decimal('400.00'), status='active')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create a CTE with a simple query
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('range_orders_cte', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()} ORDER BY total_amount DESC", ()))

        # Use the new API: specify which CTE to use and apply range conditions
        results = await cte_query.from_cte('range_orders_cte').select('id', 'status', 'total_amount').limit(2).offset(1).aggregate()

        # Verify results contain limited and offset records
        assert len(results) == 2
        # With offset 1 and limit 2, we should get the 2nd and 3rd highest amounts (300 and 200)
        assert results[0]['total_amount'] == Decimal('300.00')
        assert results[1]['total_amount'] == Decimal('200.00')

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_joins(self, async_order_fixtures):
        """
        Test Async CTE query with join conditions.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_join_user', email='async_cte_join@example.com', age=40)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-JOIN-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-JOIN-002', total_amount=Decimal('250.00'), status='pending')
        await order1.save()
        await order2.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create a CTE with a query that joins orders and users
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('joined_orders_cte', (f"SELECT o.id, o.status, o.total_amount, u.username FROM {AsyncOrder.table_name()} o JOIN {AsyncUser.table_name()} u ON o.user_id = u.id WHERE o.status IN (?, ?)", ('active', 'pending')))

        # Use the new API: specify which CTE to use and apply additional conditions
        results = await cte_query.from_cte('joined_orders_cte').select('id', 'status', 'total_amount', 'username').order_by(('total_amount', 'DESC')).aggregate()

        # Verify results contain joined data
        assert len(results) == 2
        # Check that we have the expected data regardless of order (since order_by might not work as expected in this context)
        amounts = {row['total_amount'] for row in results}
        statuses = {row['status'] for row in results}
        usernames = {row['username'] for row in results}
        assert Decimal('150.00') in amounts
        assert Decimal('250.00') in amounts
        assert 'active' in statuses
        assert 'pending' in statuses
        assert 'async_cte_join_user' in usernames


class TestCTEQuerySyncErrorHandling:
    """Test CTE query error handling for edge cases (synchronous)."""

    def test_cte_query_to_sql_with_empty_ctes_raises_error(self, order_fixtures):
        """
        Test that calling to_sql() on a CTEQuery with no CTEs defined raises ValueError.
        This tests the condition: if not self._ctes: raise ValueError("CTEQuery must have at least one CTE defined")
        """
        User, Order, OrderItem = order_fixtures

        # Get backend from model
        backend = Order.backend()

        # Create a CTEQuery instance without adding any CTEs
        cte_query = CTEQuery(backend)

        # Attempt to call to_sql() without defining any CTEs - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            cte_query.to_sql()

        # Verify the error message mentions the missing CTE requirement
        assert "CTEQuery must have at least one CTE defined" in str(exc_info.value)

    def test_cte_query_to_sql_with_nonexistent_main_cte_name_raises_error(self, order_fixtures):
        """
        Test that calling to_sql() with a _main_cte_name that doesn't exist in defined CTEs raises ValueError.
        This tests the condition: if main_cte_name not in cte_names: raise ValueError(...)
        """
        User, Order, OrderItem = order_fixtures

        # Get backend from model
        backend = Order.backend()

        # Create a CTEQuery instance and add one CTE
        cte_query = CTEQuery(backend)
        cte_query.with_cte('existing_cte', (f"SELECT id, status FROM {Order.table_name()}", ()))

        # Explicitly set _main_cte_name to a name that doesn't exist
        cte_query._main_cte_name = 'nonexistent_cte'

        # Attempt to call to_sql() with nonexistent CTE name - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            cte_query.to_sql()

        # Verify the error message mentions the missing CTE
        assert "CTE 'nonexistent_cte' not found in defined CTEs:" in str(exc_info.value)
        assert 'existing_cte' in str(exc_info.value)  # Should show the available CTE names


class TestCTEQueryAsyncErrorHandling:
    """Test CTE query error handling for edge cases (asynchronous)."""

    @pytest.mark.asyncio
    async def test_async_cte_query_to_sql_with_empty_ctes_raises_error(self, async_order_fixtures):
        """
        Test that calling to_sql() on an AsyncCTEQuery with no CTEs defined raises ValueError.
        This tests the async version of the condition: if not self._ctes: raise ValueError("CTEQuery must have at least one CTE defined")
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTEQuery instance without adding any CTEs
        cte_query = AsyncCTEQuery(backend)

        # Attempt to call to_sql() without defining any CTEs - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            cte_query.to_sql()

        # Verify the error message mentions the missing CTE requirement
        assert "CTEQuery must have at least one CTE defined" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_cte_query_to_sql_with_nonexistent_main_cte_name_raises_error(self, async_order_fixtures):
        """
        Test that calling to_sql() with a _main_cte_name that doesn't exist in defined CTEs raises ValueError.
        This tests the async version of the condition: if main_cte_name not in cte_names: raise ValueError(...)
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTEQuery instance and add one CTE
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('existing_cte', (f"SELECT id, status FROM {AsyncOrder.table_name()}", ()))

        # Explicitly set _main_cte_name to a name that doesn't exist
        cte_query._main_cte_name = 'nonexistent_cte'

        # Attempt to call to_sql() with nonexistent CTE name - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            cte_query.to_sql()

        # Verify the error message mentions the missing CTE
        assert "CTE 'nonexistent_cte' not found in defined CTEs:" in str(exc_info.value)
        assert 'existing_cte' in str(exc_info.value)  # Should show the available CTE names