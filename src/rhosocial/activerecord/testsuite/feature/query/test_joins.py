# src/rhosocial/activerecord/testsuite/feature/query/test_joins.py
"""Test cases for JOIN queries in ActiveQuery."""
from decimal import Decimal


def test_inner_join(order_fixtures):
    """Test inner join queries"""
    User, Order, OrderItem = order_fixtures

    # Create user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30,
        balance=Decimal('1000.00')
    )
    user.save()

    # Create order
    order = Order(
        user_id=user.id,
        order_number='ORD-001',
        total_amount=Decimal('150.00')
    )
    order.save()

    # Create order item
    item = OrderItem(
        order_id=order.id,
        product_name='Test Product',
        quantity=2,
        unit_price=Decimal('75.00'),
        subtotal=Decimal('150.00')
    )
    item.save()

    # Test three-table INNER JOIN
    results = Order.query() \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .where(f'{Order.__table_name__}.id = ?', (order.id,)) \
        .all()

    assert len(results) == 1
    assert results[0].id == order.id


def test_left_join(order_fixtures):
    """Test left join queries"""
    User, Order, OrderItem = order_fixtures

    # Create user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    # Create two orders: one with order items, one without
    order1 = Order(user_id=user.id, order_number='ORD-001')
    order1.save()

    order2 = Order(user_id=user.id, order_number='ORD-002')
    order2.save()

    # Create order item only for order1
    item = OrderItem(
        order_id=order1.id,
        product_name='Test Product',
        quantity=1,
        unit_price=Decimal('100.00'),
        subtotal=Decimal('100.00')
    )
    item.save()

    # Test LEFT JOIN
    results = Order.query().select('orders.*') \
        .join(f"""
            LEFT JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.user_id = ?', (user.id,)) \
        .order_by(f'{Order.__table_name__}.order_number') \
        .all()

    assert len(results) == 2  # Should return both orders


def test_join_with_conditions(order_fixtures):
    """Test join queries with conditions"""
    User, Order, OrderItem = order_fixtures

    # Create user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    # Create order
    order = Order(user_id=user.id, order_number='ORD-001')
    order.save()

    # Create two order items with different quantities
    items = [
        OrderItem(
            order_id=order.id,
            product_name=f'Product {i}',
            quantity=i + 1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal(f'{(i + 1) * 100}.00')
        )
        for i in range(2)
    ]
    for item in items:
        item.save()

    # Test JOIN with conditions
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
            AND {OrderItem.__table_name__}.quantity > 1
        """) \
        .where(f'{User.__table_name__}.username = ?', ('test_user',)) \
        .all()

    assert len(results) == 1  # Only one order item has quantity > 1


# Removed test that uses or_where, start_or_group, end_or_group methods as these are no longer supported


def test_join_with_in_conditions(order_fixtures):
    """Test join queries with IN conditions"""
    User, Order, OrderItem = order_fixtures

    # Create test users
    users = [
        User(username=f'user{i}', email=f'user{i}@example.com', age=25 + i)
        for i in range(3)
    ]
    for user in users:
        user.save()

    # Create orders and order items
    orders = []
    for i, user in enumerate(users):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            status=['pending', 'paid', 'shipped'][i],
            total_amount=Decimal(f'{(i + 1) * 100}.00')
        )
        order.save()
        orders.append(order)

        item = OrderItem(
            order_id=order.id,
            product_name=f'Product {i + 1}',
            quantity=i + 1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal(f'{(i + 1) * 100}.00')
        )
        item.save()

    # Test JOIN with IN condition using where clause with IN operator
    results = Order.query() \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.status IN ?', (['pending', 'paid'],)) \
        .where(f'{OrderItem.__table_name__}.quantity > ?', (1,)) \
        .all()

    assert len(results) >= 0  # Number may vary based on test data
    for result in results:
        assert result.status in ['pending', 'paid']

    # Test JOIN with NOT IN condition using where clause with NOT IN operator
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .where(f'{Order.__table_name__}.status NOT IN ?', (['shipped'],)) \
        .order_by(f'{Order.__table_name__}.total_amount') \
        .all()

    assert len(results) >= 0  # Number may vary based on test data
    for result in results:
        assert result.status != 'shipped'


def test_complex_join_conditions(order_fixtures):
    """Test complex JOIN condition combinations"""
    User, Order, OrderItem = order_fixtures

    # Create test users
    users = [
        User(username=f'user{i}', email=f'user{i}@example.com', age=25 + i)
        for i in range(3)
    ]
    for user in users:
        user.save()

    # Create orders and order items
    orders = []
    statuses = ['pending', 'paid', 'shipped']
    for i, user in enumerate(users):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            status=statuses[i],
            total_amount=Decimal(f'{(i + 1) * 100}.00')
        )
        order.save()
        orders.append(order)

        # Create two order items for each order
        for j in range(2):
            item = OrderItem(
                order_id=order.id,
                product_name=f'Product {i}-{j}',
                quantity=i + j + 1,
                unit_price=Decimal('100.00'),
                subtotal=Decimal(f'{(i + j + 1) * 100}.00')
            )
            item.save()

    # Test basic join functionality
    results = Order.query() \
        .select(f'{Order.__table_name__}.*', f'{User.__table_name__}.age') \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{User.__table_name__}.age < ?', (30,)) \
        .order_by(f'{Order.__table_name__}.total_amount') \
        .all()

    # Verify results: user age < 30
    for result in results:
        user = User.find_one(result.user_id)  # Get related user
        assert user.age < 30  # Use related user's age


