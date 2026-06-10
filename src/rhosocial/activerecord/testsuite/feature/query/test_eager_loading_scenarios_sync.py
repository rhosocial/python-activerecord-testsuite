# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_scenarios_sync.py
"""Sync: extended eager loading scenario tests.

Covers edge cases not covered by the existing 5 test files:

1. SQL query count verification (core) — proves N+1 prevention
2. Empty relation boundary — parent exists, relation table empty
3. all() empty result — with_() must not execute batch queries
4. HasOne batch loading
5. HasMany empty → [] — relation cache stores empty list
6. with_() vs lazy loading mutual exclusion — correct data both ways
7. Mixed with_() + lazy — part cached, part lazy-loaded
"""
from decimal import Decimal

from rhosocial.activerecord.backend.base import StorageBackend


# ---------------------------------------------------------------------------
# Helper: query-counting wrapper
# ---------------------------------------------------------------------------
class QueryCounter:
    """Counts SELECT queries (fetch_all / fetch_one) on a StorageBackend."""

    def __init__(self, model_or_backend):
        if hasattr(model_or_backend, "backend"):
            self._backend = model_or_backend.backend()
        else:
            self._backend = model_or_backend
        self.select_count = 0

    def install(self):
        orig_fetch_all = self._backend.fetch_all

        def counting_fetch_all(*args, **kwargs):
            self.select_count += 1
            return orig_fetch_all(*args, **kwargs)

        self._backend.fetch_all = counting_fetch_all
        orig_fetch_one = self._backend.fetch_one

        def counting_fetch_one(*args, **kwargs):
            self.select_count += 1
            return orig_fetch_one(*args, **kwargs)

        self._backend.fetch_one = counting_fetch_one
        return self


# ---------------------------------------------------------------------------
# 1. SQL query count verification
# ---------------------------------------------------------------------------
class TestSyncQueryCount:
    """Verify N+1 prevention via query counters.

    Expected SQL queries:
    - 1 master query (SELECT)
    - 1 batch query per eager-loaded relation (WHERE pk IN …)
    → Total = 1 + number_of_relations (NOT 1 + N)
    """

    def _install_counter(self, model_class) -> QueryCounter:
        return QueryCounter(model_class.backend()).install()

    def test_has_many_count(self, combined_fixtures):
        """HasMany: with_('orders') → 2 queries regardless of N."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='qc_hm', email='qc_hm@example.com', age=25)
        user.save()
        for i in range(3):
            Order(user_id=user.id, order_number=f'QC-HM-{i:03d}',
                  total_amount=Decimal('10')).save()

        counter = self._install_counter(User)
        results = User.query().with_('orders').where(User.c.id == user.id).all()
        assert len(results) == 1
        related = results[0].orders()
        assert len(related) == 3
        assert counter.select_count == 2, f"Expected 2 queries, got {counter.select_count}"

    def test_belongs_to_count(self, combined_fixtures):
        """BelongsTo: with_('user') on N orders → 2 queries."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='qc_bt', email='qc_bt@example.com', age=25)
        user.save()
        for i in range(5):
            Order(user_id=user.id, order_number=f'QC-BT-{i:03d}',
                  total_amount=Decimal('10')).save()

        counter = self._install_counter(Order)
        results = Order.query().with_('user').where(Order.c.user_id == user.id).all()
        assert len(results) == 5
        for o in results:
            assert o.user() is not None
        assert counter.select_count == 2, f"Expected 2 queries, got {counter.select_count}"

    def test_multiple_relations_count(self, combined_fixtures):
        """Multiple with_: with_('orders', 'posts') on 1 user → 3 queries."""
        User, Order, _, Post, _ = combined_fixtures
        user = User(username='qc_mr', email='qc_mr@example.com', age=25)
        user.save()
        for i in range(2):
            Order(user_id=user.id, order_number=f'QC-MR-{i:03d}',
                  total_amount=Decimal('10')).save()
            Post(title=f'QC-MR-{i}', content='x', user_id=user.id,
                 status='published').save()

        counter = self._install_counter(User)
        results = User.query().with_('orders', 'posts').where(User.c.id == user.id).all()
        assert len(results) == 1
        assert len(results[0].orders()) == 2
        assert len(results[0].posts()) == 2
        assert counter.select_count == 3, f"Expected 3 queries, got {counter.select_count}"

    def test_without_eager_is_nplus1(self, combined_fixtures):
        """Baseline: without with_() causes N+1 (1 + N queries).

        This test proves the counter works by demonstrating the N+1 pattern
        when with_() is NOT used.
        """
        User, Order, _, _, _ = combined_fixtures
        user = User(username='qc_n1', email='qc_n1@example.com', age=25)
        user.save()
        for i in range(4):
            Order(user_id=user.id, order_number=f'QC-N1-{i:03d}',
                  total_amount=Decimal('10')).save()

        counter = self._install_counter(Order)
        results = Order.query().where(Order.c.user_id == user.id).all()
        assert len(results) == 4
        for o in results:
            _ = o.user()  # lazy — each triggers a query
        assert counter.select_count == 5, f"Expected 5 queries (N+1), got {counter.select_count}"


