# src/rhosocial/activerecord/testsuite/feature/query/basic/test_queries_async.py
"""
Async query tests

This module contains tests for asynchronous query operations including:
- Async ActiveQuery initialization
- Async aggregation operations
- Async relation loading
- Async basic operations (all, one, first, exists)
- Async JOIN operations
"""
from decimal import Decimal

# Import the async_order_fixtures directly from conftest
from rhosocial.activerecord.testsuite.feature.query.conftest import async_order_fixtures


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
    assert len(results) == 1, "Expected exactly one matching order"
    assert results[0].order_number == 'ASYNC-INIT-001', \
        "Expected order_number to be ASYNC-INIT-001"


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
    assert total == expected_total, "Expected total to equal sum of amounts"

    count = await async_query.count()
    assert count == len(amounts), "Expected count to equal len of amounts"


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
    assert len(results) == 1, "Expected exactly one matching order"

    result = results[0]
    assert hasattr(result, 'user'), "Expected result to expose a user relation"
    # Access the related user instance by calling the relation method
    related_user = await result.user()  # For async relations, we need to await the call
    assert related_user.id == user.id, "Expected related user id to match"


async def test_async_basic_operations(async_order_fixtures):
    """
    Test async basic operations
    
    Note: Each query operation uses a fresh query object to ensure SQL standard compliance.
    Aggregate queries (like exists/count) should not have ORDER BY clauses without GROUP BY,
    as this violates SQL standard and causes PostgreSQL to raise GroupingError.
    """
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test data for async basic operations
    user = AsyncUser(username='async_basic_user', email='asyncbasic@example.com', age=30)
    await user.save()

    order = AsyncOrder(user_id=user.id, order_number='ASYNC-BASIC-001', total_amount=Decimal('125.50'))
    await order.save()

    # Async one() operation - fresh query object
    one_result = await AsyncOrder.query().where(AsyncOrder.c.id == order.id).one()
    assert one_result is not None, "Expected one() to return a matching order"
    assert one_result.id == order.id, "Expected one_result id to match order id"

    # Async one() with order_by - fresh query object (ORDER BY is meaningful here)
    one_result = await AsyncOrder.query().order_by(AsyncOrder.c.order_number).one()
    assert one_result is not None, "Expected one() to return a result with order_by"

    # Async exists() operation - fresh query object (no ORDER BY for aggregate)
    exists = await AsyncOrder.query().where(
        AsyncOrder.c.order_number == 'ASYNC-BASIC-001'
    ).exists()
    assert exists is True, "Expected exists() to be True for existing record"

    # Async exists() for non-existent record - fresh query object
    exists_not = await AsyncOrder.query().where(
        AsyncOrder.c.order_number == 'NON-EXISTENT'
    ).exists()
    assert exists_not is False, "Expected exists() to be False for missing record"


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

    assert len(joined_results) == 1, "Expected exactly one joined result"
    assert joined_results[0].order_number == 'ASYNC-JOIN-001', \
        "Expected joined order_number to be ASYNC-JOIN-001"