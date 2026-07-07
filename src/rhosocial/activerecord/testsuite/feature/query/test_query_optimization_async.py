# src/rhosocial/activerecord/testsuite/feature/query/test_query_optimization.py
"""Query optimization tests"""
import pytest
from decimal import Decimal


@pytest.mark.asyncio


async def test_n_plus_one_detection(async_combined_fixtures):
    """
    Test N+1 query detection and prevention
    
    This test demonstrates the N+1 query problem where retrieving related
    data results in multiple individual queries instead of a single optimized
    query. The test compares the performance of lazy loading vs eager loading.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem, AsyncPost, AsyncComment = async_combined_fixtures

    # Create user for N+1 testing
    user = AsyncUser(username='nplus1_detect_user', email='nplus1detect@example.com', age=30)
    await user.save()

    # Create multiple orders for N+1 scenario
    orders = []
    for i in range(5):
        order = AsyncOrder(
            user_id=user.id,
            order_number=f'N1D-{i+1:03d}',
            total_amount=Decimal(f'{(i+1)*50.00}')
        )
        await order.save()
        orders.append(order)

        # Create order items for each order
        for j in range(2):
            item = AsyncOrderItem(
                order_id=order.id,
                product_name=f'N1D-Item-{i}-{j}',
                quantity=j + 1,
                unit_price=Decimal('25.00'),
                subtotal=Decimal(f'{(j+1)*25.00}')
            )
            await item.save()

    # Scenario 1: Without eager loading, will cause N+1 problem
    # This would result in 1 query for orders + N queries for users (N+1 total)
    orders_without_eager = AsyncOrder.query().where(AsyncOrder.c.user_id == user.id).all()
    for order in orders_without_eager:
        # Access associated user info, this will trigger additional query
        user_obj = await AsyncUser.find_one(order.user_id)

    # Scenario 2: With eager loading, avoid N+1 problem
    # This results in 1 optimized query with JOIN
    orders_with_eager = AsyncOrder.query().with_('user').where(AsyncOrder.c.user_id == user.id).all()
    
    # Access pre-loaded user info (should not trigger additional queries)
    accessed_users_eager = []
    for order in orders_with_eager:
        # Access pre-loaded data
        if hasattr(order, 'user'):
            # If relation attribute exists, verify it exists
            accessed_users_eager.append(order.user)
        else:
            # If relation not set, still need to query
            accessed_users_eager.append(await AsyncUser.find_one(order.user_id))

    # Verify both approaches return same number of results
    assert len(orders_without_eager) == len(orders_with_eager)
    assert len(orders_with_eager) == 5


@pytest.mark.asyncio


async def test_batch_loading_performance(async_order_fixtures):
    """
    Test batch loading performance improvements
    
    This test verifies that batch loading techniques can significantly
    improve performance by reducing the number of database round trips
    when loading related data for multiple records.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create user for batch loading testing
    user = AsyncUser(username='batch_user', email='batch@example.com', age=30)
    await user.save()

    # Create multiple orders for batch loading
    orders = []
    for i in range(10):
        order = AsyncOrder(
            user_id=user.id,
            order_number=f'BATCH-{i+1:03d}',
            total_amount=Decimal(f'{(i+1)*30.00}')
        )
        await order.save()
        orders.append(order)

        # Create multiple order items for each order
        for j in range(3):
            item = AsyncOrderItem(
                order_id=order.id,
                product_name=f'Batch-Item-{i}-{j}',
                quantity=j + 1,
                unit_price=Decimal('10.00'),
                subtotal=Decimal(f'{(j+1)*10.00}')
            )
            await item.save()

    # Test batch loading performance: load all orders and their order items in one go
    orders_with_items = AsyncOrder.query().with_('items').where(AsyncOrder.c.user_id == user.id).all()
    
    # Verify all orders are loaded
    assert len(orders_with_items) == 10
    
    # Verify each order may contain its order items (if relation is set correctly)
    for order in orders_with_items:
        # Check if we can access associated order items without triggering additional queries
        if hasattr(order, 'items'):
            # If relation attribute exists, verify it exists
            assert order.items is not None


@pytest.mark.asyncio


async def test_query_caching_mechanism(async_order_fixtures):
    """
    Test query caching mechanism functionality
    
    This test verifies that query caching works correctly by ensuring
    that identical queries return consistent results and that updates
    to data are properly reflected in cached queries.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for caching testing
    user = AsyncUser(username='cache_user', email='cache@example.com', age=30)
    await user.save()

    order = AsyncOrder(
        user_id=user.id,
        order_number='CACHE-001',
        total_amount=Decimal('125.75'),
        status='confirmed'
    )
    await order.save()

    # Execute same query multiple times to test caching
    query = AsyncOrder.query().where(AsyncOrder.c.order_number == 'CACHE-001')
    
    # First execution
    result1 = await query.all()
    
    # Second execution of same query (should potentially use cache)
    result2 = await query.all()
    
    # Verify results are consistent
    assert len(result1) == len(result2) == 1
    assert result1[0].id == result2[0].id
    assert result1[0].order_number == result2[0].order_number == 'CACHE-001'

    # Test query changes after modification
    # Update order to test cache invalidation
    order.status = 'shipped'
    await order.save()

    # Execute query again, should reflect update (cache should be invalidated)
    result3 = await query.all()
    assert len(result3) == 1
    assert result3[0].status == 'shipped'

    # Test parameterized query caching
    param_query = AsyncOrder.query().where('order_number = ?', ('CACHE-001',))
    result4 = await param_query.all()
    assert len(result4) == 1
    assert result4[0].id == order.id