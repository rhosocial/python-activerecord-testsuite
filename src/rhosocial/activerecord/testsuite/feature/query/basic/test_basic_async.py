# src/rhosocial/activerecord/testsuite/feature/query/basic/test_basic_async.py
"""Test basic query functionality."""
from decimal import Decimal


async def test_find_by_id(async_order_fixtures):
    """Test finding record by ID"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test user
    user = AsyncUser(
        username='test_user',
        email='test@example.com',
        age=30
    )
    await user.save()

    # Create order
    order = AsyncOrder(
        user_id=user.id,
        order_number='ORD-001',
        total_amount=Decimal('100.00')
    )
    await order.save()

    found = await AsyncOrder.find_one(order.id)
    assert found is not None
    assert found.order_number == 'ORD-001'


async def test_find_by_condition(async_order_fixtures):
    """Test finding record by conditions"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(
        username='test_user',
        email='test@example.com',
        age=30
    )
    await user.save()

    order = AsyncOrder(
        user_id=user.id,
        order_number='ORD-TEST',
        status='processing'
    )
    await order.save()

    found = await AsyncOrder.find_one({'status': 'processing'})
    assert found is not None
    assert found.order_number == 'ORD-TEST'


async def test_find_all(async_order_fixtures):
    """Test finding all records"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(
        username='test_user',
        email='test@example.com',
        age=30
    )
    await user.save()

    for i in range(3):
        order = AsyncOrder(
            user_id=user.id,
            order_number=f'ORD-{i + 1:03d}',
            total_amount=Decimal('100.00')
        )
        await order.save()

    all_orders = await AsyncOrder.query().all()
    assert len(all_orders) == 3


async def test_count(async_order_fixtures):
    """Test record counting"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    user = AsyncUser(
        username='test_user',
        email='test@example.com',
        age=30
    )
    await user.save()

    for i in range(3):
        order = AsyncOrder(
            user_id=user.id,
            order_number=f'ORD-{i + 1:03d}'
        )
        await order.save()

    count = await AsyncOrder.query().count()
    assert count == 3


async def test_exists_method(async_order_fixtures):
    """Test exists() method for checking if records exist"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test user
    user = AsyncUser(
        username='exists_test_user',
        email='exists_test@example.com',
        age=35
    )
    await user.save()

    # Create test order
    order = AsyncOrder(
        user_id=user.id,
        order_number='EXISTS-TEST-001',
        total_amount=Decimal('150.00'),
        status='pending'
    )
    await order.save()

    # Test exists on records that do exist
    exists_result = await AsyncOrder.query().where('order_number = ?', ('EXISTS-TEST-001',)).exists()
    assert exists_result is True

    # Test exists with conditions matching multiple records
    for i in range(3):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'EXISTS-MULTI-{i + 1:03d}',
            total_amount=Decimal('100.00'),
            status='active'
        ).save()

    exists_result = await AsyncOrder.query().where('status = ?', ('active',)).exists()
    assert exists_result is True

    # Test exists on records that do not exist
    exists_result = await AsyncOrder.query().where('order_number = ?', ('NON-EXISTENT',)).exists()
    assert exists_result is False

    # Test exists with complex conditions
    exists_result = (await AsyncOrder.query()
                     .where('total_amount > ?', (Decimal('120.00'),))
                     .where('status = ?', ('pending',))
                     .exists())
    assert exists_result is True

    exists_result = (await AsyncOrder.query()
                     .where('total_amount < ?', (Decimal('50.00'),))
                     .exists())
    assert exists_result is False


# Removed tests that use or_where, start_or_group, end_or_group methods as these are no longer supported


async def test_exists_with_limit_and_offset(async_order_fixtures):
    """Test exists() method with LIMIT and OFFSET clauses"""
    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test user
    user = AsyncUser(
        username='exists_limit_user',
        email='exists_limit@example.com',
        age=50
    )
    await user.save()

    # Create multiple test orders
    for i in range(5):
        await AsyncOrder(
            user_id=user.id,
            order_number=f'LIMIT-TEST-{i + 1:03d}',
            total_amount=Decimal('100.00'),
            status='active'
        ).save()

    # Test exists with limit
    exists_result = await AsyncOrder.query().where('status = ?', ('active',)).limit(1).exists()
    assert exists_result is True

    # Test exists with limit and offset
    exists_result = await AsyncOrder.query().where('status = ?', ('active',)).limit(3).offset(2).exists()
    assert exists_result is False

    # Test exists with limit and offset that exceeds available records
    exists_result = await AsyncOrder.query().where('status = ?', ('active',)).limit(1).offset(10).exists()
    assert exists_result is False


async def test_exists_with_joins(async_order_fixtures):
    """Test exists() method with JOIN clauses"""

    AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

    # Create test user
    user = AsyncUser(
        username='exists_join_user',
        email='exists_join@example.com',
        age=55
    )
    await user.save()

    # Create test order
    order = AsyncOrder(
        user_id=user.id,
        order_number='JOIN-EXISTS-001',
        total_amount=Decimal('350.00'),
        status='pending'
    )
    await order.save()

    # Create order item
    item = AsyncOrderItem(
        order_id=order.id,
        product_name='Test Product',
        quantity=2,
        price=Decimal('175.00'),
        unit_price=Decimal('150.00')
    )
    await item.save()

    # Test exists with JOIN
    exists_result = (await AsyncOrder.query()
                     .join('order_items', 'orders.id = order_items.order_id')
                     .join('users', 'orders.user_id = users.id')
                     .where('orders.order_number = ?', ('JOIN-EXISTS-001',))
                     .where('users.username = ?', ('exists_join_user',))
                     .where('order_items.product_name = ?', ('Test Product',))
                     .exists())
    assert exists_result is True

    # Test exists with JOIN and non-matching condition
    exists_result = (await AsyncOrder.query()
                     .join('order_items', 'orders.id = order_items.order_id')
                     .join('users', 'orders.user_id = users.id')
                     .where('orders.order_number = ?', ('JOIN-EXISTS-001',))
                     .where('order_items.product_name = ?', ('Non-Existent Product',))
                     .exists())
    assert exists_result is False
