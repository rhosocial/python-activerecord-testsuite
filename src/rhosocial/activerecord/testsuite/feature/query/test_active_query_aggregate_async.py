# src/rhosocial/activerecord/testsuite/feature/query/test_active_query_aggregate_async.py
"""ActiveQuery aggregate functionality tests

This module contains tests for the aggregate ActiveQuery operations including:
- Simple aggregation functions (count, sum, avg, min, max)
- Aggregation with conditions (where, group by, having)
- Existence checking functionality
"""

import pytest
from decimal import Decimal
class TestAsyncActiveQueryAggregate:
    """
    Asynchronous ActiveQuery aggregate functionality tests
    """

    async def test_count_simple(self, async_order_fixtures):
        """
        Test simple count aggregation with async

        This test verifies that the async count() method correctly counts all records
        in the result set. Count is a fundamental aggregation function used
        for getting the total number of records matching query conditions.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Create 3 orders for counting
        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'CNT-{i+1:03d}')
            await order.save()

        # Count all orders for this user
        count = await AsyncOrder.query().count()
        assert count == 3

    async def test_count_with_column(self, async_order_fixtures):
        """
        Test count with specific column with async

        This test verifies that the async count() method can count specific columns
        rather than all records. This is useful when counting non-null values
        in particular fields.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Create 3 orders with specific column values
        for i in range(3):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'COL-{i+1:03d}',
                total_amount=Decimal(f'{(i+1)*100.00}')
            )
            await order.save()

        # Count specific column values
        count = await AsyncOrder.query().count(AsyncOrder.c.order_number)
        assert count == 3

    async def test_count_distinct(self, async_order_fixtures):
        """
        Test distinct count aggregation with async

        This test verifies that the async count() method can count unique values
        when the is_distinct parameter is True. This is important for
        eliminating duplicates in counting operations.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Create multiple orders with same status to test distinct counting
        for i in range(3):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'DIST-{i+1:03d}',
                status='pending'
            )
            await order.save()

        # Add one order with different status
        order = AsyncOrder(
            user_id=user.id,
            order_number='DIST-004',
            status='completed'
        )
        await order.save()

        # Count distinct status values
        distinct_status_count = await AsyncOrder.query().count(AsyncOrder.c.status, is_distinct=True)
        assert distinct_status_count == 2  # 'pending' and 'completed'

    async def test_sum_simple(self, async_order_fixtures):
        """
        Test simple sum aggregation with async

        This test verifies that the async sum_() method correctly calculates the
        total sum of values in a numeric column. Sum is commonly used for
        financial calculations and totals.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Define amounts to sum
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'SUM-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Calculate total sum of amounts
        total = await AsyncOrder.query().sum_(AsyncOrder.c.total_amount)
        assert total == sum(amounts)

    async def test_sum_with_column(self, async_order_fixtures):
        """
        Test sum with specific column with async

        This test verifies that the async sum_() method can calculate the sum
        for a specific column. This ensures the method works correctly
        with different column types and names.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Define amounts to sum
        amounts = [Decimal('50.00'), Decimal('150.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'COL-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Calculate sum for specific column
        total = await AsyncOrder.query().sum_(AsyncOrder.c.total_amount)
        assert total == sum(amounts)

    async def test_avg_simple(self, async_order_fixtures):
        """
        Test simple average calculation with async

        This test verifies that the async avg() method correctly calculates the
        arithmetic mean of values in a numeric column. Average is useful
        for statistical analysis and reporting.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Define amounts for average calculation
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AVG-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Calculate average of amounts
        avg = await AsyncOrder.query().avg(AsyncOrder.c.total_amount)
        expected_avg = sum(amounts) / len(amounts)
        assert avg == expected_avg

    async def test_min_max_simple(self, async_order_fixtures):
        """
        Test minimum and maximum value functions with async

        This test verifies that the async min_() and max_() methods correctly
        identify the smallest and largest values in a numeric column.
        These functions are essential for finding extremes in datasets.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Define amounts with known min/max values
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('50.00'), Decimal('300.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'MINMAX-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Find minimum and maximum values
        min_val = await AsyncOrder.query().min_(AsyncOrder.c.total_amount)
        max_val = await AsyncOrder.query().max_(AsyncOrder.c.total_amount)

        assert min_val == min(amounts)
        assert max_val == max(amounts)

    async def test_exists_method(self, async_order_fixtures):
        """
        Test async exists method for checking record existence

        This test verifies that the async exists() method efficiently checks whether
        records matching the query conditions exist in the database without
        retrieving the actual data. This is more efficient than using count()
        when only existence matters.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='EXIST-001', total_amount=Decimal('100.00'))
        await order.save()

        # Test existence case - record should exist
        exists = await AsyncOrder.query().where(AsyncOrder.c.order_number == 'EXIST-001').exists()
        assert exists is True

        # Test non-existence case - record should not exist
        exists = await AsyncOrder.query().where(AsyncOrder.c.order_number == 'NON-EXISTENT').exists()
        assert exists is False

    async def test_aggregate_with_where_condition(self, async_order_fixtures):
        """
        Test aggregation with WHERE conditions with async

        This test verifies that async aggregation functions work correctly
        when combined with WHERE clauses to filter the dataset before
        performing calculations.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Define test data with different statuses
        orders_data = [
            {'number': 'COND-001', 'amount': Decimal('100.00'), 'status': 'active'},
            {'number': 'COND-002', 'amount': Decimal('200.00'), 'status': 'active'},
            {'number': 'COND-003', 'amount': Decimal('300.00'), 'status': 'inactive'}
        ]

        for data in orders_data:
            order = AsyncOrder(
                user_id=user.id,
                order_number=data['number'],
                total_amount=data['amount'],
                status=data['status']
            )
            await order.save()

        # Perform aggregation only on active orders
        active_count = await AsyncOrder.query().where(AsyncOrder.c.status == 'active').count()
        active_total = await AsyncOrder.query().where(AsyncOrder.c.status == 'active').sum_(AsyncOrder.c.total_amount)

        active_orders = [d for d in orders_data if d['status'] == 'active']
        assert active_count == len(active_orders)
        assert active_total == sum(d['amount'] for d in active_orders)

    async def test_count_wildcard_string(self, async_order_fixtures):
        """
        Test async count with wildcard string '*' as column argument.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'AWLD-{i+1:03d}')
            await order.save()

        count = await AsyncOrder.query().count("*")
        assert count == 3

    async def test_sum_wildcard_raises_error(self, async_order_fixtures):
        """
        Test async sum_ with wildcard string '*' raises ValueError.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'ASUM-{i+1:03d}')
            await order.save()

        with pytest.raises(ValueError, match="SUM\\(\\*\\)"):
            await AsyncOrder.query().sum_("*")

    async def test_avg_wildcard_raises_error(self, async_order_fixtures):
        """
        Test async avg with wildcard string '*' raises ValueError.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'AAVG-{i+1:03d}')
            await order.save()

        with pytest.raises(ValueError, match="AVG\\(\\*\\)"):
            await AsyncOrder.query().avg("*")

    async def test_min_wildcard_raises_error(self, async_order_fixtures):
        """
        Test async min_ with wildcard string '*' raises ValueError.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'AMIN-{i+1:03d}')
            await order.save()

        with pytest.raises(ValueError, match="MIN\\(\\*\\)"):
            await AsyncOrder.query().min_("*")

    async def test_max_wildcard_raises_error(self, async_order_fixtures):
        """
        Test async max_ with wildcard string '*' raises ValueError.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'AMAX-{i+1:03d}')
            await order.save()

        with pytest.raises(ValueError, match="MAX\\(\\*\\)"):
            await AsyncOrder.query().max_("*")