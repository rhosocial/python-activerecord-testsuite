# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_with_modifier.py
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
class TestSyncEagerLoadingWithModifier:
    """Sync: verify query_modifier is applied during eager loading.

    Scenarios:
    - Filter modifier
    - Order modifier
    - No modifier (all records)
    - Noop modifier
    - Backward compatibility: eager result == lazy result
    """

    def test_filter_modifier(self, combined_fixtures):
        """A modifier that filters by order_number should only load matching Orders."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_mod', email='ela_mod@example.com', age=25)
        user.save()
        for i in range(3):
            o = Order(user_id=user.id, order_number=f'ELA-MOD-{i:03d}',
                      total_amount=Decimal('50'))
            o.save()

        def filter_order(q):
            return q.where(Order.c.order_number == 'ELA-MOD-001')

        result = User.query().with_(('orders', filter_order)).where(User.c.id == user.id).one()
        assert result is not None
        related = result.orders()
        assert len(related) == 1
        assert related[0].order_number == 'ELA-MOD-001'

    def test_order_modifier(self, combined_fixtures):
        """A modifier that sorts by total_amount DESC should return records in order."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_mod2', email='ela_mod2@example.com', age=25)
        user.save()
        for i in range(3):
            o = Order(user_id=user.id, order_number=f'ELA-MOD2-{i:03d}',
                      total_amount=Decimal(f'{(i+1)*10}'))
            o.save()

        def desc_order(q):
            return q.order_by((Order.c.total_amount, "DESC"))

        result = User.query().with_(('orders', desc_order)).where(User.c.id == user.id).one()
        assert result is not None
        related = result.orders()
        assert len(related) == 3
        assert related[0].total_amount == Decimal('30')

    def test_without_modifier(self, combined_fixtures):
        """Using with_ without a modifier should load all related records."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_mod3', email='ela_mod3@example.com', age=25)
        user.save()
        for i in range(2):
            o = Order(user_id=user.id, order_number=f'ELA-MOD3-{i:03d}',
                      total_amount=Decimal('50'))
            o.save()

        result = User.query().with_('orders').where(User.c.id == user.id).one()
        assert result is not None
        related = result.orders()
        assert len(related) == 2

    def test_none_modifier(self, combined_fixtures):
        """A noop modifier should not interfere with normal loading."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_mod4', email='ela_mod4@example.com', age=25)
        user.save()

        def noop(q):
            return q

        results = User.query().with_(('orders', noop)).where(User.c.id == user.id).all()
        assert len(results) == 1

    def test_eager_equivalent_to_lazy(self, combined_fixtures):
        """Backward-compatibility: with_ (without modifier) must produce same data as lazy loading.

        Previously with_ was a no-op and relation_name() triggered lazy loading.
        After the fix, eager loading must return identical results for the same query.
        """
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_bc', email='ela_bc@example.com', age=30)
        user.save()
        for i in range(3):
            o = Order(user_id=user.id, order_number=f'ELA-BC-{i:03d}',
                      total_amount=Decimal(f'{(i+1)*10}'))
            o.save()

        # ---- Eager loading via with_ (no modifier) ----
        eager_result = User.query().with_('orders').where(User.c.id == user.id).one()
        eager_orders = sorted(eager_result.orders(), key=lambda o: o.id)

        # ---- Lazy loading without with_ ----
        lazy_user = User.find_one(user.id)
        lazy_orders = sorted(lazy_user.orders(), key=lambda o: o.id)

        # ---- Compare: same data regardless of loading strategy ----
        assert len(eager_orders) == len(lazy_orders)
        for eo, lo in zip(eager_orders, lazy_orders):
            assert eo.id == lo.id
            assert eo.order_number == lo.order_number
            assert eo.total_amount == lo.total_amount

    def test_eager_with_belongs_to_equivalent_to_lazy(self, combined_fixtures):
        """Backward-compatibility: with_('user') must return the same User as lazy user()."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_bc2', email='ela_bc2@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-BC2-001', total_amount=Decimal('100'))
        order.save()

        # Eager
        eager = Order.query().with_('user').where(Order.c.id == order.id).one()
        eager_user = eager.user()

        # Lazy
        lazy_order = Order.find_one(order.id)
        lazy_user = lazy_order.user()

        assert eager_user.id == lazy_user.id
        assert eager_user.username == lazy_user.username
        assert eager_user.email == lazy_user.email

class TestSyncForUpdate:
    """Verify for_update() compatibility with with_().

    NOTE: for_update requires LockingSupport protocol.
    SQLite does not support FOR UPDATE, so these tests are skipped there.
    The combined fixtures (combined_fixtures) include Order model with user relation.
    """

    @pytest.mark.requires_protocol((LockingSupport, "supports_for_update"))
    def test_for_update_with_with_(self, combined_fixtures):
        """for_update() can be chained before with_() and all().

        Only runs on backends that support FOR UPDATE (MySQL, Postgres, etc.).
        """
        User, Order, _, _, _ = combined_fixtures
        user = User(username='for_up_user', email='for_up@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='FOR-UP-001', total_amount=Decimal('100'))
        order.save()

        results = Order.query().for_update().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related = results[0].user()
        assert related is not None
        assert related.id == user.id

    @pytest.mark.requires_protocol((LockingSupport, "supports_for_update"))
    def test_for_update_with_with_one(self, combined_fixtures):
        """for_update() chained with with_() works with one()."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='for_up_user2', email='for_up2@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='FOR-UP-002', total_amount=Decimal('200'))
        order.save()

        result = Order.query().for_update().with_('user').where(Order.c.id == order.id).one()
        assert result is not None
        related = result.user()
        assert related is not None
        assert related.id == user.id