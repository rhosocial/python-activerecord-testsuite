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