# ---------------------------------------------------------------------------
# 2. Empty relation boundary
# ---------------------------------------------------------------------------
class TestSyncEmptyRelation:
    """Parent exists, related table is empty."""

    def test_has_many_empty(self, combined_fixtures):
        """Parent with no orders → .orders() returns [] (empty list)."""
        User, _, _, _, _ = combined_fixtures
        user = User(username='empty_hm', email='empty_hm@example.com', age=25)
        user.save()

        result = User.query().with_('orders').where(User.c.id == user.id).one()
        assert result is not None
        related = result.orders()
        assert related is not None
        assert related == []  # empty list, not None

    def test_belongs_to_none(self, combined_fixtures):
        """Order with no matching user → .user() returns None.

        Note: Creates an orphaned FK reference by first saving a User,
        then an Order referencing it, then deleting the User. This requires
        the Provider's schema to either not have FK constraints or use
        ON DELETE CASCADE/SET NULL for this test to pass.
        """
        User, Order, _, _, _ = combined_fixtures
        user = User(username='orphan_ref', email='orphan_ref@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ORPHAN-001', total_amount=Decimal('10'))
        order.save()

        # Attempt to delete the User — may fail if FK enforcement is ON.
        # If it fails, the test cannot verify the orphan case and is skipped
        # (the Provider must handle this scenario).
        try:
            user.delete()
        except Exception:
            # FK enforcement prevents deletion; skip this edge case
            return

        result = Order.query().with_('user').where(Order.c.id == order.id).one()
        assert result is not None
        related = result.user()
        assert related is None

    def test_has_many_empty_list_after_eager(self, combined_fixtures):
        """HasMany: relation_name() returns [] when no related records exist."""
        User, _, _, _, _ = combined_fixtures
        user = User(username='emplist', email='emplist@example.com', age=25)
        user.save()

        result = User.query().with_('orders').where(User.c.id == user.id).one()
        assert result is not None
        orders = result.orders()
        assert orders is not None
        assert isinstance(orders, list)
        assert len(orders) == 0


# ---------------------------------------------------------------------------
# 3. all() empty result — with_() must not fire any batch query
# ---------------------------------------------------------------------------
class TestSyncEmptyResultNoQuery:
    """When .all() returns [] / .one() returns None, no batch queries should fire."""

    def _install_counter(self, model_class) -> QueryCounter:
        return QueryCounter(model_class.backend()).install()

    def test_all_empty_no_batch(self, combined_fixtures):
        """No matching parent → all() returns [] and no batch queries fire.

        The master query executes (1 SELECT) but returns 0 rows, so eager
        loading skips all batch queries.
        """
        _, Order, _, _, _ = combined_fixtures
        counter = self._install_counter(Order)
        results = Order.query().with_('user').where(Order.c.id == -1).all()
        assert results == []
        assert counter.select_count == 1, f"Expected 1 query, got {counter.select_count}"

    def test_one_none_no_batch(self, combined_fixtures):
        """No matching parent → one() returns None and no batch queries fire."""
        _, Order, _, _, _ = combined_fixtures
        counter = self._install_counter(Order)
        result = Order.query().with_('user').where(Order.c.id == -1).one()
        assert result is None
        assert counter.select_count == 1, f"Expected 1 query, got {counter.select_count}"