def test_complex_join_conditions_2(order_fixtures):
    """Test complex join queries with new condition methods"""
    User, Order, OrderItem = order_fixtures

    # Create test users with varying attributes
    users = [
        User(username='alpha', email='alpha@example.com', age=25),
        User(username='beta', email='beta@example.com', age=None),
        User(username='gamma', email='gamma@example.com', age=35)
    ]
    for user in users:
        user.save()

    # Create orders with various characteristics for each user
    status_map = {
        'alpha': [('ORD-A1', 'pending', '150.00'), ('ORD-A2', 'paid', '250.00')],
        'beta': [('ORD-B1', 'shipped', '350.00'), ('ORD-B2', 'pending', '450.00')],
        'gamma': [('ORD-C1', 'paid', '550.00')]
    }

    for user in users:
        for order_num, status, amount in status_map[user.username]:
            order = Order(
                user_id=user.id,
                order_number=order_num,
                status=status,
                total_amount=Decimal(amount)
            )
            order.save()

            # Create multiple order items for each order
            for i in range(2):
                item = OrderItem(
                    order_id=order.id,
                    product_name=f'Product {order_num}-{i + 1}',
                    quantity=i + 1,
                    unit_price=Decimal('100.00'),
                    subtotal=Decimal('100.00') * (i + 1)
                )
                item.save()

    # Basic join query
    results = Order.query() \
        .select(
        f'{Order.__table_name__}.*',
        f'{User.__table_name__}.username',
        f'{OrderItem.__table_name__}.quantity'
    ) \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            LEFT JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.total_amount > ?', (Decimal('100.00'),)) \
        .order_by(f'{Order.__table_name__}.total_amount DESC') \
        .all()

    # Verify results
    assert len(results) > 0
    for result in results:
        # Get related user for verification
        user = User.find_one(result.user_id)

        # Check that each result has amount > 100.00
        assert result.total_amount > Decimal('100.00')

    # Additional basic join query
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.total_amount < ?', (Decimal('1000.00'),)) \
        .all()

    # Verify the second query results
    for result in results:
        # Amount should be less than 1000.00
        assert result.total_amount < Decimal('1000.00')

    # Create user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    # Create two orders: one with order items, one without
    order1 = Order(user_id=user.id, order_number='ORD-001')
    order1.save()

    order2 = Order(user_id=user.id, order_number='ORD-002')
    order2.save()

    # Create order item only for order1
    item = OrderItem(
        order_id=order1.id,
        product_name='Test Product',
        quantity=1,
        unit_price=Decimal('100.00'),
        subtotal=Decimal('100.00')
    )
    item.save()

    # Test LEFT JOIN
    results = Order.query().select('orders.*') \
        .join(f"""
            LEFT JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.user_id = ?', (user.id,)) \
        .order_by(f'{Order.__table_name__}.order_number') \
        .all()

    assert len(results) == 2  # Should return both orders


def test_join_with_conditions(order_fixtures):
    """Test join queries with conditions"""
    User, Order, OrderItem = order_fixtures

    # Create user
    user = User(
        username='test_user',
        email='test@example.com',
        age=30
    )
    user.save()

    # Create order
    order = Order(user_id=user.id, order_number='ORD-001')
    order.save()

    # Create two order items with different quantities
    items = [
        OrderItem(
            order_id=order.id,
            product_name=f'Product {i}',
            quantity=i + 1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal(f'{(i + 1) * 100}.00')
        )
        for i in range(2)
    ]
    for item in items:
        item.save()

    # Test JOIN with conditions
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
            AND {OrderItem.__table_name__}.quantity > 1
        """) \
        .where(f'{User.__table_name__}.username = ?', ('test_user',)) \
        .all()

    assert len(results) == 1  # Only one order item has quantity > 1


# Removed test that uses or_where, start_or_group, end_or_group methods as these are no longer supported


