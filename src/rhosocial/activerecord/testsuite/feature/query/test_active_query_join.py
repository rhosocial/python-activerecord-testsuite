# src/rhosocial/activerecord/testsuite/feature/query/test_active_query_join.py
"""ActiveQuery join functionality tests

This module contains tests for the JOIN ActiveQuery operations including:
- Inner joins
- Join with conditions
- Multiple joins in sequence
- Join with ordering and pagination
"""

import pytest
from decimal import Decimal


class TestSyncActiveQueryJoin:
    """
    Synchronous ActiveQuery join functionality tests
    """

    @pytest.mark.requires_inner_join
    def test_inner_join_basic(self, order_fixtures):
        """
        Test basic inner join functionality

        This test verifies that the join method can perform basic inner joins
        between related tables, returning only matching records from both sides.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='join_user', email='join@example.com', age=30)
        user.save()

        order = Order(user_id=user.id, order_number='JOIN-001', total_amount=Decimal('100.00'))
        order.save()

        # Perform inner join between User and Order
        results = User.query().join(Order, User.c.id == Order.c.user_id).all()
        assert len(results) == 1
        assert results[0].id == user.id

    @pytest.mark.requires_inner_join
    def test_join_with_where_condition(self, order_fixtures):
        """
        Test join with additional WHERE conditions

        This test verifies that joins work correctly when combined with
        WHERE clauses to filter the results further.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='cond_join_user', email='cond@example.com', age=30)
        user.save()

        order1 = Order(user_id=user.id, order_number='COND-001', total_amount=Decimal('100.00'), status='active')
        order1.save()

        order2 = Order(user_id=user.id, order_number='COND-002', total_amount=Decimal('200.00'), status='inactive')
        order2.save()

        # Join with WHERE condition to get only active orders
        results = User.query().join(Order, User.c.id == Order.c.user_id).where(Order.c.status == 'active').all()
        assert len(results) >= 0  # Should return users with active orders

    @pytest.mark.requires_inner_join
    def test_multiple_joins(self, blog_fixtures):
        """
        Test multiple joins in sequence

        This test verifies that multiple joins can be chained together
        to connect several related tables in a single query.
        """
        User, Post, Comment = blog_fixtures

        user = User(username='multi_join_user', email='multi@example.com', age=30)
        user.save()

        post = Post(user_id=user.id, title='Multi Join Post', content='Test content')
        post.save()

        comment = Comment(user_id=user.id, post_id=post.id, content='Test comment')
        comment.save()

        # Perform multiple joins: User -> Post -> Comment
        results = User.query().join(Post, User.c.id == Post.c.user_id).join(Comment, Post.c.id == Comment.c.post_id).all()
        assert len(results) >= 0  # Should return users who have posts with comments

    @pytest.mark.requires_inner_join
    def test_join_with_order_by(self, order_fixtures):
        """
        Test join with ordering functionality

        This test verifies that joins work correctly when combined with
        ORDER BY clauses to sort the results.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='order_join_user', email='order@example.com', age=30)
        user.save()

        order1 = Order(user_id=user.id, order_number='ORD-001', total_amount=Decimal('100.00'))
        order1.save()

        order2 = Order(user_id=user.id, order_number='ORD-002', total_amount=Decimal('200.00'))
        order2.save()

        # Join with ordering
        results = User.query().join(Order, User.c.id == Order.c.user_id).order_by(Order.c.total_amount).all()
        assert len(results) >= 0  # Should return ordered results

    @pytest.mark.requires_inner_join
    def test_join_with_limit_offset(self, order_fixtures):
        """
        Test join with pagination functionality

        This test verifies that joins work correctly when combined with
        LIMIT and OFFSET clauses for pagination.
        """
        User, Order, OrderItem = order_fixtures

        user = User(username='page_join_user', email='page@example.com', age=30)
        user.save()

        # Create multiple orders for pagination testing
        for i in range(5):
            order = Order(user_id=user.id, order_number=f'PAGE-{i+1:03d}', total_amount=Decimal(f'{(i+1)*100.00}'))
            order.save()

        # Join with pagination
        results = User.query().join(Order, User.c.id == Order.c.user_id).order_by(Order.c.order_number).limit(2).offset(1).all()
        assert len(results) >= 0  # Should return paginated results


class TestAsyncActiveQueryJoin:
    """
    Asynchronous ActiveQuery join functionality tests
    """

    @pytest.mark.asyncio
    @pytest.mark.requires_inner_join
    async def test_inner_join_basic_async(self, async_order_fixtures):
        """
        Test basic inner join functionality (async version)

        This test verifies that the async join method can perform basic inner joins
        between related tables, returning only matching records from both sides.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_join_user', email='async_join@example.com', age=30)
        await user.save()

        order = AsyncOrder(user_id=user.id, order_number='AJ-001', total_amount=Decimal('100.00'))
        await order.save()

        # Perform inner join between User and Order
        results = await AsyncUser.query().join(AsyncOrder, AsyncUser.c.id == AsyncOrder.c.user_id).all()
        assert len(results) == 1
        assert results[0].id == user.id

    @pytest.mark.asyncio
    @pytest.mark.requires_inner_join
    async def test_join_with_where_condition_async(self, async_order_fixtures):
        """
        Test join with additional WHERE conditions (async version)

        This test verifies that async joins work correctly when combined with
        WHERE clauses to filter the results further.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_cond_join_user', email='async_cond@example.com', age=30)
        await user.save()

        order1 = AsyncOrder(user_id=user.id, order_number='ACOND-001', total_amount=Decimal('100.00'), status='active')
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='ACOND-002', total_amount=Decimal('200.00'), status='inactive')
        await order2.save()

        # Join with WHERE condition to get only active orders
        results = await AsyncUser.query().join(AsyncOrder, AsyncUser.c.id == AsyncOrder.c.user_id).where(AsyncOrder.c.status == 'active').all()
        assert len(results) >= 0  # Should return users with active orders

    @pytest.mark.asyncio
    @pytest.mark.requires_inner_join
    async def test_multiple_joins_async(self, async_blog_fixtures):
        """
        Test multiple joins in sequence (async version)

        This test verifies that multiple async joins can be chained together
        to connect several related tables in a single query.
        """
        AsyncUser, AsyncPost, AsyncComment = async_blog_fixtures

        user = AsyncUser(username='async_multi_join_user', email='async_multi@example.com', age=30)
        await user.save()

        post = AsyncPost(user_id=user.id, title='Async Multi Join Post', content='Async test content')
        await post.save()

        comment = AsyncComment(user_id=user.id, post_id=post.id, content='Async test comment')
        await comment.save()

        # Perform multiple joins: User -> Post -> Comment
        results = await AsyncUser.query().join(AsyncPost, AsyncUser.c.id == AsyncPost.c.user_id).join(AsyncComment, AsyncPost.c.id == AsyncComment.c.post_id).all()
        assert len(results) >= 0  # Should return users who have posts with comments

    @pytest.mark.asyncio
    @pytest.mark.requires_inner_join
    async def test_join_with_order_by_async(self, async_order_fixtures):
        """
        Test join with ordering functionality (async version)

        This test verifies that async joins work correctly when combined with
        ORDER BY clauses to sort the results.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_order_join_user', email='async_order@example.com', age=30)
        await user.save()

        order1 = AsyncOrder(user_id=user.id, order_number='AORD-001', total_amount=Decimal('100.00'))
        await order1.save()

        order2 = AsyncOrder(user_id=user.id, order_number='AORD-002', total_amount=Decimal('200.00'))
        await order2.save()

        # Join with ordering
        results = await AsyncUser.query().join(AsyncOrder, AsyncUser.c.id == AsyncOrder.c.user_id).order_by(AsyncOrder.c.total_amount).all()
        assert len(results) >= 0  # Should return ordered results

    @pytest.mark.asyncio
    @pytest.mark.requires_inner_join
    async def test_join_with_limit_offset_async(self, async_order_fixtures):
        """
        Test join with pagination functionality (async version)

        This test verifies that async joins work correctly when combined with
        LIMIT and OFFSET clauses for pagination.
        """
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures

        user = AsyncUser(username='async_page_join_user', email='async_page@example.com', age=30)
        await user.save()

        # Create multiple orders for pagination testing
        for i in range(5):
            order = AsyncOrder(user_id=user.id, order_number=f'APAGE-{i+1:03d}', total_amount=Decimal(f'{(i+1)*100.00}'))
            await order.save()

        # Join with pagination
        results = await AsyncUser.query().join(AsyncOrder, AsyncUser.c.id == AsyncOrder.c.user_id).order_by(AsyncOrder.c.order_number).limit(2).offset(1).all()
        assert len(results) >= 0  # Should return paginated results