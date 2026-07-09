# src/rhosocial/activerecord/testsuite/feature/query/test_aggregate_queries_async.py
"""Aggregate query tests"""
from decimal import Decimal


async def test_count_simple(async_order_fixtures):
    """
    Test simple count aggregation

    This test verifies that the count() method correctly counts all records
    in the result set. Count is a fundamental aggregation function used
    for getting the total number of records matching query conditions.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Create 3 orders for counting
    for i in range(3):
        await AsyncOrder(user_id=user.id, order_number=f'CNT-{i+1:03d}').save()

    # Count all orders for this user
    count = await AsyncOrder.query().count()
    assert count == 3


async def test_count_with_column(async_order_fixtures):
    """
    Test count with specific column

    This test verifies that the count() method can count specific columns
    rather than all records. This is useful when counting non-null values
    in particular fields.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Create 3 orders with specific column values
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'COL-{i+1:03d}',
            total_amount=Decimal(f'{(i+1)*100.00}')
        ).save()

    # Count specific column values
    count = await AsyncOrder.query().count(AsyncOrder.c.order_number)
    assert count == 3


async def test_count_distinct(async_order_fixtures):
    """
    Test distinct count aggregation

    This test verifies that the count() method can count unique values
    when the is_distinct parameter is True. This is important for
    eliminating duplicates in counting operations.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Create multiple orders with same status to test distinct counting
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'DIST-{i+1:03d}',
            status='pending'
        ).save()

    # Add one order with different status
    await AsyncOrder(
        user_id=user.id,
        order_number='DIST-004',
        status='completed'
    ).save()

    # Count distinct status values
    distinct_status_count = await AsyncOrder.query().count(AsyncOrder.c.status, is_distinct=True)
    assert distinct_status_count == 2  # 'pending' and 'completed'


async def test_sum_simple(async_order_fixtures):
    """
    Test simple sum aggregation

    This test verifies that the sum_() method correctly calculates the
    total sum of values in a numeric column. Sum is commonly used for
    financial calculations and totals.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define amounts to sum
    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'SUM-{i+1:03d}',
            total_amount=amount
        ).save()

    # Calculate total sum of amounts
    total = await AsyncOrder.query().sum_(AsyncOrder.c.total_amount)
    assert total == sum(amounts)


async def test_sum_with_column(async_order_fixtures):
    """
    Test sum with specific column

    This test verifies that the sum_() method can calculate the sum
    for a specific column. This ensures the method works correctly
    with different column types and names.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define amounts to sum
    amounts = [Decimal('50.00'), Decimal('150.00'), Decimal('250.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'COL-{i+1:03d}',
            total_amount=amount
        ).save()

    # Calculate sum for specific column
    total = await AsyncOrder.query().sum_(AsyncOrder.c.total_amount)
    assert total == sum(amounts)


async def test_avg_simple(async_order_fixtures):
    """
    Test simple average calculation

    This test verifies that the avg() method correctly calculates the
    arithmetic mean of values in a numeric column. Average is useful
    for statistical analysis and reporting.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define amounts for average calculation
    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'AVG-{i+1:03d}',
            total_amount=amount
        ).save()

    # Calculate average of amounts
    avg = await AsyncOrder.query().avg(AsyncOrder.c.total_amount)
    expected_avg = sum(amounts) / len(amounts)
    assert avg == expected_avg


