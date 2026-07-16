# src/rhosocial/activerecord/testsuite/feature/query/eager_loading/test_eager_loading_with_all_async.py
"""Test eager loading using all() method.

Verifies that relations configured via with_() are eagerly loaded and accessible
after all() returns, without requiring additional database queries.
"""
from decimal import Decimal
class TestAsyncEagerLoadingWithAll:
    """Async: verify with_('relation').all() preloads — same behaviour as sync.

    Must mirror every scenario in TestSyncEagerLoadingWithAll.
    """

    async def test_belongs_to(self, async_combined_fixtures):
        """AsyncOrder.with_('user').all() should eagerly load the User relation."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_all', email='aela_all@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-ALL-001', total_amount=Decimal('100'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related = await results[0].user()
        assert related is not None
        assert related.id == user.id

    async def test_has_many(self, async_combined_fixtures):
        """AsyncUser.with_('orders').all() should preload all related Orders."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_all_hm', email='aela_all_hm@example.com', age=30)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-HM-{i:03d}', total_amount=Decimal('50'))
            await o.save()

        results = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1
        related = await results[0].orders()
        assert len(related) == 3

    async def test_empty_result(self, async_combined_fixtures):
        """Empty result set should return empty list, not raise (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).all()
        assert len(results) == 0

    async def test_data_correctness(self, async_combined_fixtures):
        """Preloaded User instance should have correct field values (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_all_dc', email='aela_all_dc@example.com', age=28)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-ALL-DC-001', total_amount=Decimal('100'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related = await results[0].user()
        assert related is not None
        assert related.id == user.id
        assert related.username == 'aela_all_dc'

    async def test_multiple_relations(self, async_combined_fixtures):
        """Chaining with_() and where() with all() should preload (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_all_multi', email='aela_all_multi@example.com', age=35)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-MULTI-001', total_amount=Decimal('150'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related_user = await results[0].user()
        assert related_user is not None
        assert related_user.id == user.id






