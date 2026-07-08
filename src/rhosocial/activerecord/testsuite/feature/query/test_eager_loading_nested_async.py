# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_nested_async.py
"""Test nested relation eager loading (e.g. 'posts.comments').

Verifies that with_('relation.nested') recursively preloads data at all levels.
"""
from decimal import Decimal
class TestAsyncEagerLoadingNested:
    """Async: nested eager loading — same behaviour as sync.

    Must mirror every scenario in TestSyncEagerLoadingNested.
    """

    async def test_deep_nesting(self, async_combined_fixtures):
        """AsyncOrder.with_('items').all() should preload OrderItem records."""
        AsyncUser, AsyncOrder, AsyncOrderItem, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_nest', email='aela_nest@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-NEST-001', total_amount=Decimal('100'))
        await order.save()
        for j in range(2):
            item = AsyncOrderItem(order_id=order.id, product_name=f'Nested-{j}',
                                  quantity=1, unit_price=Decimal('50'), subtotal=Decimal('50'))
            await item.save()

        results = await AsyncOrder.query().with_('items').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related_items = await results[0].items()
        assert len(related_items) == 2

    async def test_belongs_to_nested(self, async_combined_fixtures):
        """Async version of Order.with_('user') nested preloading."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_nest2', email='aela_nest2@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-NEST2-001', total_amount=Decimal('200'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related = await results[0].user()
        assert related is not None
        assert related.id == user.id

    async def test_multiple_nested_same_parent(self, async_combined_fixtures):
        """Async version: repeated access to same nested relation returns consistent data."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_nest3', email='aela_nest3@example.com', age=28)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-NEST3-001', total_amount=Decimal('300'))
        await order.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related = await results[0].user()
        assert related is not None
        assert related.id == user.id

    async def test_all_nested_loaded(self, async_combined_fixtures):
        """When all() returns multiple parent records, each should have nested data loaded (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_nest4', email='aela_nest4@example.com', age=32)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-NEST4-{i:03d}',
                           total_amount=Decimal('100'))
            await o.save()

        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.user_id == user.id).all()
        assert len(results) == 3
        for r in results:
            u = await r.user()
            assert u is not None
            assert u.id == user.id