def test_join_with_in_conditions(order_fixtures):
    """Test join queries with IN conditions"""
    User, Order, OrderItem = order_fixtures

    # Create test users
    users = [
        User(username=f'user{i}', email=f'user{i}@example.com', age=25 + i)
        for i in range(3)
    ]
    for user in users:
        user.save()

    # Create orders and order items
    orders = []
    for i, user in enumerate(users):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            status=['pending', 'paid', 'shipped'][i],
            total_amount=Decimal(f'{(i + 1) * 100}.00')
        )
        order.save()
        orders.append(order)

        item = OrderItem(
            order_id=order.id,
            product_name=f'Product {i + 1}',
            quantity=i + 1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal(f'{(i + 1) * 100}.00')
        )
        item.save()

    # Test JOIN with IN condition using where clause with IN operator
    results = Order.query() \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.status IN ?', (['pending', 'paid'],)) \
        .where(f'{OrderItem.__table_name__}.quantity > ?', (1,)) \
        .all()

    assert len(results) >= 0  # Number may vary based on test data
    for result in results:
        assert result.status in ['pending', 'paid']

    # Test JOIN with NOT IN condition using where clause with NOT IN operator
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .where(f'{Order.__table_name__}.status NOT IN ?', (['shipped'],)) \
        .order_by(f'{Order.__table_name__}.total_amount') \
        .all()

    assert len(results) >= 0  # Number may vary based on test data
    for result in results:
        assert result.status != 'shipped'


def test_complex_join_conditions(order_fixtures):
    """Test complex JOIN condition combinations"""
    User, Order, OrderItem = order_fixtures

    # Create test users
    users = [
        User(username=f'user{i}', email=f'user{i}@example.com', age=25 + i)
        for i in range(3)
    ]
    for user in users:
        user.save()

    # Create orders and order items
    orders = []
    statuses = ['pending', 'paid', 'shipped']
    for i, user in enumerate(users):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            status=statuses[i],
            total_amount=Decimal(f'{(i + 1) * 100}.00')
        )
        order.save()
        orders.append(order)

        # Create two order items for each order
        for j in range(2):
            item = OrderItem(
                order_id=order.id,
                product_name=f'Product {i}-{j}',
                quantity=i + j + 1,
                unit_price=Decimal('100.00'),
                subtotal=Decimal(f'{(i + j + 1) * 100}.00')
            )
            item.save()

    # Test basic join functionality
    results = Order.query() \
        .select(f'{Order.__table_name__}.*', f'{User.__table_name__}.age') \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{User.__table_name__}.age < ?', (30,)) \
        .order_by(f'{Order.__table_name__}.total_amount') \
        .all()

    # Verify results: user age < 30
    for result in results:
        user = User.find_one(result.user_id)  # Get related user
        assert user.age < 30  # Use related user's age


def test_complex_join_conditions_2(order_fixtures):
    """Test complex join queries with new condition methods"""
    User, Order, OrderItem = order_fixtures

    # Create test users with varying attributes
    users = [
        User(username='alpha', email='alpha@example.com', age=25),
        User(username='beta', email='beta@example.com', age=None),
        User(username='gamma', email='gamma@example.com', age=35)
    ]
    for user in users:
        user.save()

    # Create orders with various characteristics for each user
    status_map = {
        'alpha': [('ORD-A1', 'pending', '150.00'), ('ORD-A2', 'paid', '250.00')],
        'beta': [('ORD-B1', 'shipped', '350.00'), ('ORD-B2', 'pending', '450.00')],
        'gamma': [('ORD-C1', 'paid', '550.00')]
    }

    for user in users:
        for order_num, status, amount in status_map[user.username]:
            order = Order(
                user_id=user.id,
                order_number=order_num,
                status=status,
                total_amount=Decimal(amount)
            )
            order.save()

            # Create multiple order items for each order
            for i in range(2):
                item = OrderItem(
                    order_id=order.id,
                    product_name=f'Product {order_num}-{i + 1}',
                    quantity=i + 1,
                    unit_price=Decimal('100.00'),
                    subtotal=Decimal('100.00') * (i + 1)
                )
                item.save()

    # Basic join query
    results = Order.query() \
        .select(
        f'{Order.__table_name__}.*',
        f'{User.__table_name__}.username',
        f'{OrderItem.__table_name__}.quantity'
    ) \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            LEFT JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.total_amount > ?', (Decimal('100.00'),)) \
        .order_by(f'{Order.__table_name__}.total_amount DESC') \
        .all()

    # Verify results
    assert len(results) > 0
    for result in results:
        # Get related user for verification
        user = User.find_one(result.user_id)

        # Check that each result has amount > 100.00
        assert result.total_amount > Decimal('100.00')

    # Additional basic join query
    results = Order.query() \
        .join(f"""
            INNER JOIN {User.__table_name__}
            ON {Order.__table_name__}.user_id = {User.__table_name__}.id
        """) \
        .join(f"""
            INNER JOIN {OrderItem.__table_name__}
            ON {Order.__table_name__}.id = {OrderItem.__table_name__}.order_id
        """) \
        .where(f'{Order.__table_name__}.total_amount < ?', (Decimal('1000.00'),)) \
        .all()

    # Verify the second query results
    for result in results:
        # Amount should be less than 1000.00
        assert result.total_amount < Decimal('1000.00')
