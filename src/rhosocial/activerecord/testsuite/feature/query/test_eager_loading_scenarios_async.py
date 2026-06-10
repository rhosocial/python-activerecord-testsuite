# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_scenarios_async.py
"""Async: extended eager loading scenario tests.

Mirrors test_eager_loading_scenarios_sync.py exactly for sync/async parity.
"""
from decimal import Decimal

from rhosocial.activerecord.backend.base import AsyncStorageBackend


# ---------------------------------------------------------------------------
# Helper: async query-counting wrapper
# ---------------------------------------------------------------------------
class AsyncQueryCounter:
    """Counts SELECT queries (fetch_all / fetch_one) on an AsyncStorageBackend."""

    def __init__(self, model_or_backend):
        if hasattr(model_or_backend, "backend"):
            self._backend = model_or_backend.backend()
        else:
            self._backend = model_or_backend
        self.select_count = 0

    def install(self):
        orig_fetch_all = self._backend.fetch_all

        async def counting_fetch_all(*args, **kwargs):
            self.select_count += 1
            return await orig_fetch_all(*args, **kwargs)

        self._backend.fetch_all = counting_fetch_all
        orig_fetch_one = self._backend.fetch_one

        async def counting_fetch_one(*args, **kwargs):
            self.select_count += 1
            return await orig_fetch_one(*args, **kwargs)

        self._backend.fetch_one = counting_fetch_one
        return self


# ---------------------------------------------------------------------------
# 1. SQL query count verification
# ---------------------------------------------------------------------------
class TestAsyncQueryCount:
    """Async: verify N+1 prevention via query counters."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_has_many_count(self, async_combined_fixtures):
        """HasMany: with_('orders') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_hm', email='aqc_hm@example.com', age=25)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-HM-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1
        related = await results[0].orders()
        assert len(related) == 3
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_belongs_to_count(self, async_combined_fixtures):
        """BelongsTo: with_('user') on N orders → 2 queries (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_bt', email='aqc_bt@example.com', age=25)
        await user.save()
        for i in range(4):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-BT-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.user_id == user.id).all()
        assert len(results) == 4
        for o in results:
            assert await o.user() is not None
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_multiple_relations_count(self, async_combined_fixtures):
        """Multiple with_: with_('orders', 'posts') → 3 queries (async)."""
        AsyncUser, AsyncOrder, _, AsyncPost, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_mr', email='aqc_mr@example.com', age=25)
        await user.save()
        for i in range(2):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-MR-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()
            p = AsyncPost(title=f'AQC-MR-{i}', content='x', user_id=user.id, status='published')
            await p.save()

        counter = self._install_counter(AsyncUser)
        results = await AsyncUser.query().with_('orders', 'posts').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1
        assert len(await results[0].orders()) == 2
        assert len(await results[0].posts()) == 2
        assert counter.select_count == 3, f"Expected 3 async queries, got {counter.select_count}"

    async def test_without_eager_is_nplus1(self, async_combined_fixtures):
        """Baseline: without with_() causes N+1 (1 + N queries) (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aqc_n1', email='aqc_n1@example.com', age=25)
        await user.save()
        for i in range(4):
            o = AsyncOrder(user_id=user.id, order_number=f'AQC-N1-{i:03d}',
                           total_amount=Decimal('10'))
            await o.save()

        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().where(AsyncOrder.c.user_id == user.id).all()
        assert len(results) == 4
        for o in results:
            _ = await o.user()
        assert counter.select_count == 5, f"Expected 5 async queries (N+1), got {counter.select_count}"


# ---------------------------------------------------------------------------
# 2. Empty relation boundary
# ---------------------------------------------------------------------------
class TestAsyncEmptyRelation:
    """Async: parent exists, related table is empty."""

    async def test_has_many_empty(self, async_combined_fixtures):
        """Parent with no orders → .orders() returns [] (async)."""
        AsyncUser, _, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aempty_hm', email='aempty_hm@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        assert result is not None
        related = await result.orders()
        assert related == []

    async def test_belongs_to_none(self, async_combined_fixtures):
        """Order with no matching user → .user() returns None (async).

        Strategy: create a User, save an Order referencing it, then delete
        the User. Same pattern as sync version.
        """
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aorphan_ref', email='aorphan_ref@example.com', age=25)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AORPHAN-001', total_amount=Decimal('10'))
        await order.save()
        # Delete the parent — Order now orphaned
        await user.delete()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None
        related = await result.user()
        assert related is None

    async def test_has_many_empty_list_after_eager(self, async_combined_fixtures):
        """HasMany: relation_name() returns [] when empty (async)."""
        AsyncUser, _, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aemplist', email='aemplist@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        assert result is not None
        orders = await result.orders()
        assert isinstance(orders, list)
        assert len(orders) == 0


# ---------------------------------------------------------------------------
# 3. all() empty result — with_() must not fire any batch query
# ---------------------------------------------------------------------------
class TestAsyncEmptyResultNoQuery:
    """Async: .all()/.one() empty → no batch queries."""

    def _install_counter(self, model_class) -> AsyncQueryCounter:
        return AsyncQueryCounter(model_class).install()

    async def test_all_empty_no_batch(self, async_combined_fixtures):
        """No matching parent → all() returns [] and 1 query total (async)."""
        _, AsyncOrder, _, _, _ = async_combined_fixtures
        counter = self._install_counter(AsyncOrder)
        results = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).all()
        assert results == []
        assert counter.select_count == 1, f"Expected 1 async query, got {counter.select_count}"

    async def test_one_none_no_batch(self, async_combined_fixtures):
        """No matching parent → one() returns None and 1 query total (async)."""
        _, AsyncOrder, _, _, _ = async_combined_fixtures
        counter = self._install_counter(AsyncOrder)
        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == -1).one()
        assert result is None
        assert counter.select_count == 1, f"Expected 1 async query, got {counter.select_count}"


