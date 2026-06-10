# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_with_one.py
"""Test eager loading using one() method.

Verifies that relations configured via with_() are eagerly loaded when using one().
"""
from decimal import Decimal

import pytest


class TestSyncEagerLoadingWithOne:
    """Sync: verify with_('relation').one() preloads related data.

    Scenarios:
    - BelongsTo (Order -> User)
    - BelongsTo on a different model (Post -> User)
    - No match returns None (not an error)
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
        """Same eager-loading behaviour on a different model pair (Post -> User)."""
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


class TestAsyncEagerLoadingWithOne:
    """Async: verify with_('relation').one() — same behaviour as sync.

    Must mirror every scenario in TestSyncEagerLoadingWithOne.
    """

    async def test_belongs_to(self, async_combined_fixtures):
        """AsyncOrder.with_('user').one() should preload the User relation."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_one', email='aela_one@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-ONE-001', total_amount=Decimal('100'))
        await order.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None
        assert result.id == order.id
        related = await result.user()
        assert related is not None
        assert related.id == user.id

    async def test_with_post_belongs_to(self, async_combined_fixtures):
        """Same eager-loading on a different async model pair (AsyncPost -> author).

        AsyncPost uses 'author' relation. The async_combined_fixtures configures
        all models (including AsyncPost) with the same shared backend, so eager
        loading via with_('author') + one() should work identically to sync.
        """
        AsyncUser, _, _, AsyncPost, _ = async_combined_fixtures
        user = AsyncUser(username='aela_one_post', email='aela_one_post@example.com', age=30)
        await user.save()
        post = AsyncPost(title='One Test', content='Content', user_id=user.id, status='published')
        await post.save()

        result = await AsyncPost.query().with_('author').where(AsyncPost.c.id == post.id).one()
        assert result is not None
        related = await result.author()
        assert related is not None
        assert related.id == user.id

    async def test_none_result(self, async_combined_fixtures):
        """with_().one() should return None when no records match (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).one()
        assert result is None
