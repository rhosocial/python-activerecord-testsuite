# tests/rhosocial/activerecord_test/feature/query/test_async_queries.py
"""
Async query tests

This module contains tests for asynchronous query operations including:
- Async ActiveQuery initialization
- Async aggregation operations
- Async relation loading
- Async basic operations (all, one, first, exists)
- Async JOIN operations
"""
import pytest
from decimal import Decimal

# Import the async_order_fixtures directly from conftest
from rhosocial.activerecord.testsuite.feature.query.conftest import async_order_fixtures


@pytest.mark.asyncio
async def test_async_active_query_init(async_order_fixtures):
    """
    Test async ActiveQuery initialization
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async query testing
    user = AsyncUser(username='async_init_user', email='asyncinit@example.com', age=30)
    await user.save()

    order = AsyncOrder(user_id=user.id, order_number='ASYNC-INIT-001', total_amount=Decimal('100.00'))
    await order.save()

    # Async query
    async_query = AsyncOrder.query()
    results = await async_query.where(AsyncOrder.c.id == order.id).all()
    assert len(results) == 1
    assert results[0].order_number == 'ASYNC-INIT-001'


@pytest.mark.asyncio
async def test_async_aggregate_operations(async_order_fixtures):
    """
    Test async aggregation operations
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async aggregation testing
    user = AsyncUser(username='async_agg_user', email='asyncagg@example.com', age=30)
    await user.save()

    amounts = [Decimal('50.00'), Decimal('150.00'), Decimal('250.00')]
    for i, amount in enumerate(amounts):
        o = AsyncOrder(
            user_id=user.id,
            order_number=f'ASYNC-AGG-{i+1:03d}',
            total_amount=amount
        )
        await o.save()

    # Async aggregation query
    async_query = AsyncOrder.query()
    total = await async_query.sum_(AsyncOrder.c.total_amount)
    expected_total = sum(amounts)
    assert total == expected_total

    count = await async_query.count()
    assert count == len(amounts)


@pytest.mark.asyncio
async def test_async_relation_loading(async_order_fixtures):
    """
    Test async relation loading
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async relation loading
    user = AsyncUser(username='async_rel_user', email='asyncrel@example.com', age=30)
    await user.save()

    order = AsyncOrder(user_id=user.id, order_number='ASYNC-REL-001', total_amount=Decimal('200.00'))
    await order.save()

    # Async relation query
    async_query = AsyncOrder.query()
    results = await async_query.with_('user').where(AsyncOrder.c.id == order.id).all()
    assert len(results) == 1

    result = results[0]
    assert hasattr(result, 'user')
    # Access the related user instance by calling the relation method
    related_user = await result.user()  # For async relations, we need to await the call
    assert related_user.id == user.id


@pytest.mark.asyncio
async def test_async_basic_operations(async_order_fixtures):
    """
    Test async basic operations
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async basic operations
    user = AsyncUser(username='async_basic_user', email='asyncbasic@example.com', age=30)
    await user.save()

    order = AsyncOrder(user_id=user.id, order_number='ASYNC-BASIC-001', total_amount=Decimal('125.50'))
    await order.save()

    # Test async basic operations
    async_query = AsyncOrder.query()

    # Async one() operation
    one_result = await async_query.where(AsyncOrder.c.id == order.id).one()
    assert one_result is not None
    assert one_result.id == order.id

    # Async one() operation (replacing first() since first() doesn't exist)
    one_result = await async_query.order_by(AsyncOrder.c.order_number).one()
    assert one_result is not None

    # Async exists() operation
    exists = await async_query.where(AsyncOrder.c.order_number == 'ASYNC-BASIC-001').exists()
    assert exists is True

    exists_not = await async_query.where(AsyncOrder.c.order_number == 'NON-EXISTENT').exists()
    assert exists_not is False


@pytest.mark.asyncio
async def test_async_join_operations(async_order_fixtures):
    """
    Test async JOIN operations
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async JOIN operations
    user = AsyncUser(username='async_join_user', email='asyncjoin@example.com', age=30)
    await user.save()

    order = AsyncOrder(user_id=user.id, order_number='ASYNC-JOIN-001', total_amount=Decimal('300.00'))
    await order.save()

    # Async JOIN query
    async_query = AsyncOrder.query()
    joined_results = await async_query \
        .inner_join(AsyncUser, on=(AsyncOrder.c.user_id == AsyncUser.c.id)) \
        .where(AsyncOrder.c.id == order.id) \
        .all()

    assert len(joined_results) == 1
    assert joined_results[0].order_number == 'ASYNC-JOIN-001'