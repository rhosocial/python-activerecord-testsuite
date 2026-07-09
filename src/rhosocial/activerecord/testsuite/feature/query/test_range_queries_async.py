# src/rhosocial/activerecord/testsuite/feature/query/test_range_queries_async.py
"""
Range query tests

This module contains tests for SQL range operations including:
- IN list operations
- NOT IN operations
- BETWEEN operations
- Comparison operators (>, <, >=, <=, =, !=)
- Handling of empty lists and edge cases
"""


from decimal import Decimal


async def test_in_list_with_values(async_order_fixtures):
    """
    Test IN list operation with specific values
    
    This test verifies that the in_list method correctly filters records
    where a column value matches any value in the provided list. This is
    important for filtering by multiple discrete values efficiently.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='in_list_user', email='inlist@example.com', age=30)
    await user.save()

    # Create multiple orders with different statuses for IN testing
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    for i, status in enumerate(statuses):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'IN-{i+1:03d}',
            status=status,
            total_amount=Decimal(f'{(i+1)*50.00}')
        ).save()

    # Test IN query with specific status values
    results = await AsyncOrder.query().in_list(AsyncOrder.c.status, ['pending', 'shipped', 'delivered']).all()
    assert len(results) == 3  # Should match 3 statuses
    
    result_statuses = [r.status for r in results]
    assert 'pending' in result_statuses
    assert 'shipped' in result_statuses
    assert 'delivered' in result_statuses
    assert 'processing' not in result_statuses
    assert 'cancelled' not in result_statuses


async def test_in_list_empty_result_true(async_order_fixtures):
    """
    Test IN list with empty list and empty_result=True
    
    This test verifies that when an empty list is provided to in_list
    with empty_result=True, the query returns no results. This is the
    default behavior and prevents returning all records when no values
    are specified.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='empty_in_user', email='empty@example.com', age=30)
    await user.save()

    # Create some orders for testing
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'EMPTY-{i+1:03d}',
            status='active'
        ).save()

    # Empty list query with empty_result=True (default), should return empty results
    results = await AsyncOrder.query().in_list(AsyncOrder.c.status, [], empty_result=True).all()
    assert len(results) == 0


async def test_in_list_empty_result_false(async_order_fixtures):
    """
    Test IN list with empty list and empty_result=False
    
    This test verifies that when an empty list is provided to in_list
    with empty_result=False, the condition is ignored and all records
    are returned. This is useful when building dynamic queries where
    some filters might be empty.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='no_empty_in_user', email='noempty@example.com', age=30)
    await user.save()

    # Create some orders for testing
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'NOEMPTY-{i+1:03d}',
            status='active'
        ).save()

    # Empty list query with empty_result=False, should return all results
    results = await AsyncOrder.query().in_list(AsyncOrder.c.status, [], empty_result=False).all()
    assert len(results) == 3


async def test_not_in_with_values(async_order_fixtures):
    """
    Test NOT IN operation with specific values
    
    This test verifies that the not_in method correctly filters records
    where a column value does not match any value in the provided list.
    This is the inverse of the IN operation and is useful for exclusions.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='not_in_user', email='notin@example.com', age=30)
    await user.save()

    # Create multiple orders with different statuses for NOT IN testing
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    for i, status in enumerate(statuses):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'NOTIN-{i+1:03d}',
            status=status,
            total_amount=Decimal(f'{(i+1)*50.00}')
        ).save()

    # Test NOT IN query to exclude specific statuses
    results = await AsyncOrder.query().not_in(AsyncOrder.c.status, ['pending', 'cancelled']).all()
    assert len(results) == 3  # Should exclude pending and cancelled, leaving 3
    
    result_statuses = [r.status for r in results]
    assert 'pending' not in result_statuses
    assert 'cancelled' not in result_statuses
    assert 'processing' in result_statuses
    assert 'shipped' in result_statuses
    assert 'delivered' in result_statuses