# ---------------------------------------------------------------------------
# 4. HasOne batch loading
# ---------------------------------------------------------------------------
class TestAsyncHasOneEagerLoading:
    """Async: verify HasOne can be batch-loaded via with_()."""

    async def test_has_one_eager(self, async_profile_fixtures):
        """with_('profile') should preload HasOne relation (async)."""
        AsyncUser, AsyncProfile = async_profile_fixtures
        user = AsyncUser(username='aho_user', email='aho_user@example.com', age=25)
        await user.save()
        profile = AsyncProfile(user_id=user.id, bio="Test bio", avatar_url="http://example.com/av.jpg")
        await profile.save()

        result = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).one()
        assert result is not None
        related = await result.profile()
        assert related is not None
        assert related.bio == "Test bio"

    async def test_has_one_count(self, async_profile_fixtures):
        """with_('profile') → 2 queries regardless of N (async)."""
        AsyncUser, AsyncProfile = async_profile_fixtures
        counter = AsyncQueryCounter(AsyncUser).install()
        user = AsyncUser(username='aho_count', email='aho_count@example.com', age=25)
        await user.save()
        await AsyncProfile(user_id=user.id, bio="Count test").save()

        results = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).all()
        assert len(results) == 1
        p = await results[0].profile()
        assert p is not None
        assert counter.select_count == 2, f"Expected 2 async queries, got {counter.select_count}"

    async def test_has_one_empty(self, async_profile_fixtures):
        """User with no profile → .profile() returns None (async)."""
        AsyncUser, _ = async_profile_fixtures
        user = AsyncUser(username='aho_empty', email='aho_empty@example.com', age=25)
        await user.save()

        result = await AsyncUser.query().with_('profile').where(AsyncUser.c.id == user.id).one()
        assert result is not None
        profile = await result.profile()
        assert profile is None


# ---------------------------------------------------------------------------
# 5. HasMany empty → []  (covered in TestAsyncEmptyRelation above)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 6. with_() vs lazy loading mutual exclusion
# ---------------------------------------------------------------------------
class TestAsyncEagerVsLazyParity:
    """Async: eager and lazy produce identical results."""

    async def test_eager_vs_lazy_has_many(self, async_combined_fixtures):
        """Eager and lazy return identical data for HasMany (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aparity', email='aparity@example.com', age=30)
        await user.save()
        for i in range(3):
            o = AsyncOrder(user_id=user.id, order_number=f'APARITY-{i:03d}',
                           total_amount=Decimal(f'{(i + 1) * 10}'))
            await o.save()

        eager = await AsyncUser.query().with_('orders').where(AsyncUser.c.id == user.id).one()
        eager_orders = sorted(await eager.orders(), key=lambda o: o.id)

        lazy_user = await AsyncUser.find_one(user.id)
        lazy_orders = sorted(await lazy_user.orders(), key=lambda o: o.id)

        assert len(eager_orders) == len(lazy_orders)
        for eo, lo in zip(eager_orders, lazy_orders):
            assert eo.order_number == lo.order_number
            assert eo.total_amount == lo.total_amount

    async def test_eager_vs_lazy_belongs_to(self, async_combined_fixtures):
        """Eager and lazy return identical User for BelongsTo (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='aparity_bt', email='aparity_bt@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='APARITY-BT-001', total_amount=Decimal('50'))
        await order.save()

        eager = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        eager_user = await eager.user()

        lazy_order = await AsyncOrder.find_one(order.id)
        lazy_user = await lazy_order.user()

        assert eager_user.id == lazy_user.id
        assert eager_user.username == lazy_user.username


# ---------------------------------------------------------------------------
# 7. Mixed with_() + lazy — part cached, part lazy-loaded
# ---------------------------------------------------------------------------
class TestAsyncMixedEagerLazy:
    """Async: some relations eager, some lazy."""

    async def test_mixed_relations(self, async_combined_fixtures):
        """with_('user') eager, items lazy (async)."""
        AsyncUser, AsyncOrder, AsyncOrderItem, _, _ = async_combined_fixtures
        user = AsyncUser(username='amixed', email='amixed@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AMIXED-001', total_amount=Decimal('50'))
        await order.save()
        item = AsyncOrderItem(order_id=order.id, product_name='AM-Item', quantity=1,
                              unit_price=Decimal('25'), subtotal=Decimal('25'))
        await item.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None

        eager_user = await result.user()
        assert eager_user is not None
        assert eager_user.username == 'amixed'

        lazy_items = await result.items()
        assert len(lazy_items) == 1
        assert lazy_items[0].product_name == 'AM-Item'

    async def test_mixed_eager_then_lazy_same_relation(self, async_combined_fixtures):
        """First access via eager, second via lazy — both work (async)."""
        AsyncUser, AsyncOrder, _, _, _ = async_combined_fixtures
        user = AsyncUser(username='amix2', email='amix2@example.com', age=30)
        await user.save()
        order = AsyncOrder(user_id=user.id, order_number='AMIXED-002', total_amount=Decimal('50'))
        await order.save()

        result = await AsyncOrder.query().with_('user').where(AsyncOrder.c.id == order.id).one()
        assert result is not None

        u1 = await result.user()
        assert u1 is not None
        u2 = await result.user()
        assert u2 is not None
        assert u2.id == u1.id
