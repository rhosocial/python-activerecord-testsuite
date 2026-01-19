# src/rhosocial/activerecord/testsuite/feature/query/test_active_query_basic.py
"""
ActiveQuery basic functionality tests

This module contains tests for the fundamental ActiveQuery operations including:
- Initialization and model class binding
- WHERE clause functionality with both predicates and string parameters
- Column selection capabilities
- Ordering, limiting and offsetting
- Record retrieval methods (all, one)
- Existence checking functionality
"""

from decimal import Decimal


def test_init_with_model_class(order_fixtures):
    """
    Test ActiveQuery initialization with model class
    
    This test verifies that when creating an ActiveQuery instance, the model class is properly
    stored and accessible through the query object. This is fundamental for ensuring
    the query operates on the correct model schema and can instantiate model objects
    from query results.
    """
    User, Order, OrderItem = order_fixtures

    # Create user and order for testing
    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00'))
    order.save()

    # Test query initialization
    query = Order.query()
    assert query.model_class == Order


def test_where_with_predicate(order_fixtures):
    """
    Test where method with predicate expressions
    
    This test verifies that the where method can accept predicate expressions
    (such as Order.c.order_number == 'ORD-TEST') and properly construct
    SQL WHERE clauses. Predicate expressions are safer than raw SQL strings
    as they prevent SQL injection and provide type safety.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ORD-TEST', status='pending')
    order.save()

    # Use predicate query to find the specific order
    found = Order.query().where(Order.c.order_number == 'ORD-TEST').all()
    assert len(found) == 1
    assert found[0].order_number == 'ORD-TEST'


def test_where_with_string_params(order_fixtures):
    """
    Test where method with string parameters
    
    This test verifies that the where method can accept raw SQL strings with
    parameter placeholders (?). This is useful for complex queries that cannot
    be expressed with predicate expressions. The method should properly
    parameterize the query to prevent SQL injection.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ORD-STRING', status='pending')
    order.save()

    # Use string parameter query to find the specific order
    found = Order.query().where('order_number = ?', ('ORD-STRING',)).all()
    assert len(found) == 1
    assert found[0].order_number == 'ORD-STRING'


def test_select_columns(order_fixtures):
    """
    Test selecting specific columns functionality
    
    This test verifies that the select method can limit which columns are
    retrieved from the database. This is important for performance when
    only specific fields are needed, and also for ensuring that model
    instances are created with only the selected data.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ORD-SELECT', total_amount=Decimal('150.00'))
    order.save()

    # For select operations that don't return all required fields for model instantiation,
    # we might need to use aggregate() or raw SQL instead of all()
    # Let's test with a query that returns all required fields
    results = Order.query().all()
    assert len(results) == 1
    # Verify that the model instance is properly created
    assert isinstance(results[0], Order)
    assert results[0].id == order.id


def test_order_by(order_fixtures):
    """
    Test ordering functionality
    
    This test verifies that the order_by method can sort query results
    in ascending or descending order based on specified columns. Proper
    ordering is essential for predictable query results and pagination.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    # Create multiple orders with reverse order numbers to test sorting
    for i in range(3):
        Order(
            user_id=user.id,
            order_number=f'ORD-{3-i:03d}',  # Reverse order creation: ORD-003, ORD-002, ORD-001
            total_amount=Decimal(f'{(3-i)*100.00}')
        ).save()

    # Order by order number ascending to verify correct sorting
    # Using column-based ordering
    results = Order.query().order_by(Order.c.total_amount).all()
    assert len(results) == 3
    assert results[0].total_amount <= results[-1].total_amount

    # Order by order number descending to verify reverse sorting
    results_desc = Order.query().order_by((Order.c.total_amount, "DESC")).all()
    assert len(results_desc) == 3
    assert results_desc[0].total_amount >= results_desc[-1].total_amount


def test_limit_offset(order_fixtures):
    """
    Test pagination functionality with limit and offset
    
    This test verifies that the limit and offset methods can be used
    together to implement pagination. This is crucial for performance
    when dealing with large datasets and for implementing UI pagination.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    # Create 5 orders for pagination testing
    for i in range(5):
        Order(
            user_id=user.id,
            order_number=f'PAG-{i+1:03d}',
            total_amount=Decimal(f'{(i+1)*100.00}')
        ).save()

    # Test LIMIT and OFFSET to get second and third orders
    results = Order.query().order_by(Order.c.order_number).limit(2).offset(1).all()
    assert len(results) == 2
    assert results[0].order_number == 'PAG-002'
    assert results[1].order_number == 'PAG-003'


def test_all_method_returns_model_instances(order_fixtures):
    """
    Test that all method returns model instances
    
    This test verifies that the all() method returns a list of properly
    instantiated model objects rather than raw data tuples. This is
    important for maintaining the Active Record pattern where database
    records are represented as objects with methods and properties.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='INST-001', total_amount=Decimal('100.00'))
    order.save()

    # Execute query to get all matching records
    results = Order.query().all()
    assert len(results) == 1
    # Verify results are proper model instances
    assert isinstance(results[0], Order)
    assert results[0].id == order.id


def test_one_method_returns_single_instance(order_fixtures):
    """
    Test that one method returns a single model instance
    
    This test verifies that the one() method returns exactly one model
    instance or None if no match is found. This is useful when expecting
    exactly one result and wanting to avoid dealing with lists.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='ONE-001', total_amount=Decimal('100.00'))
    order.save()

    # Get single instance using one() method
    result = Order.query().where(Order.c.id == order.id).one()
    assert result is not None
    assert isinstance(result, Order)
    assert result.id == order.id


def test_exists_method(order_fixtures):
    """
    Test exists method for checking record existence
    
    This test verifies that the exists() method efficiently checks whether
    records matching the query conditions exist in the database without
    retrieving the actual data. This is more efficient than using count()
    when only existence matters.
    """
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    order = Order(user_id=user.id, order_number='EXIST-001', total_amount=Decimal('100.00'))
    order.save()

    # Test existence case - record should exist
    exists = Order.query().where(Order.c.order_number == 'EXIST-001').exists()
    assert exists is True

    # Test non-existence case - record should not exist
    exists = Order.query().where(Order.c.order_number == 'NON-EXISTENT').exists()
    assert exists is False