# src/rhosocial/activerecord/testsuite/feature/query/basic/test_queries.py
"""
Synchronous query tests

This module contains tests for synchronous query operations including:
- Sync ActiveQuery initialization
- Sync aggregation operations
- Sync relation loading
- Sync basic operations (all, one, first, exists)
- Sync JOIN operations

This file is the synchronous counterpart to test_queries_async.py,
following the sync/async parity principle of the framework.
"""
import pytest
from decimal import Decimal

# Import the order_fixtures directly from conftest
from rhosocial.activerecord.testsuite.feature.query.conftest import order_fixtures


def test_sync_active_query_init(order_fixtures):
    """
    Test sync ActiveQuery initialization
    """
    User, Order, OrderItem = order_fixtures

    # Create test data for sync query testing
    user = User(username='sync_init_user', email='syncinit@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='SYNC-INIT-001', total_amount=Decimal('100.00'))
    order.save()

    # Sync query
    sync_query = Order.query()
    results = sync_query.where(Order.c.id == order.id).all()
    assert len(results) == 1
    assert results[0].order_number == 'SYNC-INIT-001'


def test_sync_aggregate_operations(order_fixtures):
    """
    Test sync aggregation operations
    """
    User, Order, OrderItem = order_fixtures

    # Create test data for sync aggregation testing
    user = User(username='sync_agg_user', email='syncagg@example.com', age=30)
    user.save()

    amounts = [Decimal('50.00'), Decimal('150.00'), Decimal('250.00')]
    for i, amount in enumerate(amounts):
        o = Order(
            user_id=user.id,
            order_number=f'SYNC-AGG-{i+1:03d}',
            total_amount=amount
        )
        o.save()

    # Sync aggregation query
    sync_query = Order.query()
    total = sync_query.sum_(Order.c.total_amount)
    expected_total = sum(amounts)
    assert total == expected_total

    count = Order.query().count()
    assert count == len(amounts)


def test_sync_relation_loading(order_fixtures):
    """
    Test sync relation loading
    """
    User, Order, OrderItem = order_fixtures

    # Create test data for sync relation loading
    user = User(username='sync_rel_user', email='syncrel@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='SYNC-REL-001', total_amount=Decimal('200.00'))
    order.save()

    # Sync relation query
    sync_query = Order.query()
    results = sync_query.with_('user').where(Order.c.id == order.id).all()
    assert len(results) == 1

    result = results[0]
    assert hasattr(result, 'user')
    # Access the related user instance by calling the relation method
    related_user = result.user()
    assert related_user.id == user.id


def test_sync_basic_operations(order_fixtures):
    """
    Test sync basic operations
    
    Note: Each query operation uses a fresh query object to ensure SQL standard compliance.
    Aggregate queries (like exists/count) should not have ORDER BY clauses without GROUP BY,
    as this violates SQL standard and causes PostgreSQL to raise GroupingError.
    """
    User, Order, OrderItem = order_fixtures

    # Create test data for sync basic operations
    user = User(username='sync_basic_user', email='syncbasic@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='SYNC-BASIC-001', total_amount=Decimal('125.50'))
    order.save()

    # Sync one() operation - fresh query object
    one_result = Order.query().where(Order.c.id == order.id).one()
    assert one_result is not None
    assert one_result.id == order.id

    # Sync one() with order_by - fresh query object (ORDER BY is meaningful here)
    one_result = Order.query().order_by(Order.c.order_number).one()
    assert one_result is not None

    # Sync exists() operation - fresh query object (no ORDER BY for aggregate)
    exists = Order.query().where(
        Order.c.order_number == 'SYNC-BASIC-001'
    ).exists()
    assert exists is True

    # Sync exists() for non-existent record - fresh query object
    exists_not = Order.query().where(
        Order.c.order_number == 'NON-EXISTENT'
    ).exists()
    assert exists_not is False


def test_sync_join_operations(order_fixtures):
    """
    Test sync JOIN operations
    """
    User, Order, OrderItem = order_fixtures

    # Create test data for sync JOIN operations
    user = User(username='sync_join_user', email='syncjoin@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='SYNC-JOIN-001', total_amount=Decimal('300.00'))
    order.save()

    # Sync JOIN query
    sync_query = Order.query()
    joined_results = sync_query \
        .inner_join(User, on=(Order.c.user_id == User.c.id)) \
        .where(Order.c.id == order.id) \
        .all()

    assert len(joined_results) == 1
    assert joined_results[0].order_number == 'SYNC-JOIN-001'
