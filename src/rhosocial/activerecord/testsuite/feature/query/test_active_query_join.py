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
        assert len(results) > 0  # Should return users with active orders

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
        assert len(results) > 0  # Should return users who have posts with comments

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
        assert len(results) > 0  # Should return ordered results

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
        assert len(results) > 0  # Should return paginated results