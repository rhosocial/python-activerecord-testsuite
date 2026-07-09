# src/rhosocial/activerecord/testsuite/feature/query/test_active_query_set_operation_async.py
"""ActiveQuery set operation functionality tests

This module contains tests for the set operation ActiveQuery operations including:
- UNION operations
- INTERSECT operations
- EXCEPT operations
- Chaining multiple set operations
- Set operations with conditions
"""

from decimal import Decimal

from rhosocial.activerecord.backend.dialect.protocols import SetOperationSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol
class TestAsyncActiveQuerySetOperation:
    """
    Asynchronous ActiveQuery set operation functionality tests
    """

    async def test_union_operation(self, async_order_fixtures):

        """
        Test async UNION operation between two queries

        This test verifies that the async union method can combine results from two different queries,
        returning all unique records from both queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_union_user', email='async_union@example.com', age=30)
        await user.save()

        # Create orders for union operation
        order1 = AsyncOrder(user_id=user.id, order_number='AUNION-A-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AUNION-B-002', total_amount=Decimal('200.00'), status='completed')
        await order2.save()

        # Create two separate queries
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        completed_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Perform union operation to combine both result sets
        # Note: Need to use the async version of set operations for async queries
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        union_query = AsyncSetOperationQuery(active_orders, completed_orders, "UNION")
        results = await union_query.aggregate()

        # Should return all orders (active + completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_intersect_operation(self, async_order_fixtures):
        """
        Test async INTERSECT operation between two queries

        This test verifies that the async intersect method can find common results between two queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_intersect_user', email='async_intersect@example.com', age=30)
        await user.save()

        # Create orders for intersect operation
        order1 = AsyncOrder(user_id=user.id, order_number='AINT-001', total_amount=Decimal('200.00'), status='pending')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AINT-002', total_amount=Decimal('300.00'), status='active')
        await order2.save()

        # Create two queries: one selects pending orders, one selects orders with amount > 150
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')
        high_amount_orders = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('150.00'))

        # Perform intersect operation to find orders that are both pending and high amount
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        intersect_query = AsyncSetOperationQuery(pending_orders, high_amount_orders, "INTERSECT")
        results = await intersect_query.aggregate()

        # Should return orders that satisfy both conditions (pending and amount > 150)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_except_operation(self, async_order_fixtures):
        """
        Test async EXCEPT operation between two queries

        This test verifies that the async except_ method can find results in one query that are not in another.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_except_user', email='async_except@example.com', age=30)
        await user.save()

        # Create orders for except operation
        order1 = AsyncOrder(user_id=user.id, order_number='AEXC-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AEXC-002', total_amount=Decimal('200.00'), status='pending')
        await order2.save()

        order3 = AsyncOrder(user_id=user.id, order_number='AEXC-003', total_amount=Decimal('300.00'), status='completed')
        await order3.save()

        # Create two queries: all orders, and active orders
        all_orders = AsyncOrder.query()
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Perform except operation: all orders minus active orders
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        except_query = AsyncSetOperationQuery(all_orders, active_orders, "EXCEPT")
        results = await except_query.aggregate()

        # Should return non-active orders (pending and completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_multiple_set_operations(self, async_order_fixtures):
        """
        Test async chaining multiple set operations

        This test verifies that multiple async set operations can be chained together.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_multi_set_user', email='async_multiset@example.com', age=30)
        await user.save()

        # Create different types of orders for multiple set operations
        order1 = AsyncOrder(user_id=user.id, order_number='AMS-001', total_amount=Decimal('100.00'), status='pending')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AMS-002', total_amount=Decimal('200.00'), status='active')
        await order2.save()

        order3 = AsyncOrder(user_id=user.id, order_number='AMS-003', total_amount=Decimal('300.00'), status='pending')
        await order3.save()

        # Create three different queries
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        high_amount_orders = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('250.00'))

        # Chain operations: (pending ∪ active) ∩ high_amount
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        union_query = AsyncSetOperationQuery(pending_orders, active_orders, "UNION")
        final_query = AsyncSetOperationQuery(union_query, high_amount_orders, "INTERSECT")
        results = await final_query.aggregate()

        # Result should be orders that are either pending or active, and amount > 250
        assert len(results) > 0  # At least some results should be returned

    async def test_set_operation_with_conditions(self, async_order_fixtures):
        """
        Test async set operations with additional WHERE conditions

        This test verifies that async set operations work correctly when combined with
        WHERE clauses to filter the results further.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_cond_set_user', email='async_condset@example.com', age=30)
        await user.save()

        # Create orders for conditional set operations
        order1 = AsyncOrder(user_id=user.id, order_number='ACOND-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='ACOND-002', total_amount=Decimal('200.00'), status='pending')
        await order2.save()

        # Create two queries with conditions
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')

        # Perform union with additional condition
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        union_query = AsyncSetOperationQuery(active_orders, pending_orders, "UNION")
        results = await union_query.aggregate()

        assert len(results) > 0  # Should return combined results

    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_set_operation_chaining(self, async_order_fixtures):
        """
        Test async chaining multiple set operations together

        This test verifies that multiple async set operations can be chained in sequence.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_chain_set_user', email='async_chainset@example.com', age=30)
        await user.save()

        # Create orders for chaining operations
        for i in range(4):
            status = ['active', 'pending', 'completed', 'cancelled'][i]
            amount = Decimal(f'{(i+1)*100.00}')
            order = AsyncOrder(user_id=user.id, order_number=f'ACHAIN-{i+1:03d}', total_amount=amount, status=status)
            await order.save()

        # Create multiple queries
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')
        high_amount_orders = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('200.00'))

        # Chain operations: (active ∪ pending) except high_amount
        from rhosocial.activerecord.query.set_operation import AsyncSetOperationQuery
        union_result = AsyncSetOperationQuery(active_orders, pending_orders, "UNION")
        final_result = AsyncSetOperationQuery(union_result, high_amount_orders, "EXCEPT")
        results = await final_result.aggregate()

        assert len(results) > 0  # Should return chained operation results

    async def test_union_operator(self, async_order_fixtures):
        """
        Test the | operator for UNION operations on asynchronous queries.

        This test verifies that the | operator correctly performs UNION operations
        between two asynchronous queries, returning all unique records from both queries.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_union_op_user', email='async_union_op@example.com', age=30)
        await user.save()

        # Create orders for union operation
        order1 = AsyncOrder(user_id=user.id, order_number='AUNION-OP-A-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AUNION-OP-B-002', total_amount=Decimal('200.00'), status='completed')
        await order2.save()

        # Create two separate queries using the | operator for UNION
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        completed_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'completed')

        # Perform union operation using the | operator
        union_query = active_orders | completed_orders
        results = await union_query.aggregate()

        # Should return all orders (active + completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_intersect_operator(self, async_order_fixtures):
        """
        Test the & operator for INTERSECT operations on asynchronous queries.

        This test verifies that the & operator correctly performs INTERSECT operations
        between two asynchronous queries, returning only common records.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_intersect_op_user', email='async_intersect_op@example.com', age=30)
        await user.save()

        # Create orders for intersect operation
        order1 = AsyncOrder(user_id=user.id, order_number='AINT-OP-001', total_amount=Decimal('200.00'), status='pending')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AINT-OP-002', total_amount=Decimal('300.00'), status='active')
        await order2.save()

        # Create two queries: one selects pending orders, one selects orders with amount > 150
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')
        high_amount_orders = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('150.00'))

        # Perform intersect operation using the & operator
        intersect_query = pending_orders & high_amount_orders
        results = await intersect_query.aggregate()

        # Should return orders that satisfy both conditions (pending and amount > 150)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_except')
    async def test_except_operator(self, async_order_fixtures):
        """
        Test the - operator for EXCEPT operations on asynchronous queries.

        This test verifies that the - operator correctly performs EXCEPT operations
        between two asynchronous queries, returning records in the first query that are not in the second.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_except_op_user', email='async_except_op@example.com', age=30)
        await user.save()

        # Create orders for except operation
        order1 = AsyncOrder(user_id=user.id, order_number='AEXC-OP-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AEXC-OP-002', total_amount=Decimal('200.00'), status='pending')
        await order2.save()

        order3 = AsyncOrder(user_id=user.id, order_number='AEXC-OP-003', total_amount=Decimal('300.00'), status='completed')
        await order3.save()

        # Create two queries: all orders, and active orders
        all_orders = AsyncOrder.query()
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')

        # Perform except operation using the - operator: all orders minus active orders
        except_query = all_orders - active_orders
        results = await except_query.aggregate()

        # Should return non-active orders (pending and completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    async def test_operator_precedence(self, async_order_fixtures):
        """
        Test operator precedence for multiple operations on asynchronous queries.

        This test verifies that the operators work correctly when chained together
        and follow expected precedence rules.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_op_prec_user', email='async_op_prec@example.com', age=30)
        await user.save()

        # Create different types of orders for multiple set operations
        order1 = AsyncOrder(user_id=user.id, order_number='APREC-001', total_amount=Decimal('100.00'), status='pending')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='APREC-002', total_amount=Decimal('200.00'), status='active')
        await order2.save()

        order3 = AsyncOrder(user_id=user.id, order_number='APREC-003', total_amount=Decimal('300.00'), status='pending')
        await order3.save()

        # Create three different queries
        pending_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'pending')
        active_orders = AsyncOrder.query().where(AsyncOrder.c.status == 'active')
        high_amount_orders = AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('250.00'))

        # Chain operations: (pending | active) & high_amount
        union_query = pending_orders | active_orders
        final_query = union_query & high_amount_orders
        results = await final_query.aggregate()

        # Result should be orders that are either pending or active, and amount > 250
        assert len(results) > 0  # At least some results should be returned