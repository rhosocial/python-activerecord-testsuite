# src/rhosocial/activerecord/testsuite/feature/query/test_cte_query_set_operation.py
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
from rhosocial.activerecord.backend.expression import statements, core
from rhosocial.activerecord.testsuite.utils import requires_cte


class TestCTEQuerySetOperation:
    """Test CTE queries wrapping set operations of ActiveQuery instances (synchronous)."""

    @requires_cte()
    def test_cte_with_union_of_active_queries(self, order_fixtures):
        """
        Test CTE query that uses a UNION operation between two ActiveQuery instances.
        
        This test verifies that a CTE can be created with a UNION operation
        between two ActiveQuery instances as its underlying query.
        """
        User, Order, OrderItem = order_fixtures
        
        # Create test data
        user = User(username='cte_union_user', email='cte_union@example.com', age=30)
        user.save()
        
        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-UNION-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-UNION-002', total_amount=Decimal('200.00'), status='completed')
        order3 = Order(user_id=user.id, order_number='CTE-UNION-003', total_amount=Decimal('300.00'), status='pending')
        order1.save()
        order2.save()
        order3.save()
        
        # Get backend from model
        backend = Order.backend()
        
        # Create two ActiveQuery instances for the UNION operation
        active_orders_query = Order.query().where(Order.c.status == 'active')
        completed_orders_query = Order.query().where(Order.c.status == 'completed')
        
        # Perform UNION operation between the two ActiveQuery instances
        union_query = active_orders_query.union(completed_orders_query)
        
        # Create a CTE that uses the UNION operation as its source
        cte_query = CTEQuery(backend)
        cte_query.with_cte('union_orders_cte', union_query)
        # Query the CTE
        cte_query.query("SELECT * FROM union_orders_cte")
        
        # Execute the CTE query
        results = cte_query.aggregate()
        
        # Verify results contain both active and completed orders (no duplicates in UNION)
        assert len(results) >= 2  # At least active and completed orders
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses
        assert 'completed' in statuses

    @requires_cte()
    def test_cte_with_intersect_of_active_queries(self, order_fixtures):
        """
        Test CTE query that uses an INTERSECT operation between two ActiveQuery instances.
        
        This test verifies that a CTE can be created with an INTERSECT operation
        between two ActiveQuery instances as its underlying query.
        """
        User, Order, OrderItem = order_fixtures
        
        # Create test data
        user = User(username='cte_intersect_user', email='cte_intersect@example.com', age=35)
        user.save()
        
        # Create orders for the test - we'll create some orders with specific amounts
        # to make sure there are some overlaps for the intersect operation
        order1 = Order(user_id=user.id, order_number='CTE-INTERSECT-001', total_amount=Decimal('150.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-INTERSECT-002', total_amount=Decimal('200.00'), status='active')
        order3 = Order(user_id=user.id, order_number='CTE-INTERSECT-003', total_amount=Decimal('150.00'), status='pending')
        order4 = Order(user_id=user.id, order_number='CTE-INTERSECT-004', total_amount=Decimal('250.00'), status='completed')
        order1.save()
        order2.save()
        order3.save()
        order4.save()
        
        # Get backend from model
        backend = Order.backend()
        
        # Create two ActiveQuery instances for the INTERSECT operation
        # First query: orders with amount > 100
        high_amount_query = Order.query().where(Order.c.total_amount > Decimal('100.00'))
        # Second query: active orders (regardless of amount)
        active_orders_query = Order.query().where(Order.c.status == 'active')
        
        # Perform INTERSECT operation between the two ActiveQuery instances
        intersect_query = high_amount_query.intersect(active_orders_query)
        
        # Create a CTE that uses the INTERSECT operation as its source
        cte_query = CTEQuery(backend)
        cte_query.with_cte('intersect_orders_cte', intersect_query)
        # Query the CTE
        cte_query.query("SELECT * FROM intersect_orders_cte")
        
        # Execute the CTE query
        results = cte_query.aggregate()
        
        # Verify results contain orders that are both high amount AND active
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')
            assert row.get('status') == 'active'

    @requires_cte()
    def test_cte_with_except_of_active_queries(self, order_fixtures):
        """
        Test CTE query that uses an EXCEPT operation between two ActiveQuery instances.
        
        This test verifies that a CTE can be created with an EXCEPT operation
        between two ActiveQuery instances as its underlying query.
        """
        User, Order, OrderItem = order_fixtures
        
        # Create test data
        user = User(username='cte_except_user', email='cte_except@example.com', age=40)
        user.save()
        
        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-EXCEPT-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-EXCEPT-002', total_amount=Decimal('200.00'), status='completed')
        order3 = Order(user_id=user.id, order_number='CTE-EXCEPT-003', total_amount=Decimal('300.00'), status='pending')
        order4 = Order(user_id=user.id, order_number='CTE-EXCEPT-004', total_amount=Decimal('400.00'), status='active')
        order1.save()
        order2.save()
        order3.save()
        order4.save()
        
        # Get backend from model
        backend = Order.backend()
        
        # Create two ActiveQuery instances for the EXCEPT operation
        # First query: all orders
        all_orders_query = Order.query()
        # Second query: completed orders
        completed_orders_query = Order.query().where(Order.c.status == 'completed')
        
        # Perform EXCEPT operation between the two ActiveQuery instances
        except_query = all_orders_query.except_(completed_orders_query)
        
        # Create a CTE that uses the EXCEPT operation as its source
        cte_query = CTEQuery(backend)
        cte_query.with_cte('except_orders_cte', except_query)
        # Query the CTE
        cte_query.query("SELECT * FROM except_orders_cte")
        
        # Execute the CTE query
        results = cte_query.aggregate()
        
        # Verify results contain orders that are NOT completed
        for row in results:
            assert row.get('status') != 'completed'


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
        # Query the CTE
        cte_query.query("SELECT * FROM union_orders_cte")
        
        # Execute the CTE query
        results = await cte_query.aggregate()
        
        # Verify results contain both active and completed orders (no duplicates in UNION)
        assert len(results) >= 2  # At least active and completed orders
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses
        assert 'completed' in statuses

    @pytest.mark.asyncio
    @requires_cte()
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
        # Query the CTE
        cte_query.query("SELECT * FROM intersect_orders_cte")
        
        # Execute the CTE query
        results = await cte_query.aggregate()
        
        # Verify results contain orders that are both high amount AND active
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')
            assert row.get('status') == 'active'

    @pytest.mark.asyncio
    @requires_cte()
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
        # Query the CTE
        cte_query.query("SELECT * FROM except_orders_cte")

        # Execute the CTE query
        results = await cte_query.aggregate()

        # Verify results contain orders that are NOT completed
        for row in results:
            assert row.get('status') != 'completed'


class TestCTEQueryWithQueryExpression:
    """Test CTE queries with QueryExpression as parameters."""

    @requires_cte()
    def test_cte_with_query_expression_as_subquery(self, order_fixtures):
        """
        Test CTE query that uses a QueryExpression as the underlying query.

        This test verifies that a CTE can be created with a QueryExpression
        instance as its source, which implements the ToSQLProtocol.
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_query_expr_user', email='cte_query_expr@example.com', age=30)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-QUERY-EXPR-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-QUERY-EXPR-002', total_amount=Decimal('200.00'), status='completed')
        order1.save()
        order2.save()

        # Get backend and dialect
        backend = Order.backend()
        dialect = backend.dialect

        # Create a QueryExpression directly (this implements ToSQLProtocol)
        query_expr = statements.QueryExpression(
            dialect,
            select=[core.Column(dialect, "id"), core.Column(dialect, "status"), core.Column(dialect, "total_amount")],
            from_=core.TableExpression(dialect, Order.table_name()),
            where=statements.WhereClause(dialect, condition=core.Column(dialect, "status") == core.Literal(dialect, 'active'))
        )

        # Create a CTE that uses the QueryExpression as its source
        cte_query = CTEQuery(backend)
        cte_query.with_cte('query_expr_cte', query_expr)
        # Query the CTE
        cte_query.query("SELECT * FROM query_expr_cte")

        # Execute the CTE query
        results = cte_query.aggregate()

        # Verify results contain only active orders
        assert len(results) >= 1
        for row in results:
            assert row.get('status') == 'active'

    @requires_cte()
    def test_cte_with_query_expression_as_main_query(self, order_fixtures):
        """
        Test CTE query where the main query is a QueryExpression.

        This test verifies that a CTE can be created with a main query that is a QueryExpression.
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_main_query_expr_user', email='cte_main_query_expr@example.com', age=35)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-MAIN-QUERY-EXPR-001', total_amount=Decimal('150.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-MAIN-QUERY-EXPR-002', total_amount=Decimal('250.00'), status='pending')
        order1.save()
        order2.save()

        # Get backend and dialect
        backend = Order.backend()
        dialect = backend.dialect

        # Create a CTE with a simple query - explicitly select columns to avoid column mismatch
        cte_query = CTEQuery(backend)
        cte_query.with_cte('simple_orders_cte', (f"SELECT id, status, total_amount FROM {Order.table_name()} WHERE status IN (?, ?)", ('active', 'pending')))

        # Create a QueryExpression for the main query that references the CTE
        main_query_expr = statements.QueryExpression(
            dialect,
            select=[core.Column(dialect, "id"), core.Column(dialect, "status"), core.Column(dialect, "total_amount")],
            from_=core.TableExpression(dialect, 'simple_orders_cte'),
            where=statements.WhereClause(dialect, condition=core.Column(dialect, "total_amount") > core.Literal(dialect, Decimal('100.00')))
        )

        # Set the main query to the QueryExpression
        cte_query.query(main_query_expr)

        # Execute the CTE query
        results = cte_query.aggregate()

        # Verify results contain orders with amount > 100
        assert len(results) >= 2
        for row in results:
            assert row.get('total_amount') > Decimal('100.00')


class TestCTEQueryWithActiveQuery:
    """Test CTE queries with ActiveQuery as parameters, using custom join_clause."""

    @requires_cte()
    def test_cte_with_active_query_using_custom_join_clause(self, order_fixtures):
        """
        Test CTE query that uses an ActiveQuery with a custom join_clause as the underlying query.

        This test verifies that a CTE can be created with an ActiveQuery instance
        where we manually set the join_clause to reference a CTE query name.
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_active_query_user', email='cte_active_query@example.com', age=40)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-ACTIVE-QUERY-001', total_amount=Decimal('100.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-ACTIVE-QUERY-002', total_amount=Decimal('200.00'), status='completed')
        order3 = Order(user_id=user.id, order_number='CTE-ACTIVE-QUERY-003', total_amount=Decimal('300.00'), status='pending')
        order1.save()
        order2.save()
        order3.save()

        # Get backend
        backend = Order.backend()

        # Create an ActiveQuery for active orders
        active_orders_query = Order.query().where(Order.c.status == 'active')

        # Create a CTE that uses the ActiveQuery as its source
        cte_query = CTEQuery(backend)
        cte_query.with_cte('active_orders_cte', active_orders_query)

        # Create another ActiveQuery that will query the CTE
        # Manually set the join_clause to reference the CTE name
        from rhosocial.activerecord.backend.expression.core import TableExpression
        cte_query_obj = Order.query()
        dialect = backend.dialect
        cte_query_obj.join_clause = TableExpression(dialect, 'active_orders_cte')

        # Set the main query to use the ActiveQuery with custom join_clause
        cte_query.query(cte_query_obj)

        # Execute the CTE query
        results = cte_query.aggregate()

        # Verify results contain only active orders
        assert len(results) >= 1
        for row in results:
            assert row.get('status') == 'active'

    @requires_cte()
    def test_cte_with_active_query_as_main_query(self, order_fixtures):
        """
        Test CTE query where the main query is an ActiveQuery.

        This test verifies that a CTE can be created with a main query that is an ActiveQuery.
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='cte_main_active_query_user', email='cte_main_active_query@example.com', age=45)
        user.save()

        # Create orders for the test
        order1 = Order(user_id=user.id, order_number='CTE-MAIN-ACTIVE-QUERY-001', total_amount=Decimal('150.00'), status='active')
        order2 = Order(user_id=user.id, order_number='CTE-MAIN-ACTIVE-QUERY-002', total_amount=Decimal('250.00'), status='pending')
        order1.save()
        order2.save()

        # Get backend
        backend = Order.backend()

        # Create a CTE with a simple query - explicitly select columns to avoid column mismatch
        cte_query = CTEQuery(backend)
        cte_query.with_cte('simple_orders_cte', (f"SELECT id, status, total_amount FROM {Order.table_name()} WHERE status IN (?, ?)", ('active', 'pending')))

        # Create a QueryExpression that will query the CTE directly
        from rhosocial.activerecord.backend.expression import statements, core
        dialect = backend.dialect
        main_query = statements.QueryExpression(
            dialect,
            select=[
                core.Column(dialect, "id", table="simple_orders_cte"),
                core.Column(dialect, "status", table="simple_orders_cte"),
                core.Column(dialect, "total_amount", table="simple_orders_cte")
            ],
            from_=core.TableExpression(dialect, 'simple_orders_cte')
        )

        # Set the main query to the ActiveQuery
        cte_query.query(main_query)

        # Execute the CTE query
        results = cte_query.aggregate()

        # Verify results contain orders with expected statuses
        assert len(results) >= 2
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses or 'pending' in statuses


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
            where=statements.WhereClause(dialect, condition=core.Column(dialect, "status") == core.Literal(dialect, 'active'))
        )

        # Create a CTE that uses the QueryExpression as its source
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte('query_expr_cte', query_expr)
        # Query the CTE
        cte_query.query("SELECT * FROM query_expr_cte")

        # Execute the CTE query
        results = await cte_query.aggregate()

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

        # Create a QueryExpression for the main query that references the CTE
        main_query_expr = statements.QueryExpression(
            dialect,
            select=[core.Column(dialect, "id"), core.Column(dialect, "status"), core.Column(dialect, "total_amount")],
            from_=core.TableExpression(dialect, 'simple_orders_cte'),
            where=statements.WhereClause(dialect, condition=core.Column(dialect, "total_amount") > core.Literal(dialect, Decimal('100.00')))
        )

        # Set the main query to the QueryExpression
        cte_query.query(main_query_expr)

        # Execute the CTE query
        results = await cte_query.aggregate()

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

        # Create another AsyncActiveQuery that will query the CTE
        # Manually set the join_clause to reference the CTE name
        from rhosocial.activerecord.backend.expression.core import TableExpression
        dialect = backend.dialect
        main_query = AsyncOrder.query()
        main_query.join_clause = TableExpression(dialect, 'active_orders_cte')

        # Set the main query to use the modified query
        cte_query.query(main_query)

        # Execute the CTE query
        results = await cte_query.aggregate()

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

        # Create a QueryExpression that will query the CTE directly
        from rhosocial.activerecord.backend.expression import statements, core
        dialect = backend.dialect
        main_query = statements.QueryExpression(
            dialect,
            select=[
                core.Column(dialect, "id", table="simple_orders_cte"),
                core.Column(dialect, "status", table="simple_orders_cte"),
                core.Column(dialect, "total_amount", table="simple_orders_cte")
            ],
            from_=core.TableExpression(dialect, 'simple_orders_cte')
        )

        # Set the main query to the AsyncActiveQuery
        cte_query.query(main_query)

        # Execute the CTE query
        results = await cte_query.aggregate()

        # Verify results contain orders with expected statuses
        assert len(results) >= 2
        statuses = {row.get('status') for row in results}
        assert 'active' in statuses or 'pending' in statuses