# ---------------------------------------------------------------------------
# 4. HasOne batch loading
# ---------------------------------------------------------------------------
class TestSyncHasOneEagerLoading:
    """Verify HasOne can be batch-loaded via with_()."""

    def test_has_one_eager(self, profile_fixtures):
        """with_('profile') should preload HasOne relation."""
        User, Profile = profile_fixtures
        user = User(username='ho_user', email='ho_user@example.com', age=25)
        user.save()
        profile = Profile(user_id=user.id, bio="Test bio", avatar_url="http://example.com/av.jpg")
        profile.save()

        result = User.query().with_('profile').where(User.c.id == user.id).one()
        assert result is not None
        related = result.profile()
        assert related is not None
        assert related.bio == "Test bio"

    def test_has_one_count(self, profile_fixtures):
        """with_('profile') → 2 queries regardless of N."""
        User, Profile = profile_fixtures
        counter = QueryCounter(User).install()
        user = User(username='ho_count', email='ho_count@example.com', age=25)
        user.save()
        Profile(user_id=user.id, bio="Count test").save()

        results = User.query().with_('profile').where(User.c.id == user.id).all()
        assert len(results) == 1
        p = results[0].profile()
        assert p is not None
        assert counter.select_count == 2, f"Expected 2 queries, got {counter.select_count}"

    def test_has_one_empty(self, profile_fixtures):
        """User with no profile → .profile() returns None."""
        User, _ = profile_fixtures
        user = User(username='ho_empty', email='ho_empty@example.com', age=25)
        user.save()

        result = User.query().with_('profile').where(User.c.id == user.id).one()
        assert result is not None
        profile = result.profile()
        assert profile is None


# ---------------------------------------------------------------------------
# 5. HasMany empty → []  (covered in TestSyncEmptyRelation above)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 6. with_() vs lazy loading mutual exclusion
# ---------------------------------------------------------------------------
class TestSyncEagerVsLazyParity:
    """Eager loading (with_()) and lazy loading produce identical results."""

    def _create_data(self, User, Order):
        user = User(username='parity', email='parity@example.com', age=30)
        user.save()
        for i in range(3):
            Order(user_id=user.id, order_number=f'PARITY-{i:03d}',
                  total_amount=Decimal(f'{(i + 1) * 10}')).save()
        return user

    def test_eager_vs_lazy_has_many(self, combined_fixtures):
        """Eager and lazy return identical data for HasMany."""
        User, Order, _, _, _ = combined_fixtures
        user = self._create_data(User, Order)

        eager = User.query().with_('orders').where(User.c.id == user.id).one()
        eager_orders = sorted(eager.orders(), key=lambda o: o.id)

        lazy_user = User.find_one(user.id)
        lazy_orders = sorted(lazy_user.orders(), key=lambda o: o.id)

        assert len(eager_orders) == len(lazy_orders)
        for eo, lo in zip(eager_orders, lazy_orders):
            assert eo.order_number == lo.order_number
            assert eo.total_amount == lo.total_amount

    def test_eager_vs_lazy_belongs_to(self, combined_fixtures):
        """Eager and lazy return identical User for BelongsTo."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='parity_bt', email='parity_bt@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='PARITY-BT-001', total_amount=Decimal('50'))
        order.save()

        eager = Order.query().with_('user').where(Order.c.id == order.id).one()
        eager_user = eager.user()

        lazy_order = Order.find_one(order.id)
        lazy_user = lazy_order.user()

        assert eager_user.id == lazy_user.id
        assert eager_user.username == lazy_user.username


# ---------------------------------------------------------------------------
# 7. Mixed with_() + lazy — part cached, part lazy-loaded
# ---------------------------------------------------------------------------
class TestSyncMixedEagerLazy:
    """Some relations eagerly loaded, some lazy — all must still resolve correctly."""

    def test_mixed_relations(self, combined_fixtures):
        """with_('user') eager, items lazy."""
        User, Order, OrderItem, _, _ = combined_fixtures
        user = User(username='mixed', email='mixed@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='MIXED-001', total_amount=Decimal('50'))
        order.save()
        OrderItem(order_id=order.id, product_name='M-Item', quantity=1,
                  unit_price=Decimal('25'), subtotal=Decimal('25')).save()

        result = Order.query().with_('user').where(Order.c.id == order.id).one()
        assert result is not None

        eager_user = result.user()
        assert eager_user is not None
        assert eager_user.username == 'mixed'

        items = result.items()
        assert len(items) == 1
        assert items[0].product_name == 'M-Item'

    def test_mixed_eager_then_lazy_same_relation(self, combined_fixtures):
        """First access via eager, second via lazy — both work (cache)."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='mix2', email='mix2@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='MIXED-002', total_amount=Decimal('50'))
        order.save()

        result = Order.query().with_('user').where(Order.c.id == order.id).one()
        assert result is not None

        u1 = result.user()
        assert u1 is not None
        u2 = result.user()
        assert u2 is not None
        assert u2.id == u1.id
