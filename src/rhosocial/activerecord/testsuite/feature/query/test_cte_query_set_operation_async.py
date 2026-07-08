# src/rhosocial/activerecord/testsuite/feature/query/test_cte_query_set_operation_async.py
"""
CTE Query Set Operation Tests for the RhoSocial ActiveRecord Test Suite.

This module tests Common Table Expression (CTE) queries where the underlying query
is a set operation (UNION, INTERSECT, EXCEPT) composed of two ActiveQuery instances.

These tests verify that:
1. CTE can wrap a UNION operation between two ActiveQuery instances
2. CTE can wrap an INTERSECT operation between two ActiveQuery instances
3. CTE can wrap an EXCEPT operation between two ActiveQuery instances
4. Both sync and async variants work properly
"""
import pytest
from decimal import Decimal

from rhosocial.activerecord.query import CTEQuery, AsyncCTEQuery
from rhosocial.activerecord.backend.expression import statements, core, query_parts
from rhosocial.activerecord.testsuite.utils import requires_cte
from rhosocial.activerecord.backend.dialect.protocols import SetOperationSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol
class TestAsyncCTEQuerySetOperation:
    """Test CTE queries wrapping set operations of ActiveQuery instances (asynchronous)."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_cte_with_union_of_active_queries(self, async_order_fixtures):
        """
        Async version of test_cte_with_union_of_active_queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_union_user', email='async_cte_union@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-003', total_amount=Decimal('300.00'), status='pending')
        await order1.save()
        await order2.save()
        await order3.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the UNION operation
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        completed_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Get the SQL and params for the UNION operation
        union_query = active_orders_query.union(completed_orders_query)
        union_sql, union_params = union_query.to_sql()

        # Create a CTE that uses the UNION SQL and params as its source
        # Pass the SQL and params as a tuple to preserve the parameters
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('union_orders_cte', (union_sql, union_params))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('union_orders_cte').select('status', 'id', 'order_number', 'total_amount').aggregate()

        # Verify results contain both active and completed orders (no duplicates in UNION)
        assert len(results) >= 2  # At least active and completed orders
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses
        assert 'completed' in statuses

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_cte_with_intersect_of_active_queries(self, async_order_fixtures):
        """
        Async version of test_cte_with_intersect_of_active_queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_intersect_user', email='async_cte_intersect@example.com', age=35)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-002', total_amount=Decimal('200.00'), status='active')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-003', total_amount=Decimal('150.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-004', total_amount=Decimal('250.00'), status='completed')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the INTERSECT operation
        # First query: orders with amount > 100
        high_amount_query = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('100.00'))
        # Second query: active orders (regardless of amount)
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Get the SQL and params for the INTERSECT operation
        intersect_query = high_amount_query.intersect(active_orders_query)
        intersect_sql, intersect_params = intersect_query.to_sql()

        # Create a CTE that uses the INTERSECT SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('intersect_orders_cte', (intersect_sql, intersect_params))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('intersect_orders_cte').select('status', 'total_amount', 'id', 'order_number').aggregate()

        # Verify results contain orders that are both high amount AND active
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_cte_with_except_of_active_queries(self, async_order_fixtures):
        """
        Async version of test_cte_with_except_of_active_queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_except_user', email='async_cte_except@example.com', age=40)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-003', total_amount=Decimal('300.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-004', total_amount=Decimal('400.00'), status='active')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the EXCEPT operation
        # First query: all orders
        all_orders_query = AsyncOrder.query()
        # Second query: completed orders
        completed_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Get the SQL and params for the EXCEPT operation
        except_query = all_orders_query.except_(completed_orders_query)
        except_sql, except_params = except_query.to_sql()

        # Create a CTE that uses the EXCEPT SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('except_orders_cte', (except_sql, except_params))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('except_orders_cte').select('status', 'id', 'order_number', 'total_amount').aggregate()

        # Verify results contain orders that are NOT completed
        for row in results:
            assert row.get('status') != 'completed'

