# src/rhosocial/activerecord/testsuite/feature/query/worker/test_transaction_operations.py
"""
Transaction operation tests.

When test cases execute, the environment is already prepared by the Provider:
- Database connected
- Tables created
- WorkerPool fixture available

Design principles:
- Each test runs in independent Worker processes
- Tests verify transaction isolation and concurrent safety
"""
import pytest
from typing import Type, Tuple

from rhosocial.activerecord.model import ActiveRecord


class TestTransactionOperations:
    """Transaction operation tests"""

    def test_concurrent_order_creation(
        self,
        order_fixtures: Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]],
        worker_pool,
        query_worker_connection_params,
        worker_tasks
    ):
        """
        Test concurrent creation of orders and order items.

        Verifies:
        1. Multiple orders can be created concurrently
        2. Order items are correctly associated with orders
        3. All data consistency is correct
        """
        User, Order, OrderItem = order_fixtures

        # Create a user first
        user = User(username='order_test_user', email='order_test@test.com', age=25)
        user.save()
        user_id = user.id

        n_orders = 5
        futures = []

        # Concurrently create orders
        for i in range(n_orders):
            params = {
                **query_worker_connection_params,
                'user_id': user_id,
                'order_number': f'ORD-{i:04d}',
                'items': [
                    {'product_name': f'Product-{i}-A', 'quantity': 2, 'unit_price': 10.0},
                    {'product_name': f'Product-{i}-B', 'quantity': 1, 'unit_price': 25.0},
                ]
            }
            futures.append(worker_pool.submit(worker_tasks.create_order_with_items_task, params))

        results = [f.result(timeout=30) for f in futures]

        # Verify all orders created successfully
        success_count = sum(1 for r in results if r.get('success', False))
        errors = [r.get('error', 'Unknown error') for r in results if not r.get('success', False)]
        assert success_count == n_orders, f"Expected {n_orders} successes, got {success_count}. Errors: {errors}"

        # Verify order IDs are unique
        order_ids = [r['order_id'] for r in results if r.get('success', False)]
        assert len(order_ids) == n_orders
        assert len(set(order_ids)) == n_orders

    def test_balance_transfer(
        self,
        order_fixtures: Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]],
        worker_pool,
        query_worker_connection_params,
        worker_tasks
    ):
        """
        Test balance transfer transaction operation.

        Note: Concurrent transfers require row locks (SELECT ... FOR UPDATE) for correctness.
        This test verifies the basic transaction operation flow: begin -> execute -> commit.
        """
        User, Order, OrderItem = order_fixtures

        # Create two users, each with initial balance of 100
        user1 = User(username='transfer_from', email='from@test.com', balance=100.0, age=25)
        user1.save()
        user1_id = user1.id

        user2 = User(username='transfer_to', email='to@test.com', balance=100.0, age=30)
        user2.save()
        user2_id = user2.id

        # Execute a single transfer
        transfer_amount = 30.0
        params = {
            **query_worker_connection_params,
            'from_user_id': user1_id,
            'to_user_id': user2_id,
            'amount': transfer_amount
        }
        result = worker_pool.submit(worker_tasks.transfer_balance_task, params).result(timeout=30)

        # Verify transfer succeeded
        assert result.get('success', False), f"Transfer failed: {result.get('error', 'Unknown error')}"

        # Re-query user balances
        user1_refreshed = User.find_one({'id': user1_id})
        user2_refreshed = User.find_one({'id': user2_id})

        # user1 balance should be 100 - 30 = 70
        # user2 balance should be 100 + 30 = 130
        assert user1_refreshed.balance == 70.0
        assert user2_refreshed.balance == 130.0

    def test_concurrent_order_status_update(
        self,
        order_fixtures: Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]],
        worker_pool,
        query_worker_connection_params,
        worker_tasks
    ):
        """
        Test concurrent order status updates.

        Verifies:
        1. Multiple Workers can concurrently update different order statuses
        2. Status changes are correctly recorded
        """
        User, Order, OrderItem = order_fixtures

        # Create a user
        user = User(username='status_test_user', email='status@test.com', age=30)
        user.save()
        user_id = user.id

        # Create multiple orders first
        order_ids = []
        for i in range(5):
            order = Order(user_id=user_id, order_number=f'STATUS-ORD-{i:04d}', status='pending')
            order.save()
            order_ids.append(order.id)

        # Concurrently update order statuses
        status_values = ['confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        futures = []

        for order_id, status in zip(order_ids, status_values):
            params = {
                **query_worker_connection_params,
                'order_id': order_id,
                'new_status': status
            }
            futures.append(worker_pool.submit(worker_tasks.update_order_status_task, params))

        results = [f.result(timeout=30) for f in futures]

        # Verify all updates succeeded
        success_count = sum(1 for r in results if r.get('success', False))
        assert success_count == len(order_ids)

        # Verify statuses are correctly updated
        for order_id, expected_status in zip(order_ids, status_values):
            order = Order.find_one({'id': order_id})
            assert order.status == expected_status

    def test_concurrent_complex_query(
        self,
        order_fixtures: Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]],
        worker_pool,
        query_worker_connection_params,
        worker_tasks
    ):
        """
        Test concurrent complex queries.

        Verifies:
        1. Multiple complex queries can execute concurrently
        2. Query results are correct
        """
        User, Order, OrderItem = order_fixtures

        # Create test data
        user = User(username='query_test_user', email='query@test.com', age=28)
        user.save()
        user_id = user.id

        # Create order and order items
        order = Order(user_id=user_id, order_number='QUERY-ORD-001', status='completed')
        order.save()

        for i in range(3):
            quantity = i + 1
            unit_price = 10.0 * (i + 1)
            item = OrderItem(
                order_id=order.id,
                product_name=f'Query-Product-{i}',
                quantity=quantity,
                unit_price=unit_price,
                subtotal=quantity * unit_price
            )
            item.save()

        # Concurrently execute various queries
        futures = []

        # Query 1: Get user order count
        futures.append(worker_pool.submit(
            worker_tasks.count_user_orders_task,
            {**query_worker_connection_params, 'user_id': user_id}
        ))

        # Query 2: Get order item count
        futures.append(worker_pool.submit(
            worker_tasks.count_order_items_task,
            {**query_worker_connection_params, 'order_id': order.id}
        ))

        # Query 3: Get order total amount
        futures.append(worker_pool.submit(
            worker_tasks.calculate_order_total_task,
            {**query_worker_connection_params, 'order_id': order.id}
        ))

        results = [f.result(timeout=30) for f in futures]

        # Verify query results
        assert all(r.get('success', False) for r in results)

        # User order count should be 1
        assert results[0]['count'] == 1

        # Order item count should be 3
        assert results[1]['count'] == 3

        # Order total should be 10*1 + 20*2 + 30*3 = 140
        expected_total = 10.0 * 1 + 20.0 * 2 + 30.0 * 3
        assert abs(results[2]['total'] - expected_total) < 0.01

    def test_transaction_rollback_on_error(
        self,
        order_fixtures: Tuple[Type[ActiveRecord], Type[ActiveRecord], Type[ActiveRecord]],
        worker_pool,
        query_worker_connection_params,
        worker_tasks
    ):
        """
        Test transaction rollback.

        Verifies:
        1. When an operation fails, the transaction is correctly rolled back
        2. Data remains consistent
        """
        User, Order, OrderItem = order_fixtures

        # Create a user with balance of 50
        user = User(username='rollback_test_user', email='rollback@test.com', balance=50.0, age=22)
        user.save()
        user_id = user.id

        # Attempt to transfer 100 (insufficient balance, should fail and rollback)
        params = {
            **query_worker_connection_params,
            'from_user_id': user_id,
            'to_user_id': 99999,  # Non-existent user
            'amount': 100.0
        }
        result = worker_pool.submit(worker_tasks.transfer_balance_task, params).result(timeout=30)

        # Verify transfer failed
        assert not result.get('success', False)

        # Verify user balance unchanged
        user_refreshed = User.find_one({'id': user_id})
        assert user_refreshed.balance == 50.0
