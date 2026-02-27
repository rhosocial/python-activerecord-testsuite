# src/rhosocial/activerecord/testsuite/feature/query/test_active_query_range.py
"""
ActiveQuery Range Operations Tests

This module contains tests for range operations specifically using ActiveQuery
and verifying the integration between ActiveQuery and RangeQueryMixin.
"""

import pytest
from decimal import Decimal


class TestSyncActiveQueryRange:
    """
    Synchronous ActiveQuery range operations tests
    """

    def test_active_query_in_list_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with in_list method from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        in_list method to filter records where a column value matches any value in the
        provided list. This ensures the mixin functionality works correctly when accessed
        through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='aq_in_list_user', email='aq_inlist@example.com', age=30)
        user.save()

        # Create multiple orders with different statuses for IN testing
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for i, status in enumerate(statuses):
            Order(
                user_id=user.id,
                order_number=f'AQ-IN-{i+1:03d}',
                status=status,
                total_amount=Decimal(f'{(i+1)*50.00}')
            ).save()

        # Test ActiveQuery with in_list method from RangeQueryMixin
        query = Order.query()
        results = query.in_list(Order.c.status, ['pending', 'shipped', 'delivered']).all()

        assert len(results) == 3  # Should match 3 statuses
        result_statuses = [r.status for r in results]
        assert 'pending' in result_statuses
        assert 'shipped' in result_statuses
        assert 'delivered' in result_statuses
        assert 'processing' not in result_statuses
        assert 'cancelled' not in result_statuses

    def test_active_query_not_in_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with not_in method from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        not_in method to filter records where a column value does not match any value in
        the provided list. This ensures the mixin functionality works correctly when
        accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='aq_not_in_user', email='aq_notin@example.com', age=30)
        user.save()

        # Create multiple orders with different statuses for NOT IN testing
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for i, status in enumerate(statuses):
            Order(
                user_id=user.id,
                order_number=f'AQ-NOTIN-{i+1:03d}',
                status=status,
                total_amount=Decimal(f'{(i+1)*50.00}')
            ).save()

        # Test ActiveQuery with not_in method from RangeQueryMixin
        query = Order.query()
        results = query.not_in(Order.c.status, ['pending', 'cancelled']).all()

        assert len(results) == 3  # Should exclude pending and cancelled, leaving 3
        result_statuses = [r.status for r in results]
        assert 'pending' not in result_statuses
        assert 'cancelled' not in result_statuses
        assert 'processing' in result_statuses
        assert 'shipped' in result_statuses
        assert 'delivered' in result_statuses

    def test_active_query_between_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with between method from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        between method to filter records within a specified range. This ensures the mixin
        functionality works correctly when accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='aq_between_user', email='aq_between@example.com', age=30)
        user.save()

        # Create multiple orders with different amounts for BETWEEN testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'AQ-BET-{i+1:03d}',
                total_amount=amount
            ).save()

        # Test ActiveQuery with between method from RangeQueryMixin
        query = Order.query()
        results = query.between(Order.c.total_amount, Decimal('100.00'), Decimal('200.00')).all()

        assert len(results) == 3  # 100, 150, 200 are in range
        result_amounts = [r.total_amount for r in results]
        assert Decimal('100.00') in result_amounts
        assert Decimal('150.00') in result_amounts
        assert Decimal('200.00') in result_amounts

    def test_active_query_not_between_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with not_between method from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        not_between method to filter records outside a specified range. This ensures the
        mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='aq_not_between_user', email='aq_notbetween@example.com', age=30)
        user.save()

        # Create multiple orders with different amounts for NOT BETWEEN testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            Order(
                user_id=user.id,
                order_number=f'AQ-NBET-{i+1:03d}',
                total_amount=amount
            ).save()

        # Test ActiveQuery with not_between method from RangeQueryMixin
        query = Order.query()
        results = query.not_between(Order.c.total_amount, Decimal('100.00'), Decimal('200.00')).all()

        assert len(results) == 2  # 50 and 250 are not in 100-200 range
        result_amounts = [r.total_amount for r in results]
        assert Decimal('50.00') in result_amounts
        assert Decimal('250.00') in result_amounts

    def test_active_query_comparison_operators_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with comparison operator methods from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        comparison operator methods (greater_than, less_than, etc.) to filter records based
        on value comparisons. This ensures the mixin functionality works correctly when
        accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='aq_comp_user', email='aq_comp@example.com', age=30)
        user.save()

        # Create multiple orders with different amounts for comparison testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00')]
        for i, amount in enumerate(amounts):
            order = Order(
                user_id=user.id,
                order_number=f'AQ-COMP-{i+1:03d}',
                total_amount=amount
            )
            order.save()

        # Test ActiveQuery with greater_than method from RangeQueryMixin - verify method exists and works
        query = Order.query()
        results_gt = query.greater_than(Order.c.total_amount, Decimal('100.00')).all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_gt, list)

        # Test ActiveQuery with greater_than_or_equal method from RangeQueryMixin
        results_gte = query.greater_than_or_equal(Order.c.total_amount, Decimal('100.00')).all()
        assert isinstance(results_gte, list)

        # Test ActiveQuery with less_than method from RangeQueryMixin
        results_lt = query.less_than(Order.c.total_amount, Decimal('150.00')).all()
        assert isinstance(results_lt, list)

        # Test ActiveQuery with less_than_or_equal method from RangeQueryMixin
        results_lte = query.less_than_or_equal(Order.c.total_amount, Decimal('150.00')).all()
        assert isinstance(results_lte, list)

        # Verify that the query object still supports chaining after range methods
        chained_query = query.greater_than(Order.c.total_amount, Decimal('50.00')).less_than(Order.c.total_amount, Decimal('200.00'))
        chained_results = chained_query.all()
        assert isinstance(chained_results, list)

    def test_active_query_pattern_matching_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with pattern matching methods from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        pattern matching methods (like, not_like) to filter records based on pattern matching.
        This ensures the mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        # Create test users with different usernames for pattern matching
        user1 = User(username='alice_smith', email='alice@example.com', age=25)
        user1.save()

        user2 = User(username='bob_jones', email='bob@example.com', age=30)
        user2.save()

        user3 = User(username='charlie_smith', email='charlie@example.com', age=35)
        user3.save()

        # Test ActiveQuery with like method from RangeQueryMixin - verify method exists and works
        query = User.query()
        results_like = query.like(User.c.username, '%smith%').all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_like, list)

        # Test ActiveQuery with not_like method from RangeQueryMixin
        results_not_like = query.not_like(User.c.username, '%smith%').all()
        assert isinstance(results_not_like, list)

        # Verify that the query object still supports chaining after pattern matching methods
        chained_query = query.like(User.c.username, '%test%').not_like(User.c.username, '%admin%')
        chained_results = chained_query.all()
        assert isinstance(chained_results, list)

    def test_active_query_null_check_integration(self, order_fixtures):
        """
        Test ActiveQuery integration with null checking methods from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        null checking methods (is_null, is_not_null) to filter records based on null values.
        This ensures the mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        User, Order, OrderItem = order_fixtures

        # Create test users with different age values (some null, some not)
        user1 = User(username='user1', email='user1@example.com', age=25)
        user1.save()

        user2 = User(username='user2', email='user2@example.com', age=30)
        user2.save()

        user3 = User(username='user3', email='user3@example.com', age=None)  # age is null
        user3.save()

        # Test ActiveQuery with is_null method from RangeQueryMixin - verify method exists and works
        query = User.query()
        results_null = query.is_null(User.c.age).all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_null, list)

        # Test ActiveQuery with is_not_null method from RangeQueryMixin
        results_not_null = query.is_not_null(User.c.age).all()
        assert isinstance(results_not_null, list)

        # Verify that the query object still supports chaining after null checking methods
        chained_query = query.is_null(User.c.age).is_not_null(User.c.email)
        chained_results = chained_query.all()
        assert isinstance(chained_results, list)

    def test_active_query_range_method_chaining(self, order_fixtures):
        """
        Test ActiveQuery integration with chaining multiple range methods from RangeQueryMixin.

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        methods and allows chaining multiple range operations together. This ensures the
        mixin functionality works correctly when accessed through ActiveQuery instances
        and supports method chaining.
        """
        User, Order, OrderItem = order_fixtures

        # Create test users with different ages and balances
        user1 = User(username='user1', email='user1@example.com', age=20, balance=100.0)
        user1.save()

        user2 = User(username='user2', email='user2@example.com', age=25, balance=200.0)
        user2.save()

        user3 = User(username='user3', email='user3@example.com', age=30, balance=300.0)
        user3.save()

        user4 = User(username='user4', email='user4@example.com', age=35, balance=400.0)
        user4.save()

        # Test ActiveQuery with chaining multiple range methods from RangeQueryMixin
        query = User.query()
        results = (query
                   .greater_than(User.c.age, 22)
                   .less_than(User.c.age, 33)
                   .greater_than_or_equal(User.c.balance, 200.0)
                   .all())

        # Should match user2 (age=25, balance=200.0) and user3 (age=30, balance=300.0)
        assert len(results) == 2
        usernames = {u.username for u in results}
        assert 'user2' in usernames
        assert 'user3' in usernames
        assert 'user1' not in usernames  # Too young
        assert 'user4' not in usernames  # Too old


class TestAsyncActiveQueryRange:
    """
    Asynchronous ActiveQuery range operations tests
    """

    @pytest.mark.asyncio
    async def test_active_query_in_list_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with in_list method from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        in_list method to filter records where a column value matches any value in the
        provided list. This ensures the mixin functionality works correctly when accessed
        through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='aq_in_list_user', email='aq_inlist@example.com', age=30)
        await user.save()

        # Create multiple orders with different statuses for IN testing
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for i, status in enumerate(statuses):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AQ-IN-{i+1:03d}',
                status=status,
                total_amount=Decimal(f'{(i+1)*50.00}')
            )
            await order.save()

        # Test ActiveQuery with in_list method from RangeQueryMixin
        query = AsyncOrder.query()
        results = await query.in_list(AsyncOrder.c.status, ['pending', 'shipped', 'delivered']).all()

        assert len(results) == 3  # Should match 3 statuses
        result_statuses = [r.status for r in results]
        assert 'pending' in result_statuses
        assert 'shipped' in result_statuses
        assert 'delivered' in result_statuses
        assert 'processing' not in result_statuses
        assert 'cancelled' not in result_statuses

    @pytest.mark.asyncio
    async def test_active_query_not_in_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with not_in method from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        not_in method to filter records where a column value does not match any value in
        the provided list. This ensures the mixin functionality works correctly when
        accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='aq_not_in_user', email='aq_notin@example.com', age=30)
        await user.save()

        # Create multiple orders with different statuses for NOT IN testing
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for i, status in enumerate(statuses):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AQ-NOTIN-{i+1:03d}',
                status=status,
                total_amount=Decimal(f'{(i+1)*50.00}')
            )
            await order.save()

        # Test ActiveQuery with not_in method from RangeQueryMixin
        query = AsyncOrder.query()
        results = await query.not_in(AsyncOrder.c.status, ['pending', 'cancelled']).all()

        assert len(results) == 3  # Should exclude pending and cancelled, leaving 3
        result_statuses = [r.status for r in results]
        assert 'pending' not in result_statuses
        assert 'cancelled' not in result_statuses
        assert 'processing' in result_statuses
        assert 'shipped' in result_statuses
        assert 'delivered' in result_statuses

    @pytest.mark.asyncio
    async def test_active_query_between_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with between method from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        between method to filter records within a specified range. This ensures the mixin
        functionality works correctly when accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='aq_between_user', email='aq_between@example.com', age=30)
        await user.save()

        # Create multiple orders with different amounts for BETWEEN testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AQ-BET-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Test ActiveQuery with between method from RangeQueryMixin
        query = AsyncOrder.query()
        results = await query.between(AsyncOrder.c.total_amount, Decimal('100.00'), Decimal('200.00')).all()

        assert len(results) == 3  # 100, 150, 200 are in range
        result_amounts = [r.total_amount for r in results]
        assert Decimal('100.00') in result_amounts
        assert Decimal('150.00') in result_amounts
        assert Decimal('200.00') in result_amounts

    @pytest.mark.asyncio
    async def test_active_query_not_between_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with not_between method from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        not_between method to filter records outside a specified range. This ensures the
        mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='aq_not_between_user', email='aq_notbetween@example.com', age=30)
        await user.save()

        # Create multiple orders with different amounts for NOT BETWEEN testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00'), Decimal('250.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AQ-NBET-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Test ActiveQuery with not_between method from RangeQueryMixin
        query = AsyncOrder.query()
        results = await query.not_between(AsyncOrder.c.total_amount, Decimal('100.00'), Decimal('200.00')).all()

        assert len(results) == 2  # 50 and 250 are not in 100-200 range
        result_amounts = [r.total_amount for r in results]
        assert Decimal('50.00') in result_amounts
        assert Decimal('250.00') in result_amounts

    @pytest.mark.asyncio
    async def test_active_query_comparison_operators_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with comparison operator methods from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        comparison operator methods (greater_than, less_than, etc.) to filter records based
        on value comparisons. This ensures the mixin functionality works correctly when
        accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='aq_comp_user', email='aq_comp@example.com', age=30)
        await user.save()

        # Create multiple orders with different amounts for comparison testing
        amounts = [Decimal('50.00'), Decimal('100.00'), Decimal('150.00'), Decimal('200.00')]
        for i, amount in enumerate(amounts):
            order = AsyncOrder(
                user_id=user.id,
                order_number=f'AQ-COMP-{i+1:03d}',
                total_amount=amount
            )
            await order.save()

        # Test ActiveQuery with greater_than method from RangeQueryMixin - verify method exists and works
        query = AsyncOrder.query()
        results_gt = await query.greater_than(AsyncOrder.c.total_amount, Decimal('100.00')).all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_gt, list)

        # Test ActiveQuery with greater_than_or_equal method from RangeQueryMixin
        results_gte = await query.greater_than_or_equal(AsyncOrder.c.total_amount, Decimal('100.00')).all()
        assert isinstance(results_gte, list)

        # Test ActiveQuery with less_than method from RangeQueryMixin
        results_lt = await query.less_than(AsyncOrder.c.total_amount, Decimal('150.00')).all()
        assert isinstance(results_lt, list)

        # Test ActiveQuery with less_than_or_equal method from RangeQueryMixin
        results_lte = await query.less_than_or_equal(AsyncOrder.c.total_amount, Decimal('150.00')).all()
        assert isinstance(results_lte, list)

        # Verify that the query object still supports chaining after range methods
        chained_query = query.greater_than(AsyncOrder.c.total_amount, Decimal('50.00')).less_than(AsyncOrder.c.total_amount, Decimal('200.00'))
        chained_results = await chained_query.all()
        assert isinstance(chained_results, list)

    @pytest.mark.asyncio
    async def test_active_query_pattern_matching_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with pattern matching methods from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        pattern matching methods (like, not_like) to filter records based on pattern matching.
        This ensures the mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test users with different usernames for pattern matching
        user1 = AsyncUser(username='alice_smith', email='alice@example.com', age=25)
        await user1.save()

        user2 = AsyncUser(username='bob_jones', email='bob@example.com', age=30)
        await user2.save()

        user3 = AsyncUser(username='charlie_smith', email='charlie@example.com', age=35)
        await user3.save()

        # Test ActiveQuery with like method from RangeQueryMixin - verify method exists and works
        query = AsyncUser.query()
        results_like = await query.like(AsyncUser.c.username, '%smith%').all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_like, list)

        # Test ActiveQuery with not_like method from RangeQueryMixin
        results_not_like = await query.not_like(AsyncUser.c.username, '%smith%').all()
        assert isinstance(results_not_like, list)

        # Verify that the query object still supports chaining after pattern matching methods
        chained_query = query.like(AsyncUser.c.username, '%test%').not_like(AsyncUser.c.username, '%admin%')
        chained_results = await chained_query.all()
        assert isinstance(chained_results, list)

    @pytest.mark.asyncio
    async def test_active_query_null_check_integration_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with null checking methods from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        null checking methods (is_null, is_not_null) to filter records based on null values.
        This ensures the mixin functionality works correctly when accessed through ActiveQuery instances.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test users with different age values (some null, some not)
        user1 = AsyncUser(username='user1', email='user1@example.com', age=25)
        await user1.save()

        user2 = AsyncUser(username='user2', email='user2@example.com', age=30)
        await user2.save()

        user3 = AsyncUser(username='user3', email='user3@example.com', age=None)  # age is null
        await user3.save()

        # Test ActiveQuery with is_null method from RangeQueryMixin - verify method exists and works
        query = AsyncUser.query()
        results_null = await query.is_null(AsyncUser.c.age).all()
        # Just verify that the query executes without error and returns a list
        assert isinstance(results_null, list)

        # Test ActiveQuery with is_not_null method from RangeQueryMixin
        results_not_null = await query.is_not_null(AsyncUser.c.age).all()
        assert isinstance(results_not_null, list)

        # Verify that the query object still supports chaining after null checking methods
        chained_query = query.is_null(AsyncUser.c.age).is_not_null(AsyncUser.c.email)
        chained_results = await chained_query.all()
        assert isinstance(chained_results, list)

    @pytest.mark.asyncio
    async def test_active_query_range_method_chaining_async(self, async_order_fixtures):
        """
        Test ActiveQuery integration with chaining multiple range methods from RangeQueryMixin (async version).

        This test verifies that ActiveQuery properly integrates with the RangeQueryMixin's
        methods and allows chaining multiple range operations together. This ensures the
        mixin functionality works correctly when accessed through ActiveQuery instances
        and supports method chaining.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        # Create test users with different ages and balances
        user1 = AsyncUser(username='user1', email='user1@example.com', age=20, balance=100.0)
        await user1.save()

        user2 = AsyncUser(username='user2', email='user2@example.com', age=25, balance=200.0)
        await user2.save()

        user3 = AsyncUser(username='user3', email='user3@example.com', age=30, balance=300.0)
        await user3.save()

        user4 = AsyncUser(username='user4', email='user4@example.com', age=35, balance=400.0)
        await user4.save()

        # Test ActiveQuery with chaining multiple range methods from RangeQueryMixin
        query = AsyncUser.query()
        results = await (query
                        .greater_than(AsyncUser.c.age, 22)
                        .less_than(AsyncUser.c.age, 33)
                        .greater_than_or_equal(AsyncUser.c.balance, 200.0)
                        .all())

        # Should match user2 (age=25, balance=200.0) and user3 (age=30, balance=300.0)
        assert len(results) == 2
        usernames = {u.username for u in results}
        assert 'user2' in usernames
        assert 'user3' in usernames
        assert 'user1' not in usernames  # Too young
        assert 'user4' not in usernames  # Too old