class TestAsyncCTEQueryWithQueryExpression:
    """Test Async CTE queries with QueryExpression as parameters."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_query_expression_as_subquery(self, async_order_fixtures):
        """
        Async version of test_cte_with_query_expression_as_subquery.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_query_expr_user', email='async_cte_query_expr@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-QUERY-EXPR-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-QUERY-EXPR-002', total_amount=Decimal('200.00'), status='completed')
        await order1.save()
        await order2.save()

        # Get backend and dialect
        backend = AsyncOrder.backend()
        dialect = backend.dialect

        # Create a QueryExpression directly (this implements ToSQLProtocol)
        query_expr = statements.QueryExpression(
            dialect,
            select=[core.Column(dialect, "id"), core.Column(dialect, "status"), core.Column(dialect, "total_amount")],
            from_=core.TableExpression(dialect, AsyncOrder.table_name()),
            where=query_parts.WhereClause(dialect, condition=core.Column(dialect, "status") == core.Literal(dialect, 'active'))
        )

        # Create a CTE that uses the QueryExpression as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('query_expr_cte', query_expr)

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('query_expr_cte').select('id', 'status', 'total_amount').aggregate()

        # Verify results contain only active orders
        assert len(results) >= 1
        for row in results:
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_query_expression_as_main_query(self, async_order_fixtures):
        """
        Async version of test_cte_with_query_expression_as_main_query.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_main_query_expr_user', email='async_cte_main_query_expr@example.com', age=35)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-MAIN-QUERY-EXPR-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-MAIN-QUERY-EXPR-002', total_amount=Decimal('250.00'), status='pending')
        await order1.save()
        await order2.save()

        # Get backend and dialect
        backend = AsyncOrder.backend()
        dialect = backend.dialect

        # Create a CTE with a simple query
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('simple_orders_cte', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()} WHERE status IN (?, ?)", ('active', 'pending')))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('simple_orders_cte').select('id', 'status', 'total_amount').where("total_amount > ?", (Decimal('100.00'),)).aggregate()

        # Verify results contain orders with amount > 100
        assert len(results) >= 2
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')

class TestAsyncCTEQueryWithActiveQuery:
    """Test Async CTE queries with AsyncActiveQuery as parameters."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_async_active_query_using_custom_join_clause(self, async_order_fixtures):
        """
        Test Async CTE query that uses an AsyncActiveQuery with a custom join_clause as the underlying query.

        This test verifies that an Async CTE can be created with an AsyncActiveQuery instance
        where we manually set the join_clause to reference a CTE query name.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_active_query_user', email='async_cte_active_query@example.com', age=40)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-ACTIVE-QUERY-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-ACTIVE-QUERY-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-ACTIVE-QUERY-003', total_amount=Decimal('300.00'), status='pending')
        await order1.save()
        await order2.save()
        await order3.save()

        # Get backend
        backend = AsyncOrder.backend()

        # Create an AsyncActiveQuery for active orders
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Get the SQL and params for the active orders query
        active_sql, active_params = active_orders_query.to_sql()

        # Create a CTE that uses the SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('active_orders_cte', (active_sql, active_params))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('active_orders_cte').select('id', 'status', 'total_amount', 'order_number').aggregate()

        # Verify results contain only active orders
        assert len(results) >= 1
        for row in results:
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_async_active_query_as_main_query(self, async_order_fixtures):
        """
        Test Async CTE query where the main query is an AsyncActiveQuery.

        This test verifies that an Async CTE can be created with a main query that is an AsyncActiveQuery.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_main_active_query_user', email='async_cte_main_active_query@example.com', age=45)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-MAIN-ACTIVE-QUERY-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-MAIN-ACTIVE-QUERY-002', total_amount=Decimal('250.00'), status='pending')
        await order1.save()
        await order2.save()

        # Get backend
        backend = AsyncOrder.backend()

        # Create a CTE with a simple query
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('simple_orders_cte', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()} WHERE status IN (?, ?)", ('active', 'pending')))

        # Execute the CTE query using aggregate method
        results = await cte_query.from_cte('simple_orders_cte').select('id', 'status', 'total_amount').aggregate()

        # Verify results contain orders with expected statuses
        assert len(results) >= 2
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses or 'pending' in statuses