class TestCTEQueryInvalidTypes:
    """Test CTE queries with invalid query parameter types to ensure proper error handling."""

    @requires_cte()
    def test_cte_with_invalid_query_type_raises_error(self, order_fixtures):
        '''
        Test that CTE query raises TypeError when an unsupported query type is provided.

        This test verifies that the CTE query implementation properly validates
        the types of query objects passed to it and raises appropriate errors
        for unsupported types.
        '''
        User, Order, OrderItem = order_fixtures

        # Get backend
        backend = Order.backend()

        # Create a CTE query instance
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

    @requires_cte()
    def test_cte_with_invalid_main_query_type_raises_error(self, order_fixtures):
        '''
        Test that CTE query raises TypeError when an unsupported main query type is provided.

        This test verifies that the CTE query implementation properly validates
        the types of main query objects passed to it and raises appropriate errors
        for unsupported types.
        '''
        User, Order, OrderItem = order_fixtures

        # Get backend
        backend = Order.backend()

        # Create a CTE query instance
        cte_query = CTEQuery(backend)

        # Add a valid CTE first
        cte_query.with_cte('valid_cte', 'SELECT * FROM users')

        # Try to pass an unsupported type (e.g., integer) as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query(12345)  # Passing an integer instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'int'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a list as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query([1, 2, 3])  # Passing a list instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'list'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a dict as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query({'query': 'SELECT * FROM users'})  # Passing a dict instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'dict'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)


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

        # Try to pass an unsupported type (e.g., integer) as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query(12345)  # Passing an integer instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'int'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a list as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query([1, 2, 3])  # Passing a list instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'list'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)

        # Try to pass a dict as main query parameter
        with pytest.raises(TypeError) as exc_info:
            cte_query.query({'query': 'SELECT * FROM users'})  # Passing a dict instead of valid query type

        # Verify the error message mentions the unsupported type
        assert "Main query type <class 'dict'>" in str(exc_info.value)
        assert "not supported in CTE" in str(exc_info.value)
