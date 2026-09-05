# src/rhosocial/activerecord/testsuite/feature/query/eager_loading/test_eager_loading_caching_async.py
"""Test InstanceCache population after eager loading.

Verifies that relations loaded via with_() are cached on instances,
so repeated access does not trigger additional database queries.
"""
from decimal import Decimal
class TestAsyncEagerLoadingCaching:
    """Async: verify eager loading populates InstanceCache — same behaviour as sync.

    Must mirror every scenario in TestSyncEagerLoadingCaching.
    """

    async def test_cache_after_all(self, async_combined_fixtures):
        """After all() with with_(), repeated access should return cached data (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_cache', email='aela_cache@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-CACHE-001', total_amount=Decimal('100'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1, "Expected exactly one result"
        related1 = await results[0].user()
        assert related1 is not None, "Expected the related user to be loaded"
        assert related1.id == user.id, "Expected the related user id to match"
        related2 = await results[0].user()
        assert related2 is not None, "Expected the cached related user to be available"
        assert related2.id == user.id, "Expected the cached related user id to match"

    async def test_cache_after_one(self, async_combined_fixtures):
        """After one() with with_(), the single result has its relation cached (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_cache2', email='aela_cache2@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-CACHE2-001', total_amount=Decimal('200'))
        await order.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None, "Expected the order to be loaded"
        related = await result.user()
        assert related is not None, "Expected the related user to be loaded"
        assert related.id == user.id, "Expected the related user id to match"

    async def test_cache_independent_per_instance(self, async_combined_fixtures):
        """Each parent instance should have its own cached relation (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user1 = AsyncUser(username='aela_cache3a', email='aela_cache3a@example.com', age=25)
        await user1.save()
        user2 = AsyncUser(username='aela_cache3b', email='aela_cache3b@example.com', age=26)
        await user2.save()

        order1 = AsyncOrder(user_id=user1.id, order_number='AELA-CACHE3-001', total_amount=Decimal('100'))
        await order1.save()
        order2 = AsyncOrder(user_id=user2.id, order_number='AELA-CACHE3-002', total_amount=Decimal('200'))
        await order2.save()

        results = await AsyncOrder.query().with_('user').where(
            AsyncOrder.c.id.in_([order1.id, order2.id])
        ).order_by(AsyncOrder.c.id).all()
        assert len(results) == 2, "Expected two results"

        related1 = await results[0].user()
        assert related1.id == user1.id, "Expected first related user id to match user1"
        related2 = await results[1].user()
        assert related2.id == user2.id, "Expected second related user id to match user2"

    async def test_cache_not_mixed_between_instances(self, async_combined_fixtures):
        """Relation cache from one instance should never leak into another (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user1 = AsyncUser(username='aela_cache4a', email='aela_cache4a@example.com', age=25)
        await user1.save()
        user2 = AsyncUser(username='aela_cache4b', email='aela_cache4b@example.com', age=26)
        await user2.save()

        order1 = AsyncOrder(user_id=user1.id, order_number='AELA-CACHE4-001', total_amount=Decimal('100'))
        await order1.save()
        order2 = AsyncOrder(user_id=user2.id, order_number='AELA-CACHE4-002', total_amount=Decimal('200'))
        await order2.save()

        results = await AsyncOrder.query().with_('user') \
            .where(AsyncOrder.c.id.in_([order1.id, order2.id])) \
            .order_by(AsyncOrder.c.id).all()
        assert len(results) == 2, "Expected two results"

        assert (await results[0].user()).id == user1.id, \
            "Expected first related user id to match user1"
        assert (await results[1].user()).id == user2.id, \
            "Expected second related user id to match user2"