async def test_min_max_simple(async_order_fixtures):
    """
    Test minimum and maximum value functions

    This test verifies that the min_() and max_() methods correctly
    identify the smallest and largest values in a numeric column.
    These functions are essential for finding extremes in datasets.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define amounts with known min/max values
    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('50.00'), Decimal('300.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'MINMAX-{i+1:03d}',
            total_amount=amount
        ).save()

    # Find minimum and maximum values
    min_val = await AsyncOrder.query().min_(AsyncOrder.c.total_amount)
    max_val = await AsyncOrder.query().max_(AsyncOrder.c.total_amount)
    
    assert min_val == min(amounts)
    assert max_val == max(amounts)


async def test_aggregate_complex(async_order_fixtures):
    """
    Test complex aggregation operations with multiple functions

    This test verifies that the aggregate() method can handle multiple
    aggregation functions simultaneously, returning structured results
    with calculated values for each function.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Create orders with alternating statuses for complex aggregation
    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'AGG-{i+1:03d}',
            total_amount=amount,
            status='active' if i % 2 == 0 else 'inactive'
        ).save()

    # Get backend to access dialect for function calls
    backend = AsyncOrder.backend()
    dialect = backend.dialect
    
    # Import functions module for aggregation
    from rhosocial.activerecord.backend.expression import functions
    
    # Perform complex aggregation with multiple functions
    results = await AsyncOrder.query().select(
        functions.sum_(dialect, AsyncOrder.c.total_amount).as_('total'),
        functions.avg(dialect, AsyncOrder.c.total_amount).as_('average'),
        functions.count(dialect, '*').as_('count')
    ).aggregate()

    assert len(results) == 1
    assert results[0]['total'] == sum(amounts)
    assert results[0]['average'] == sum(amounts) / len(amounts)
    assert results[0]['count'] == len(amounts)


async def test_aggregate_multiple_fields(async_order_fixtures):
    """
    Test aggregation with multiple fields in single query

    This test verifies that a single aggregate query can calculate
    multiple metrics simultaneously, improving efficiency by reducing
    the number of database round trips.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define test data with different statuses
    orders_data = [
        {'number': 'MULT-001', 'amount': Decimal('100.00'), 'status': 'active'},
        {'number': 'MULT-002', 'amount': Decimal('200.00'), 'status': 'active'},
        {'number': 'MULT-003', 'amount': Decimal('300.00'), 'status': 'inactive'}
    ]

    for data in orders_data:
        await AsyncOrder(
            user_id=user.id,
            order_number=data['number'],
            total_amount=data['amount'],
            status=data['status']
        ).save()

    # Get backend to access dialect for function calls
    backend = AsyncOrder.backend()
    dialect = backend.dialect
    
    # Import functions module for aggregation
    from rhosocial.activerecord.backend.expression import functions
    
    # Perform multi-field aggregation
    results = await AsyncOrder.query().select(
        functions.count(dialect, '*').as_('total_orders'),
        functions.sum_(dialect, AsyncOrder.c.total_amount).as_('total_amount'),
        functions.avg(dialect, AsyncOrder.c.total_amount).as_('avg_amount')
    ).aggregate()

    assert len(results) == 1
    assert results[0]['total_orders'] == len(orders_data)
    assert results[0]['total_amount'] == sum(d['amount'] for d in orders_data)
    assert results[0]['avg_amount'] == sum(d['amount'] for d in orders_data) / len(orders_data)


async def test_aggregate_with_conditions(async_order_fixtures):
    """
    Test aggregation with conditional filtering

    This test verifies that aggregation functions work correctly
    when combined with WHERE clauses to filter the dataset before
    performing calculations.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='test_user', email='test@example.com', age=30)
    await user.save()

    # Define test data with different statuses
    orders_data = [
        {'number': 'COND-001', 'amount': Decimal('100.00'), 'status': 'active'},
        {'number': 'COND-002', 'amount': Decimal('200.00'), 'status': 'active'},
        {'number': 'COND-003', 'amount': Decimal('300.00'), 'status': 'inactive'}
    ]

    for data in orders_data:
        await AsyncOrder(
            user_id=user.id,
            order_number=data['number'],
            total_amount=data['amount'],
            status=data['status']
        ).save()

    # Get backend to access dialect for function calls
    backend = AsyncOrder.backend()
    dialect = backend.dialect
    
    # Import functions module for aggregation
    from rhosocial.activerecord.backend.expression import functions
    
    # Perform aggregation only on active orders
    results = await AsyncOrder.query().where(AsyncOrder.c.status == 'active').select(
        functions.count(dialect, '*').as_('active_count'),
        functions.sum_(dialect, AsyncOrder.c.total_amount).as_('active_total')
    ).aggregate()

    active_orders = [d for d in orders_data if d['status'] == 'active']
    assert len(results) == 1
    assert results[0]['active_count'] == len(active_orders)
    assert results[0]['active_total'] == sum(d['amount'] for d in active_orders)