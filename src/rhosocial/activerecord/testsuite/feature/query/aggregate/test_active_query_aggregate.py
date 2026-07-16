# src/rhosocial/activerecord/testsuite/feature/query/aggregate/test_active_query_aggregate.py
"""ActiveQuery aggregate functionality tests

This module contains tests for the aggregate ActiveQuery operations including:
- Simple aggregation functions (count, sum, avg, min, max)
- Aggregation with conditions (where, group by, having)
- Existence checking functionality
"""

import pytest
from decimal import Decimal
class TestSyncActiveQueryAggregate:
    """
    Synchronous ActiveQuery aggregate functionality tests
    """

    def test_count_simple(self, order_fixtures):
        """
        Test simple count aggregation

        This test verifies that the count() method correctly counts all records
        in the result set. Count is a fundamental aggregation function used
        for getting the total number of records matching query conditions.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Create 3 orders for counting
        for i in range(3):
            Order(user_id=user.id, order_number=f'CNT-{i+1:03d}').save()

        # Count all orders for this user
        count = Order.query().count()
        assert count == 3

    def test_count_with_column(self, order_fixtures):
        """
        Test count with specific column

        This test verifies that the count() method can count specific columns
        rather than all records. This is useful when counting non-null values
        in particular fields.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Create 3 orders with specific column values
        for i in range(3):
            Order(
                user_id=user.id,
                order_number=f'COL-{i+1:03d}',
                total_amount=Decimal(f'{(i+1)*100.00}')
            ).save()

        # Count specific column values
        count = Order.query().count(Order.c.order_number)
        assert count == 3

    def test_count_distinct(self, order_fixtures):
        """
        Test distinct count aggregation

        This test verifies that the count() method can count unique values
        when the is_distinct parameter is True. This is important for
        eliminating duplicates in counting operations.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Create multiple orders with same status to test distinct counting
        for i in range(3):
            Order(
                user_id=user.id,
                order_number=f'DIST-{i+1:03d}',
                status='pending'
            ).save()

        # Add one order with different status
        Order(
            user_id=user.id,
            order_number='DIST-004',
            status='completed'
        ).save()

        # Count distinct status values
        distinct_status_count = Order.query().count(Order.c.status, is_distinct=True)
        assert distinct_status_count == 2  # 'pending' and 'completed'

    def test_sum_simple(self, order_fixtures):
        """
        Test simple sum aggregation

        This test verifies that the sum_() method correctly calculates the
        total sum of values in a numeric column. Sum is commonly used for
        financial calculations and totals.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Define amounts to sum
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'SUM-{i+1:03d}',
                total_amount=amount
            ).save()

        # Calculate total sum of amounts
        total = Order.query().sum_(Order.c.total_amount)
        assert total == sum(amounts)

    def test_sum_with_column(self, order_fixtures):
        """
        Test sum with specific column

        This test verifies that the sum_() method can calculate the sum
        for a specific column. This ensures the method works correctly
        with different column types and names.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Define amounts to sum
        amounts = [Decimal('50.00'), Decimal('150.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'COL-{i+1:03d}',
                total_amount=amount
            ).save()

        # Calculate sum for specific column
        total = Order.query().sum_(Order.c.total_amount)
        assert total == sum(amounts)

    def test_avg_simple(self, order_fixtures):
        """
        Test simple average calculation

        This test verifies that the avg() method correctly calculates the
        arithmetic mean of values in a numeric column. Average is useful
        for statistical analysis and reporting.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Define amounts for average calculation
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'AVG-{i+1:03d}',
                total_amount=amount
            ).save()

        # Calculate average of amounts
        avg = Order.query().avg(Order.c.total_amount)
        expected_avg = sum(amounts) / len(amounts)
        assert avg == expected_avg

    def test_min_max_simple(self, order_fixtures):
        """
        Test minimum and maximum value functions

        This test verifies that the min_() and max_() methods correctly
        identify the smallest and largest values in a numeric column.
        These functions are essential for finding extremes in datasets.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Define amounts with known min/max values
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('50.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'MINMAX-{i+1:03d}',
                total_amount=amount
            ).save()

        # Find minimum and maximum values
        min_val = Order.query().min_(Order.c.total_amount)
        max_val = Order.query().max_(Order.c.total_amount)

        assert min_val == min(amounts)
        assert max_val == max(amounts)

    def test_exists_method(self, order_fixtures):
        """
        Test exists method for checking record existence

        This test verifies that the exists() method efficiently checks whether
        records matching the query conditions exist in the database without
        retrieving the actual data. This is more efficient than using count()
        when only existence matters.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        order = Order(user_id=user.id, order_number='EXIST-001', total_amount=Decimal('100.00'))
        order.save()

        # Test existence case - record should exist
        exists = Order.query().where(Order.c.order_number == 'EXIST-001').exists()
        assert exists is True

        # Test non-existence case - record should not exist
        exists = Order.query().where(Order.c.order_number == 'NON-EXISTENT').exists()
        assert exists is False

    def test_aggregate_with_where_condition(self, order_fixtures):
        """
        Test aggregation with WHERE conditions

        This test verifies that aggregation functions work correctly
        when combined with WHERE clauses to filter the dataset before
        performing calculations.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        # Define test data with different statuses
        orders_data = [
            {'number': 'COND-001', 'amount': Decimal('100.00'), 'status': 'active'},
            {'number': 'COND-002', 'amount': Decimal('200.00'), 'status': 'active'},
            {'number': 'COND-003', 'amount': Decimal('300.00'), 'status': 'inactive'}
        ]

        for data in orders_data:
            Order(
                user_id=user.id,
                order_number=data['number'],
                total_amount=data['amount'],
                status=data['status']
            ).save()

        # Perform aggregation only on active orders
        active_count = Order.query().where(Order.c.status == 'active').count()
        active_total = Order.query().where(Order.c.status == 'active').sum_(Order.c.total_amount)

        active_orders = [d for d in orders_data if d['status'] == 'active']
        assert active_count == len(active_orders)
        assert active_total == sum(d['amount'] for d in active_orders)

    def test_count_wildcard_string(self, order_fixtures):
        """
        Test count with wildcard string '*' as column argument.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'WLD-{i+1:03d}').save()

        count = Order.query().count("*")
        assert count == 3

    def test_sum_wildcard_raises_error(self, order_fixtures):
        """
        Test sum_ with wildcard string '*' raises ValueError.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'SUM-{i+1:03d}').save()

        with pytest.raises(ValueError, match="SUM\\(\\*\\)"):
            Order.query().sum_("*")

    def test_avg_wildcard_raises_error(self, order_fixtures):
        """
        Test avg with wildcard string '*' raises ValueError.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'AVG-{i+1:03d}').save()

        with pytest.raises(ValueError, match="AVG\\(\\*\\)"):
            Order.query().avg("*")

    def test_min_wildcard_raises_error(self, order_fixtures):
        """
        Test min_ with wildcard string '*' raises ValueError.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'MIN-{i+1:03d}').save()

        with pytest.raises(ValueError, match="MIN\\(\\*\\)"):
            Order.query().min_("*")

    def test_max_wildcard_raises_error(self, order_fixtures):
        """
        Test max_ with wildcard string '*' raises ValueError.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'MAX-{i+1:03d}').save()

        with pytest.raises(ValueError, match="MAX\\(\\*\\)"):
            Order.query().max_("*")