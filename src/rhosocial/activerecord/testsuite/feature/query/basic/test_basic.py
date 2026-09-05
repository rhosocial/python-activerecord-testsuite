# src/rhosocial/activerecord/testsuite/feature/query/basic/test_basic.py
"""Test basic query functionality."""
from decimal import Decimal


def test_find_by_id(order_fixtures):
    """Test finding record by ID"""
    User, Order, OrderItem = order_fixtures

    # Create test user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    # Create order
    order = Order(
        user_id=user.id,
        order_number='ORD-001',
        total_amount=Decimal('100.00')
    )
    order.save()

    found = Order.find_one(order.id)
    assert found is not None, "Expected to find the order by id"
    assert found.order_number == 'ORD-001', "Expected order_number to be ORD-001"


def test_find_by_condition(order_fixtures):
    """Test finding record by conditions"""
    User, Order, OrderItem = order_fixtures

    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    order = Order(
        user_id=user.id,
        order_number='ORD-TEST',
        status='processing'
    )
    order.save()

    found = Order.find_one({'status': 'processing'})
    assert found is not None, "Expected to find the order by status"
    assert found.order_number == 'ORD-TEST', "Expected order_number to be ORD-TEST"


def test_find_all(order_fixtures):
    """Test finding all records"""
    User, Order, OrderItem = order_fixtures

    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    for i in range(3):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1:03d}',
            total_amount=Decimal('100.00')
        )
        order.save()

    all_orders = Order.query().all()
    assert len(all_orders) == 3, "Expected 3 orders to be returned"


def test_count(order_fixtures):
    """Test record counting"""
    User, Order, OrderItem = order_fixtures

    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    for i in range(3):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1:03d}'
        )
        order.save()

    count = Order.query().count()
    assert count == 3, "Expected count to be 3"


def test_exists_method(order_fixtures):
    """Test exists() method for checking if records exist"""
    User, Order, OrderItem = order_fixtures

    # Create test user
    user = User(
        username='exists_test_user',
        email='exists_test@example.com',
        age=35
    )
    user.save()

    # Create test order
    order = Order(
        user_id=user.id,
        order_number='EXISTS-TEST-001',
        total_amount=Decimal('150.00'),
        status='pending'
    )
    order.save()

    # Test exists on records that do exist
    exists_result = Order.query().where('order_number = ?', ('EXISTS-TEST-001',)).exists()
    assert exists_result is True, "Expected exists() to be True for existing record"

    # Test exists with conditions matching multiple records
    for i in range(3):
        Order(
            user_id=user.id,
            order_number=f'EXISTS-MULTI-{i + 1:03d}',
            total_amount=Decimal('100.00'),
            status='active'
        ).save()

    exists_result = Order.query().where('status = ?', ('active',)).exists()
    assert exists_result is True, "Expected exists() to be True for matching multiple records"

    # Test exists on records that do not exist
    exists_result = Order.query().where('order_number = ?', ('NON-EXISTENT',)).exists()
    assert exists_result is False, "Expected exists() to be False for missing record"

    # Test exists with complex conditions
    exists_result = (Order.query()
                     .where('total_amount > ?', (Decimal('120.00'),))
                     .where('status = ?', ('pending',))
                     .exists())
    assert exists_result is True, "Expected exists() to be True with complex conditions"

    exists_result = (Order.query()
                     .where('total_amount < ?', (Decimal('50.00'),))
                     .exists())
    assert exists_result is False, "Expected exists() to be False with no matches"


# Removed tests that use or_where, start_or_group, end_or_group methods as these are no longer supported


def test_exists_with_limit_and_offset(order_fixtures):
    """Test exists() method with LIMIT and OFFSET clauses"""
    User, Order, OrderItem = order_fixtures

    # Create test user
    user = User(
        username='exists_limit_user',
        email='exists_limit@example.com',
        age=50
    )
    user.save()

    # Create multiple test orders
    for i in range(5):
        Order(
            user_id=user.id,
            order_number=f'LIMIT-TEST-{i + 1:03d}',
            total_amount=Decimal('100.00'),
            status='active'
        ).save()

    # Test exists with limit
    exists_result = Order.query().where('status = ?', ('active',)).limit(1).exists()
    assert exists_result is True, "Expected exists() to be True with limit"

    # Test exists with limit and offset
    exists_result = Order.query().where('status = ?', ('active',)).limit(3).offset(2).exists()
    assert exists_result is False, "Expected exists() to be False past available records"

    # Test exists with limit and offset that exceeds available records
    exists_result = Order.query().where('status = ?', ('active',)).limit(1).offset(10).exists()
    assert exists_result is False, "Expected exists() to be False when offset exceeds records"


def test_exists_with_joins(order_fixtures):
    """Test exists() method with JOIN clauses"""
    User, Order, OrderItem = order_fixtures

    # Create test user
    user = User(
        username='exists_join_user',
        email='exists_join@example.com',
        age=55
    )
    user.save()

    # Create test order
    order = Order(
        user_id=user.id,
        order_number='JOIN-EXISTS-001',
        total_amount=Decimal('350.00'),
        status='pending'
    )
    order.save()

    # Create order item
    item = OrderItem(
        order_id=order.id,
        product_name='Test Product',
        quantity=2,
        price=Decimal('175.00'),
        unit_price=Decimal('150.00')
    )
    item.save()

    # Test exists with JOIN
    exists_result = (Order.query()
                     .join('order_items', 'orders.id = order_items.order_id')
                     .join('users', 'orders.user_id = users.id')
                     .where('orders.order_number = ?', ('JOIN-EXISTS-001',))
                     .where('users.username = ?', ('exists_join_user',))
                     .where('order_items.product_name = ?', ('Test Product',))
                     .exists())
    assert exists_result is True, "Expected exists() to be True with JOIN matching records"

    # Test exists with JOIN and non-matching condition
    exists_result = (Order.query()
                     .join('order_items', 'orders.id = order_items.order_id')
                     .join('users', 'orders.user_id = users.id')
                     .where('orders.order_number = ?', ('JOIN-EXISTS-001',))
                     .where('order_items.product_name = ?', ('Non-Existent Product',))
                     .exists())
    assert exists_result is False, "Expected exists() to be False with non-matching JOIN"
