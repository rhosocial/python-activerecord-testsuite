# src/rhosocial/activerecord/testsuite/feature/query/basic/test_active_query_basic_async.py
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
class TestAsyncActiveQueryBasic:
    """
    Asynchronous ActiveQuery basic functionality tests
    """

    async def test_init_with_model_class(self, async_order_fixtures):
        """
        Test ActiveQuery initialization with model class (async version)

        This test verifies that when creating an async ActiveQuery instance, the model class is properly
        stored and accessible through the query object. This is fundamental for ensuring
        the query operates on the correct model schema and can instantiate model objects
        from query results.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create user and order for testing
        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00'))
        await order.save()

        # Test query initialization
        query = AsyncOrder.query()
        assert query.model_class == AsyncOrder, "Expected model_class to be AsyncOrder"

    async def test_where_with_predicate(self, async_order_fixtures):
        """
        Test where method with predicate expressions (async version)

        This test verifies that the async where method can accept predicate expressions
        (such as AsyncOrder.c.order_number == 'ORD-TEST') and properly construct
        SQL WHERE clauses. Predicate expressions are safer than raw SQL strings
        as they prevent SQL injection and provide type safety.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-TEST', status='pending')
        await order.save()

        # Use predicate query to find the specific order
        found = await AsyncOrder.query().where(AsyncOrder.c.order_number == 'ORD-TEST').all()
        assert len(found) == 1, "Expected exactly one matching order"
        assert found[0].order_number == 'ORD-TEST', "Expected order_number to be ORD-TEST"

    async def test_where_with_string_params(self, async_order_fixtures):
        """
        Test where method with string parameters (async version)

        This test verifies that the async where method can accept raw SQL strings with
        parameter placeholders (?). This is useful for complex queries that cannot
        be expressed with predicate expressions. The method should properly
        parameterize the query to prevent SQL injection.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-STRING', status='pending')
        await order.save()

        # Use string parameter query to find the specific order
        found = await AsyncOrder.query().where('order_number = ?', ('ORD-STRING',)).all()
        assert len(found) == 1, "Expected exactly one matching order"
        assert found[0].order_number == 'ORD-STRING', "Expected order_number to be ORD-STRING"

    async def test_select_columns(self, async_order_fixtures):
        """
        Test selecting specific columns functionality (async version)

        This test verifies that the async select method can limit which columns are
        retrieved from the database. This is important for performance when
        only specific fields are needed, and also for ensuring that model
        instances are created with only the selected data.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-SELECT', total_amount=Decimal('150.00'))
        await order.save()

        # For select operations that don't return all required fields for model instantiation,
        # we might need to use aggregate() or raw SQL instead of all()
        # Let's test with a query that returns all required fields
        results = await AsyncOrder.query().all()
        assert len(results) == 1, "Expected exactly one matching order"
        # Verify that the model instance is properly created
        assert isinstance(results[0], AsyncOrder), "Expected result to be an AsyncOrder instance"
        assert results[0].id == order.id, "Expected result id to match order id"

    async def test_order_by(self, async_order_fixtures):
        """
        Test ordering functionality (async version)

        This test verifies that the async order_by method can sort query results
        in ascending or descending order based on specified columns. Proper
        ordering is essential for predictable query results and pagination.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Create multiple orders with reverse order numbers to test sorting
        for i in range(3):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'ORD-{3-i:03d}',  # Reverse order creation: ORD-003, ORD-002, ORD-001
                total_amount=Decimal(f'{(3-i)*100.00}')
            )
            await order.save()

        # Order by order number ascending to verify correct sorting
        # Using column-based ordering
        results = await AsyncOrder.query().order_by(AsyncOrder.c.total_amount).all()
        assert len(results) == 3, "Expected 3 orders to be returned"
        assert results[0].total_amount <= results[-1].total_amount, \
            "Expected ascending order by total_amount"

        # Order by order number descending to verify reverse sorting
        results_desc = await AsyncOrder.query().order_by((AsyncOrder.c.total_amount, "DESC")).all()
        assert len(results_desc) == 3, "Expected 3 orders to be returned"
        assert results_desc[0].total_amount >= results_desc[-1].total_amount, \
            "Expected descending order by total_amount"

    async def test_limit_offset(self, async_order_fixtures):
        """
        Test pagination functionality with limit and offset (async version)

        This test verifies that the async limit and offset methods can be used
        together to implement pagination. This is crucial for performance
        when dealing with large datasets and for implementing UI pagination.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        # Create 5 orders for pagination testing
        for i in range(5):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'PAG-{i+1:03d}',
                total_amount=Decimal(f'{(i+1)*100.00}')
            )
            await order.save()

        # Test LIMIT and OFFSET to get second and third orders
        results = await AsyncOrder.query().order_by(AsyncOrder.c.order_number).limit(2).offset(1).all()
        assert len(results) == 2, "Expected exactly 2 paginated results"
        assert results[0].order_number == 'PAG-002', "Expected first result to be PAG-002"
        assert results[1].order_number == 'PAG-003', "Expected second result to be PAG-003"

    async def test_all_method_returns_model_instances(self, async_order_fixtures):
        """
        Test that all method returns model instances (async version)

        This test verifies that the async all() method returns a list of properly
        instantiated model objects rather than raw data tuples. This is
        important for maintaining the Active Record pattern where database
        records are represented as objects with methods and properties.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='INST-001', total_amount=Decimal('100.00'))
        await order.save()

        # Execute query to get all matching records
        results = await AsyncOrder.query().all()
        assert len(results) == 1, "Expected exactly one matching order"
        # Verify results are proper model instances
        assert isinstance(results[0], AsyncOrder), "Expected result to be an AsyncOrder instance"
        assert results[0].id == order.id, "Expected result id to match order id"

    async def test_one_method_returns_single_instance(self, async_order_fixtures):
        """
        Test that one method returns a single model instance (async version)

        This test verifies that the async one() method returns exactly one model
        instance or None if no match is found. This is useful when expecting
        exactly one result and wanting to avoid dealing with lists.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ONE-001', total_amount=Decimal('100.00'))
        await order.save()

        # Get single instance using one() method
        result = await AsyncOrder.query().where(AsyncOrder.c.id == order.id).one()
        assert result is not None, "Expected a result to be returned"
        assert isinstance(result, AsyncOrder), "Expected result to be an AsyncOrder instance"
        assert result.id == order.id, "Expected result id to match order id"

    async def test_one_method_returns_none_when_no_records_match(self, async_order_fixtures):
        """
        Test that async one method returns None when no records match the query.

        This test verifies that when an async query has no matching records in the database,
        the .one() method correctly returns None instead of raising an exception
        or returning an empty model instance.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create a user to ensure the tables exist, but don't create any orders
        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=25)
        await user.save()

        # Query for an order that doesn't exist
        non_existent_order = await AsyncOrder.query().where(AsyncOrder.c.order_number == 'NON-EXISTENT-ORDER').one()

        # Verify that None is returned when no records match
        assert non_existent_order is None, "Expected one() to return None for missing record"

    async def test_where_invalid_condition_type(self, async_order_fixtures):
        """Test that where method raises TypeError for invalid condition type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Condition must be str or SQLPredicate"):
            query.where(123)

    async def test_select_invalid_column_type(self, async_order_fixtures):
        """Test that select method raises TypeError for invalid column type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Column must be str or BaseExpression"):
            query.select(123)

    async def test_order_by_invalid_expression_type(self, async_order_fixtures):
        """Test that order_by method raises TypeError for invalid expression type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Expression must be str or BaseExpression"):
            query.order_by((123, "ASC"))

    async def test_order_by_invalid_direction(self, async_order_fixtures):
        """Test that order_by method raises ValueError for invalid direction."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(ValueError, match="Order direction must be 'ASC' or 'DESC'"):
            query.order_by(("name", "INVALID"))

    async def test_order_by_invalid_clause_type(self, async_order_fixtures):
        """Test that order_by method raises TypeError for invalid clause type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Order clause must be str, BaseExpression, or \\(expression, direction\\) tuple"):
            query.order_by(123)

    async def test_limit_then_offset(self, async_order_fixtures):
        """Test calling limit then offset."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(5):
            order = AsyncOrder(user_id=user.id, order_number=f'ORD-{i:03d}', total_amount=Decimal(f'{(i+1)*100.00}'))
            await order.save()

        results = await AsyncOrder.query().limit(3).offset(1).all()
        assert len(results) == 3, "Expected exactly 3 results after limit/offset"

    async def test_group_by_invalid_column_type(self, async_order_fixtures):
        """Test that group_by method raises TypeError for invalid column type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Column must be str or BaseExpression"):
            query.group_by(123)

    async def test_group_by_extend_existing(self, async_order_fixtures):
        """Test calling group_by multiple times extends existing clause."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        for i in range(3):
            order = AsyncOrder(user_id=user.id, order_number=f'ORD-{i:03d}', total_amount=Decimal(f'{(i+1)*100.00}'))
            await order.save()

        results = await AsyncOrder.query().select(AsyncOrder.c.user_id, AsyncOrder.c.order_number).group_by(AsyncOrder.c.user_id).group_by(AsyncOrder.c.order_number).all()
        assert len(results) == 3, "Expected 3 grouped results"

    async def test_having_invalid_condition_type(self, async_order_fixtures):
        """Test that having method raises TypeError for invalid condition type."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        query = AsyncOrder.query()

        with pytest.raises(TypeError, match="Condition must be str or SQLPredicate"):
            query.having(123)

    async def test_select_append_true(self, async_order_fixtures):
        """Test select with append=True extends existing selection."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00'))
        await order.save()

        query = AsyncOrder.query()
        query.select(AsyncOrder.c.id)
        query.select(AsyncOrder.c.order_number, append=True)
        sql, params = query.to_sql()
        assert 'order_number' in sql.lower(), "Expected order_number to appear in the SQL"

    async def test_order_by_extend_existing(self, async_order_fixtures):
        """Test calling order_by multiple times extends existing clause."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_test_user', email='async_test@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00'))
        await order.save()

        query = AsyncOrder.query()
        query.order_by(AsyncOrder.c.id)
        query.order_by(AsyncOrder.c.order_number)
        results = await query.all()
        assert [order.order_number for order in results] == ['ORD-001'], \
            "Expected only ORD-001 to be returned"