async def test_not_in_empty_behavior(async_order_fixtures):
    """
    Test NOT IN operation with empty list
    
    This test verifies the behavior of not_in when provided with an
    empty list. Depending on the empty_result parameter, it should
    either return all records or no records.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='not_empty_in_user', email='notempty@example.com', age=30)
    await user.save()

    # Create some orders for testing
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'NOTEMPTY-{i+1:03d}',
            status='active'
        ).save()

    # Empty list NOT IN query with empty_result=False (default), should return all results
    results = await AsyncOrder.query().not_in(AsyncOrder.c.status, [], empty_result=False).all()
    assert len(results) == 3

    # Empty list NOT IN query with empty_result=True, should return empty results
    results = await AsyncOrder.query().not_in(AsyncOrder.c.status, [], empty_result=True).all()
    assert len(results) == 0


async def test_between_operation(async_order_fixtures):
    """
    Test BETWEEN operation for range filtering
    
    This test verifies that range-based queries work correctly using
    BETWEEN logic. Since RangeQueryMixin may not directly provide a
    between method, we simulate it using WHERE conditions with AND.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='between_user', email='between@example.com', age=30)
    await user.save()

    # Create multiple orders with different amounts for BETWEEN testing
    amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'BET-{i+1:03d}',
            total_amount=amount
        ).save()

    # Test BETWEEN query using WHERE conditions (simulated BETWEEN)
    results = await AsyncOrder.query() \
        .where((AsyncOrder.c.total_amount >= Decimal('100.00')) & (AsyncOrder.c.total_amount <= Decimal('200.00'))) \
        .all()
    
    assert len(results) == 3  # 100, 150, 200 are in range
    result_amounts = [r.total_amount for r in results]
    assert Decimal('100.00') in result_amounts
    assert Decimal('150.00') in result_amounts
    assert Decimal('200.00') in result_amounts


async def test_not_between_operation(async_order_fixtures):
    """
    Test NOT BETWEEN operation for range exclusion
    
    This test verifies that range-based exclusion queries work correctly
    using NOT BETWEEN logic. Similar to BETWEEN, this is simulated using
    WHERE conditions with OR.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='not_between_user', email='notbetween@example.com', age=30)
    await user.save()

    # Create multiple orders with different amounts for NOT BETWEEN testing
    amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'NBET-{i+1:03d}',
            total_amount=amount
        ).save()

    # Test NOT BETWEEN query using WHERE conditions (simulated NOT BETWEEN)
    results = await AsyncOrder.query() \
        .where((AsyncOrder.c.total_amount < Decimal('100.00')) | (AsyncOrder.c.total_amount > Decimal('200.00'))) \
        .all()
    
    assert len(results) == 2  # 50 and 250 are not in 100-200 range
    result_amounts = [r.total_amount for r in results]
    assert Decimal('50.00') in result_amounts
    assert Decimal('250.00') in result_amounts


async def test_comparison_operators(async_order_fixtures):
    """
    Test various comparison operators
    
    This test verifies that all basic comparison operators work correctly:
    greater than (>), greater than or equal (>=), less than (<), less than
    or equal (<=), equals (=), and not equals (!=). These are fundamental
    for filtering data based on value comparisons.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(username='comp_user', email='comp@example.com', age=30)
    await user.save()

    # Create multiple orders with different amounts for comparison testing
    amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00')]
    for i, amount in enumerate(amounts):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'COMP-{i+1:03d}',
            total_amount=amount
        ).save()

    # Test greater than operation
    results_gt = await AsyncOrder.query().where(AsyncOrder.c.total_amount > Decimal('100.00')).all()
    assert len(results_gt) == 2  # 150 and 200 are greater than 100

    # Test greater than or equal operation
    results_gte = await AsyncOrder.query().where(AsyncOrder.c.total_amount >= Decimal('100.00')).all()
    assert len(results_gte) == 3  # 100, 150 and 200 are greater than or equal to 100

    # Test less than operation
    results_lt = await AsyncOrder.query().where(AsyncOrder.c.total_amount < Decimal('150.00')).all()
    assert len(results_lt) == 2  # 50 and 100 are less than 150

    # Test less than or equal operation
    results_lte = await AsyncOrder.query().where(AsyncOrder.c.total_amount <= Decimal('150.00')).all()
    assert len(results_lte) == 3  # 50, 100 and 150 are less than or equal to 150

    # Test equals operation
    results_eq = await AsyncOrder.query().where(AsyncOrder.c.total_amount == Decimal('100.00')).all()
    assert len(results_eq) == 1  # Only 100 equals 100

    # Test not equals operation
    results_ne = await AsyncOrder.query().where(AsyncOrder.c.total_amount != Decimal('100.00')).all()
    assert len(results_ne) == 3  # All except 100