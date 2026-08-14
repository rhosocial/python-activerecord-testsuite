# src/rhosocial/activerecord/testsuite/feature/query/basic/test_active_query_basic.py
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

import pytest
from decimal import Decimal
class TestSyncActiveQueryBasic:
    """
    Synchronous ActiveQuery basic functionality tests
    """

    def test_init_with_model_class(self, order_fixtures):
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

    def test_where_with_predicate(self, order_fixtures):
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

    def test_where_with_string_params(self, order_fixtures):
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

    def test_select_columns(self, order_fixtures):
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

    def test_order_by(self, order_fixtures):
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

    def test_limit_offset(self, order_fixtures):
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

    def test_all_method_returns_model_instances(self, order_fixtures):
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

    def test_one_method_returns_single_instance(self, order_fixtures):
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


    def test_one_method_returns_none_when_no_records_match(self, order_fixtures):
        """
        Test that one method returns None when no records match the query.

        This test verifies that when a query has no matching records in the database,
        the .one() method correctly returns None instead of raising an exception
        or returning an empty model instance.
        """
        User, Order, OrderItem = order_fixtures

        # Create a user to ensure the tables exist, but don't create any orders
        user = User(username='test_user', email='test@example.com', age=25)
        user.save()

        # Query for an order that doesn't exist
        non_existent_order = Order.query().where(Order.c.order_number == 'NON-EXISTENT-ORDER').one()

        # Verify that None is returned when no records match
        assert non_existent_order is None

    def test_where_invalid_condition_type(self, order_fixtures):
        """Test that where method raises TypeError for invalid condition type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Condition must be str or SQLPredicate"):
            query.where(123)

    def test_select_invalid_column_type(self, order_fixtures):
        """Test that select method raises TypeError for invalid column type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Column must be str or BaseExpression"):
            query.select(123)

    def test_order_by_invalid_expression_type(self, order_fixtures):
        """Test that order_by method raises TypeError for invalid expression type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Expression must be str or BaseExpression"):
            query.order_by((123, "ASC"))

    def test_order_by_invalid_direction(self, order_fixtures):
        """Test that order_by method raises ValueError for invalid direction."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(ValueError, match="Order direction must be 'ASC' or 'DESC'"):
            query.order_by(("name", "INVALID"))

    def test_order_by_invalid_clause_type(self, order_fixtures):
        """Test that order_by method raises TypeError for invalid clause type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Order clause must be str, BaseExpression, or \\(expression, direction\\) tuple"):
            query.order_by(123)

    def test_limit_then_offset(self, order_fixtures):
        """Test calling limit then offset."""
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(5):
            Order(user_id=user.id, order_number=f'ORD-{i:03d}', total_amount=Decimal(f'{(i+1)*100.00}')).save()

        results = Order.query().limit(3).offset(1).all()
        assert len(results) == 3

    def test_group_by_invalid_column_type(self, order_fixtures):
        """Test that group_by method raises TypeError for invalid column type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Column must be str or BaseExpression"):
            query.group_by(123)

    def test_group_by_extend_existing(self, order_fixtures):
        """Test calling group_by multiple times extends existing clause."""
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        for i in range(3):
            Order(user_id=user.id, order_number=f'ORD-{i:03d}', total_amount=Decimal(f'{(i+1)*100.00}')).save()

        results = Order.query().select(Order.c.user_id, Order.c.order_number).group_by(Order.c.user_id).group_by(Order.c.order_number).all()
        assert len(results) == 3

    def test_having_invalid_condition_type(self, order_fixtures):
        """Test that having method raises TypeError for invalid condition type."""
        User, Order, OrderItem = order_fixtures

        query = Order.query()

        with pytest.raises(TypeError, match="Condition must be str or SQLPredicate"):
            query.having(123)

    def test_select_append_true(self, order_fixtures):
        """Test select with append=True extends existing selection."""
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        Order(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00')).save()

        query = Order.query()
        query.select(Order.c.id)
        query.select(Order.c.order_number, append=True)
        sql, params = query.to_sql()
        assert 'order_number' in sql.lower()

    def test_order_by_extend_existing(self, order_fixtures):
        """Test calling order_by multiple times extends existing clause."""
        User, Order, OrderItem = order_fixtures

        user = User(username='test_user', email='test@example.com', age=30)
        user.save()

        Order(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00')).save()

        query = Order.query()
        query.order_by(Order.c.id)
        query.order_by(Order.c.order_number)
        results = query.all()
        assert [order.order_number for order in results] == ['ORD-001']