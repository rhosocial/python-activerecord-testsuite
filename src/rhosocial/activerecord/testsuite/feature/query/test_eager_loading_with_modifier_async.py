# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_with_modifier_async.py
"""Test eager loading with query_modifier.

Verifies that query_modifier callables passed via with_((path, modifier))
are applied during batch loading, enabling filtered or sorted relation data.

Backward-compatibility guarantee:
  The eagerly loaded result (via with_ + modifier) must be equivalent
  to the lazily loaded result (via relation_name()).  Previously with_
  was a no-op, so users relied on lazy loading; after the fix, eager
  loading must produce identical data.
"""
from decimal import Decimal

import pytest

from rhosocial.activerecord.backend.dialect.protocols import LockingSupport
class TestAsyncEagerLoadingWithModifier:
    """Async: verify query_modifier applied during eager loading — same as sync.

    Must mirror every scenario in TestSyncEagerLoadingWithModifier.
    """

    async def test_filter_modifier(self, async_combined_fixtures):
        """A filter modifier should only load matching Orders (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_mod', email='aela_mod@example.com', age=25)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-MOD-{i:03d}',
                           total_amount=Decimal('50'))
            await o.save()

        def filter_order(q):
            return q.where(AsyncOrder.c.order_number == 'AELA-MOD-001')

        result = await AsyncUser.query().with_(('orders', filter_order)).where(AsyncUser.c.id == user.id).one()
        assert result is not None
        related = await result.orders()
        assert len(related) == 1
        assert related[0].order_number == 'AELA-MOD-001'

    async def test_order_modifier(self, async_combined_fixtures):
        """An order modifier should sort related records (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_mod2', email='aela_mod2@example.com', age=25)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-MOD2-{i:03d}',
                           total_amount=Decimal(f'{(i+1)*10}'))
            await o.save()

        def desc_order(q):
            return q.order_by((AsyncOrder.c.total_amount, "DESC"))

        result = await AsyncUser.query().with_(('orders', desc_order)).where(AsyncUser.c.id == user.id).one()
        assert result is not None
        related = await result.orders()
        assert len(related) == 3
        assert related[0].total_amount == Decimal('30')

    async def test_without_modifier(self, async_combined_fixtures):
        """Using with_ without a modifier should load all related records (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_mod3', email='aela_mod3@example.com', age=25)
        await user.save()
        for i in range(2):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-MOD3-{i:03d}',
                           total_amount=Decimal('50'))
            await o.save()

        result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        assert result is not None
        related = await result.orders()
        assert len(related) == 2

    async def test_none_modifier(self, async_combined_fixtures):
        """A noop modifier should not interfere with normal loading (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_mod4', email='aela_mod4@example.com', age=25)
        await user.save()

        def noop(q):
            return q

        results = await AsyncUser.query().with_(('orders', noop)).where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1

    async def test_eager_equivalent_to_lazy(self, async_combined_fixtures):
        """Backward-compatibility: eager (no modifier) == lazy loading (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_bc', email='aela_bc@example.com', age=30)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AELA-BC-{i:03d}',
                           total_amount=Decimal(f'{(i+1)*10}'))
            await o.save()

        # Eager without modifier
        eager_result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        eager_orders = sorted(await eager_result.orders(), key=lambda o: o.id)

        # Lazy
        lazy_user = await AsyncUser.find_one(user.id)
        lazy_orders = sorted(await lazy_user.orders(), key=lambda o: o.id)

        assert len(eager_orders) == len(lazy_orders)
        for eo, lo in zip(eager_orders, lazy_orders):
            assert eo.id == lo.id
            assert eo.order_number == lo.order_number
            assert eo.total_amount == lo.total_amount

    async def test_eager_with_belongs_to_equivalent_to_lazy(self, async_combined_fixtures):
        """Backward-compatibility: eager with_('user') == lazy user() (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aela_bc2', email='aela_bc2@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AELA-BC2-001', total_amount=Decimal('100'))
        await order.save()

        eager = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        eager_user = await eager.user()

        lazy_order = await AsyncOrder.find_one(order.id)
        lazy_user = await lazy_order.user()

        assert eager_user.id == lazy_user.id
        assert eager_user.username == lazy_user.username
        assert eager_user.email == lazy_user.email

class TestAsyncForUpdate:
    """Async version of for_update + with_ compatibility."""

    @pytest.mark.requires_protocol((LockingSupport, "supports_for_update"))
    async def test_for_update_with_with_(self, async_combined_fixtures):
        """for_update() can be chained before with_() and all() (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='afor_up', email='afor_up@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AFOR-UP-001', total_amount=Decimal('100'))
        await order.save()

        results = await AsyncOrder.query().for_update().with_('user').where(AsyncOrder.c.id == order.id).all()
        assert len(results) == 1
        related = await results[0].user()
        assert related is not None
        assert related.id == user.id

    @pytest.mark.requires_protocol((LockingSupport, "supports_for_update"))
    async def test_for_update_with_with_one(self, async_combined_fixtures):
        """for_update() + with_() + one() (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='afor_up2', email='afor_up2@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AFOR-UP-002', total_amount=Decimal('200'))
        await order.save()

        result = await AsyncOrder.query().for_update().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None
        related = await result.user()
        assert related is not None
        assert related.id == user.id