# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_with_one.py
"""Test eager loading using one() method.

Verifies that relations configured via with_() are eagerly loaded when using one().
"""
from decimal import Decimal

import pytest
class TestSyncEagerLoadingWithOne:
    """Sync: verify with_('relation').one() — same behaviour as async.

    Must mirror every scenario in TestAsyncEagerLoadingWithOne.
    """

    def test_belongs_to(self, combined_fixtures):
        """Order.with_('user').one() should return a record whose .user() is preloaded."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_one', email='ela_one@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-ONE-001', total_amount=Decimal('100'))
        order.save()

        result = Order.query().with_('user').where(Order.c.id == order.id).one()
        assert result is not None
        assert result.id == order.id
        related = result.user()
        assert related is not None
        assert related.id == user.id
        assert related.username == 'ela_one'

    def test_with_post_belongs_to(self, combined_fixtures):
        """Same eager-loading on a different model pair (Post -> User).

        Post uses 'user' relation. The combined_fixtures configures
        all models (including Post) with the same shared backend, so eager
        loading via with_('user') + one() should work identically to async.
        """
        User, _, _, Post, _ = combined_fixtures
        user = User(username='ela_one_post', email='ela_one_post@example.com', age=30)
        user.save()
        post = Post(title='One Test', content='Content', user_id=user.id, status='published')
        post.save()

        result = Post.query().with_('user').where(Post.c.id == post.id).one()
        assert result is not None
        related = result.user()
        assert related is not None
        assert related.id == user.id

    def test_none_result(self, combined_fixtures):
        """with_().one() should return None when no records match."""
        User, Order, _, _, _ = combined_fixtures
        result = Order.query().with_('user').where(Order.c.id == -1).one()
        assert result is None