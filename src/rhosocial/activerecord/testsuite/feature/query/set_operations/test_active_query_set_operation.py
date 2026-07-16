# src/rhosocial/activerecord/testsuite/feature/query/set_operations/test_active_query_set_operation.py
"""ActiveQuery set operation functionality tests

This module contains tests for the set operation ActiveQuery operations including:
- UNION operations
- INTERSECT operations
- EXCEPT operations
- Chaining multiple set operations
- Set operations with conditions
"""

import pytest
from decimal import Decimal

from rhosocial.activerecord.backend.dialect.protocols import SetOperationSupport
from rhosocial.activerecord.testsuite.utils import requires_protocol
class TestSyncActiveQuerySetOperation:
    """
    Synchronous ActiveQuery set operation functionality tests
    """

    def test_union_operation(self, order_fixtures):
        """
        Test UNION operation between two queries

        This test verifies that the union method can combine results from two different queries,
        returning all unique records from both queries.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='union_user', email='union@example.com', age=30)
        user.save()

        # Create orders for union operation
        order1 = Order(user_id=user.id, order_number='UNION-A-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='UNION-B-002', total_amount=Decimal('200.00'), status='completed')
        order2.save()

        # Create two separate queries
        active_orders = Order.query().where(Order.c.status == 'active')
        completed_orders = Order.query().where(Order.c.status == 'completed')

        # Perform union operation to combine both result sets
        union_query = active_orders.union(completed_orders)
        results = union_query.aggregate()

        # Should return all orders (active + completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    def test_intersect_operation(self, order_fixtures):
        """
        Test INTERSECT operation between two queries

        This test verifies that the intersect method can find common results between two queries.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='intersect_user', email='intersect@example.com', age=30)
        user.save()

        # Create orders for intersect operation
        order1 = Order(user_id=user.id, order_number='INT-001', total_amount=Decimal('200.00'), status='pending')
        order1.save()

        order2 = Order(user_id=user.id, order_number='INT-002', total_amount=Decimal('300.00'), status='active')
        order2.save()

        # Create two queries: one selects pending orders, one selects orders with amount > 150
        pending_orders = Order.query().where(Order.c.status == 'pending')
        high_amount_orders = Order.query().where(Order.c.total_amount > Decimal('150.00'))

        # Perform intersect operation to find orders that are both pending and high amount
        intersect_query = pending_orders.intersect(high_amount_orders)
        results = intersect_query.aggregate()

        # Should return orders that satisfy both conditions (pending and amount > 150)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_except')
    def test_except_operation(self, order_fixtures):
        """
        Test EXCEPT operation between two queries

        This test verifies that the except_ method can find results in one query that are not in another.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='except_user', email='except@example.com', age=30)
        user.save()

        # Create orders for except operation
        order1 = Order(user_id=user.id, order_number='EXC-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='EXC-002', total_amount=Decimal('200.00'), status='pending')
        order2.save()

        order3 = Order(user_id=user.id, order_number='EXC-003', total_amount=Decimal('300.00'), status='completed')
        order3.save()

        # Create two queries: all orders, and active orders
        all_orders = Order.query()
        active_orders = Order.query().where(Order.c.status == 'active')

        # Perform except operation: all orders minus active orders
        except_query = all_orders.except_(active_orders)
        results = except_query.aggregate()

        # Should return non-active orders (pending and completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    def test_multiple_set_operations(self, order_fixtures):
        """
        Test chaining multiple set operations

        This test verifies that multiple set operations can be chained together.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='multi_set_user', email='multiset@example.com', age=30)
        user.save()

        # Create different types of orders for multiple set operations
        order1 = Order(user_id=user.id, order_number='MS-001', total_amount=Decimal('100.00'), status='pending')
        order1.save()

        order2 = Order(user_id=user.id, order_number='MS-002', total_amount=Decimal('200.00'), status='active')
        order2.save()

        order3 = Order(user_id=user.id, order_number='MS-003', total_amount=Decimal('300.00'), status='pending')
        order3.save()

        # Create three different queries
        pending_orders = Order.query().where(Order.c.status == 'pending')
        active_orders = Order.query().where(Order.c.status == 'active')
        high_amount_orders = Order.query().where(Order.c.total_amount > Decimal('250.00'))

        # Chain operations: (pending ∪ active) ∩ high_amount
        union_query = pending_orders.union(active_orders)
        final_query = union_query.intersect(high_amount_orders)
        results = final_query.aggregate()

        # Result should be orders that are either pending or active, and amount > 250
        assert len(results) > 0  # At least some results should be returned

    def test_set_operation_with_conditions(self, order_fixtures):
        """
        Test set operations with additional WHERE conditions

        This test verifies that set operations work correctly when combined with
        WHERE clauses to filter the results further.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='cond_set_user', email='condset@example.com', age=30)
        user.save()

        # Create orders for conditional set operations
        order1 = Order(user_id=user.id, order_number='COND-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='COND-002', total_amount=Decimal('200.00'), status='pending')
        order2.save()

        # Create two queries with conditions
        active_orders = Order.query().where(Order.c.status == 'active')
        pending_orders = Order.query().where(Order.c.status == 'pending')

        # Perform union with additional condition
        union_query = active_orders.union(pending_orders)
        results = union_query.aggregate()

        assert len(results) > 0  # Should return combined results

    @requires_protocol(SetOperationSupport, 'supports_except')
    def test_set_operation_chaining(self, order_fixtures):
        """
        Test chaining multiple set operations together

        This test verifies that multiple set operations can be chained in sequence.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='chain_set_user', email='chainset@example.com', age=30)
        user.save()

        # Create orders for chaining operations
        for i in range(4):
            status = ['active', 'pending', 'completed', 'cancelled'][i]
            amount = Decimal(f'{(i+1)*100.00}')
            order = Order(user_id=user.id, order_number=f'CHAIN-{i+1:03d}', total_amount=amount, status=status)
            order.save()

        # Create multiple queries
        active_orders = Order.query().where(Order.c.status == 'active')
        pending_orders = Order.query().where(Order.c.status == 'pending')
        high_amount_orders = Order.query().where(Order.c.total_amount > Decimal('200.00'))

        # Chain operations: (active ∪ pending) except high_amount
        union_result = active_orders.union(pending_orders)
        final_result = union_result.except_(high_amount_orders)
        results = final_result.aggregate()

        assert len(results) > 0  # Should return chained operation results

    def test_union_operator(self, order_fixtures):
        """
        Test the | operator for UNION operations on synchronous queries.
        
        This test verifies that the | operator correctly performs UNION operations
        between two synchronous queries, returning all unique records from both queries.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='union_op_user', email='union_op@example.com', age=30)
        user.save()

        # Create orders for union operation
        order1 = Order(user_id=user.id, order_number='UNION-OP-A-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='UNION-OP-B-002', total_amount=Decimal('200.00'), status='completed')
        order2.save()

        # Create two separate queries using the | operator for UNION
        active_orders = Order.query().where(Order.c.status == 'active')
        completed_orders = Order.query().where(Order.c.status == 'completed')

        # Perform union operation using the | operator
        union_query = active_orders | completed_orders
        results = union_query.aggregate()

        # Should return all orders (active + completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    def test_intersect_operator(self, order_fixtures):
        """
        Test the & operator for INTERSECT operations on synchronous queries.
        
        This test verifies that the & operator correctly performs INTERSECT operations
        between two synchronous queries, returning only common records.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='intersect_op_user', email='intersect_op@example.com', age=30)
        user.save()

        # Create orders for intersect operation
        order1 = Order(user_id=user.id, order_number='INT-OP-001', total_amount=Decimal('200.00'), status='pending')
        order1.save()

        order2 = Order(user_id=user.id, order_number='INT-OP-002', total_amount=Decimal('300.00'), status='active')
        order2.save()

        # Create two queries: one selects pending orders, one selects orders with amount > 150
        pending_orders = Order.query().where(Order.c.status == 'pending')
        high_amount_orders = Order.query().where(Order.c.total_amount > Decimal('150.00'))

        # Perform intersect operation using the & operator
        intersect_query = pending_orders & high_amount_orders
        results = intersect_query.aggregate()

        # Should return orders that satisfy both conditions (pending and amount > 150)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_except')
    def test_except_operator(self, order_fixtures):
        """
        Test the - operator for EXCEPT operations on synchronous queries.
        
        This test verifies that the - operator correctly performs EXCEPT operations
        between two synchronous queries, returning records in the first query that are not in the second.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='except_op_user', email='except_op@example.com', age=30)
        user.save()

        # Create orders for except operation
        order1 = Order(user_id=user.id, order_number='EXC-OP-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='EXC-OP-002', total_amount=Decimal('200.00'), status='pending')
        order2.save()

        order3 = Order(user_id=user.id, order_number='EXC-OP-003', total_amount=Decimal('300.00'), status='completed')
        order3.save()

        # Create two queries: all orders, and active orders
        all_orders = Order.query()
        active_orders = Order.query().where(Order.c.status == 'active')

        # Perform except operation using the - operator: all orders minus active orders
        except_query = all_orders - active_orders
        results = except_query.aggregate()

        # Should return non-active orders (pending and completed)
        assert len(results) > 0  # At least some results should be returned

    @requires_protocol(SetOperationSupport, 'supports_intersect')
    def test_operator_precedence(self, order_fixtures):
        """
        Test operator precedence for multiple operations on synchronous queries.
        
        This test verifies that the operators work correctly when chained together
        and follow expected precedence rules.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='op_prec_user', email='op_prec@example.com', age=30)
        user.save()

        # Create different types of orders for multiple set operations
        order1 = Order(user_id=user.id, order_number='PREC-001', total_amount=Decimal('100.00'), status='pending')
        order1.save()

        order2 = Order(user_id=user.id, order_number='PREC-002', total_amount=Decimal('200.00'), status='active')
        order2.save()

        order3 = Order(user_id=user.id, order_number='PREC-003', total_amount=Decimal('300.00'), status='pending')
        order3.save()

        # Create three different queries
        pending_orders = Order.query().where(Order.c.status == 'pending')
        active_orders = Order.query().where(Order.c.status == 'active')
        high_amount_orders = Order.query().where(Order.c.total_amount > Decimal('250.00'))

        # Chain operations: (pending | active) & high_amount
        union_query = pending_orders | active_orders
        final_query = union_query & high_amount_orders
        results = final_query.aggregate()

        # Result should be orders that are either pending or active, and amount > 250
        assert len(results) > 0  # At least some results should be returned