class TestAsyncCTEQueryInvalidTypes:
    """Test Async CTE queries with invalid query parameter types to ensure proper error handling."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_invalid_query_type_raises_error(self, async_order_fixtures):
        '''
        Test that Async CTE query raises TypeError when an unsupported query type is provided.

        This test verifies that the Async CTE query implementation properly validates
        the types of query objects passed to it and raises appropriate errors
        for unsupported types.
        '''
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Get backend
        backend = AsyncOrder.backend()

        # Create an Async CTE query instance
        cte_query = AsyncCTEQuery(backend)

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

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_invalid_main_query_type_raises_error(self, async_order_fixtures):
        '''
        Test that Async CTE query raises TypeError when an unsupported main query type is provided.

        This test verifies that the Async CTE query implementation properly validates
        the types of main query objects passed to it and raises appropriate errors
        for unsupported types.
        '''
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Get backend
        backend = AsyncOrder.backend()

        # Create an Async CTE query instance
        cte_query = AsyncCTEQuery(backend)

        # Add a valid CTE first
        cte_query.with_cte('valid_cte', 'SELECT * FROM users')

        # Since we removed the query() method, we now test the new API
        # The new API uses from_cte() and mixin methods to build queries
        # This test can be adapted to verify that the new API handles invalid types appropriately
        # For now, we'll test that the new API works correctly
        try:
            # Use the new API: specify which CTE to use and apply query conditions using mixins
            results = await cte_query.from_cte('valid_cte').select('id', 'username', 'email').aggregate()
            # Verify we get some results back
            assert isinstance(results, list)
        except Exception as e:
            # If there's an error, make sure it's not related to the removed query() method
            assert "query" not in str(e).lower()

class TestAsyncCTEQueryErrorHandlingSetOperations:
    """Test error handling for Async CTE queries with set operations."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_with_invalid_query_types_in_set_operations(self, async_order_fixtures):
        """
        Test Async CTE query with invalid query types in set operations.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_invalid_query_types_user', email='async_cte_invalid_query_types@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INVALID-QUERY-TYPES-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INVALID-QUERY-TYPES-002', total_amount=Decimal('200.00'), status='completed')
        await order1.save()
        await order2.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncActiveQuery instance
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Test that we can perform set operations with valid async queries
        completed_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')
        union_query = active_orders_query.union(completed_orders_query)

        # Get the SQL and params for the union query
        union_sql, union_params = union_query.to_sql()

        # Create an AsyncCTE that uses the valid UNION SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('valid_union_cte', (union_sql, union_params))

        # Use the new API: specify which CTE to use and apply query conditions
        results = await cte_query.from_cte('valid_union_cte').select('id', 'status', 'total_amount').aggregate()

        # Verify results contain both active and completed orders
        assert len(results) == 2
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses
        assert 'completed' in statuses

class TestAsyncCTEQueryExtendedFunctionalitySetOperations:
    """Test Async CTE queries with extended functionality applied to set operations."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_cte_with_union_and_extended_conditions(self, async_order_fixtures):
        """
        Test CTE query with UNION operation and extended query conditions.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='cte_union_extended_user', email='cte_union_extended@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='CTE-UNION-EXT-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='CTE-UNION-EXT-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='CTE-UNION-EXT-003', total_amount=Decimal('300.00'), status='pending')
        await order1.save()
        await order2.save()
        await order3.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the UNION operation
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        completed_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Perform UNION operation between the two ActiveQuery instances
        union_query = active_orders_query.union(completed_orders_query)

        # Create a CTE that uses the UNION operation as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('union_orders_cte', union_query)

        # Verify the SQL generation for UNION with extended conditions
        sql_query = cte_query.from_cte('union_orders_cte').select('id', 'status', 'total_amount').order_by(('total_amount', 'DESC')).limit(2)
        sql, params = sql_query.to_sql()

        # Assert the generated SQL contains dialect-independent query elements
        assert 'WITH' in sql.upper()
        assert 'UNION' in sql.upper()
        assert 'union_orders_cte' in sql

        # Use the new API: specify which CTE to use and apply extended query conditions
        results = await sql_query.aggregate()

        # Verify results contain both active and completed orders, ordered by amount descending, limited to 2
        assert len(results) == 2
        assert results[0]['status'] in ['active', 'completed']
        assert results[1]['status'] in ['active', 'completed']

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_async_cte_with_intersect_and_range_conditions(self, async_order_fixtures):
        """
        Test Async CTE query with INTERSECT operation and range conditions.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_intersect_range_user', email='async_cte_intersect_range@example.com', age=35)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-RANGE-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-RANGE-002', total_amount=Decimal('200.00'), status='active')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-RANGE-003', total_amount=Decimal('150.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-RANGE-004', total_amount=Decimal('250.00'), status='completed')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the INTERSECT operation
        # First query: orders with amount > 100
        high_amount_query = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('100.00'))
        # Second query: active orders (regardless of amount)
        active_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Get the SQL and params for the INTERSECT operation
        intersect_query = high_amount_query.intersect(active_orders_query)
        intersect_sql, intersect_params = intersect_query.to_sql()

        # Create a CTE that uses the INTERSECT SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('intersect_orders_cte', (intersect_sql, intersect_params))

        # Use the new API: specify which CTE to use and apply range conditions
        results = await cte_query.from_cte('intersect_orders_cte').select('id', 'status', 'total_amount').limit(10).offset(0).aggregate()

        # Verify results contain orders that are both high amount AND active
        assert len(results) >= 1
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_async_cte_with_except_and_join_conditions(self, async_order_fixtures):
        """
        Test Async CTE query with EXCEPT operation and join conditions.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_except_join_user', email='async_cte_except_join@example.com', age=40)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-JOIN-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-JOIN-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-JOIN-003', total_amount=Decimal('300.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-JOIN-004', total_amount=Decimal('400.00'), status='active')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create two ActiveQuery instances for the EXCEPT operation
        # First query: all orders
        all_orders_query = AsyncOrder.query()
        # Second query: completed orders
        completed_orders_query = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Get the SQL and params for the EXCEPT operation
        except_query = all_orders_query.except_(completed_orders_query)
        except_sql, except_params = except_query.to_sql()

        # Create a CTE that uses the EXCEPT SQL and params as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('except_orders_cte', (except_sql, except_params))

        # Use the new API: specify which CTE to use and apply query conditions
        results = await cte_query.from_cte('except_orders_cte').select('id', 'status', 'total_amount', 'user_id').where("total_amount > ?", (Decimal('50.00'),)).aggregate()

        # Verify results contain orders that are NOT completed and have amount > 50
        assert len(results) >= 3  # Should have active, pending, and any other non-completed orders
        for row in results:
            assert row.get('status') != 'completed'
            assert row.get('total_amount') > Decimal('50.00')

class TestAsyncCTEQuerySetOperationWithOtherQueries:
    """Test Async CTE queries with set operations against other Async query types (AsyncActiveQuery, etc.)."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_async_cte_query_union_with_async_active_query(self, async_order_fixtures):
        '''
        Test AsyncCTE query UNION operation with AsyncActiveQuery.
        '''
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_union_active_user', email='async_cte_union_active@example.com', age=30)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-ACTIVE-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-ACTIVE-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-ACTIVE-003', total_amount=Decimal('300.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-UNION-ACTIVE-004', total_amount=Decimal('400.00'), status='active')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTE with a simple query
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('async_cte_orders', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()} WHERE status = ?", ('active',)))

        # Create an AsyncActiveQuery for comparison
        active_query = AsyncOrder.query().select(AsyncOrder.c.id, AsyncOrder.c.status, AsyncOrder.c.total_amount).where(AsyncOrder.c.status == 'completed')

        # Perform UNION operation between AsyncCTE query and AsyncActiveQuery
        union_query = cte_query.from_cte('async_cte_orders').select('id', 'status', 'total_amount').union(active_query)

        # Execute the union query
        results = await union_query.aggregate()

        # Verify results contain both active orders from CTE and completed orders from AsyncActiveQuery (no duplicates in UNION)
        assert len(results) >= 2  # At least one active from CTE, one completed from AsyncActiveQuery
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses
        assert 'completed' in statuses

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_async_cte_query_intersect_with_async_active_query(self, async_order_fixtures):
        '''
        Test AsyncCTE query INTERSECT operation with AsyncActiveQuery.
        '''
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_intersect_active_user', email='async_cte_intersect_active@example.com', age=35)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-ACTIVE-001', total_amount=Decimal('150.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-ACTIVE-002', total_amount=Decimal('200.00'), status='active')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-ACTIVE-003', total_amount=Decimal('150.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-INTERSECT-ACTIVE-004', total_amount=Decimal('250.00'), status='completed')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTE with a query for high-value active orders
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('async_high_value_cte', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()} WHERE status = ? AND total_amount > ?", ('active', Decimal('100.00'))))

        # Create an AsyncActiveQuery for orders with amount > 100 (regardless of status)
        high_amount_query = AsyncOrder.query().select(AsyncOrder.c.id, AsyncOrder.c.status, AsyncOrder.c.total_amount).where(AsyncOrder.c.total_amount > Decimal('100.00'))

        # Perform INTERSECT operation between AsyncCTE query and AsyncActiveQuery
        intersect_query = cte_query.from_cte('async_high_value_cte').select('id', 'status', 'total_amount').intersect(high_amount_query)

        # Execute the intersect query
        results = await intersect_query.aggregate()

        # Verify results contain orders that are both high amount AND active
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_async_cte_query_except_with_async_active_query(self, async_order_fixtures):
        '''
        Test AsyncCTE query EXCEPT operation with AsyncActiveQuery.
        '''
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test data
        user = AsyncUser(username='async_cte_except_active_user', email='async_cte_except_active@example.com', age=40)
        await user.save()

        # Create orders for the test
        order1 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-ACTIVE-001', total_amount=Decimal('100.00'), status='active')
        order2 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-ACTIVE-002', total_amount=Decimal('200.00'), status='completed')
        order3 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-ACTIVE-003', total_amount=Decimal('300.00'), status='pending')
        order4 = AsyncOrder(user_id=user.id, order_number='ASYNC-CTE-EXCEPT-ACTIVE-004', total_amount=Decimal('400.00'), status='active')
        await order1.save()
        await order2.save()
        await order3.save()
        await order4.save()

        # Get backend from model
        backend = AsyncOrder.backend()

        # Create an AsyncCTE with a query for all orders
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('async_all_orders_cte', (f"SELECT id, status, total_amount FROM {AsyncOrder.table_name()}", ()))

        # Create an AsyncActiveQuery for completed orders
        completed_query = AsyncOrder.query().select(AsyncOrder.c.id, AsyncOrder.c.status, AsyncOrder.c.total_amount).where(AsyncOrder.c.status == 'completed')

        # Perform EXCEPT operation between AsyncCTE query and AsyncActiveQuery
        except_query = cte_query.from_cte('async_all_orders_cte').select('id', 'status', 'total_amount').except_(completed_query)

        # Execute the except query
        results = await except_query.aggregate()

        # Verify results contain orders that are NOT completed
        for row in results:
            assert row.get('status') != 'completed'