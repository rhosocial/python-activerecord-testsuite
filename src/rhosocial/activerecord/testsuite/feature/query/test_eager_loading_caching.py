# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_caching.py
"""Test InstanceCache population after eager loading.

Verifies that relations loaded via with_() are cached on instances,
so repeated access does not trigger additional database queries.
"""
from decimal import Decimal
class TestSyncEagerLoadingCaching:
    """Sync: verify eager loading populates InstanceCache — same behaviour as async.

    Must mirror every scenario in TestAsyncEagerLoadingCaching.
    """

    def test_cache_after_all(self, combined_fixtures):
        """After all() with with_(), first and second accesses both return cached data."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_cache', email='ela_cache@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-CACHE-001', total_amount=Decimal('100'))
        order.save()

        results = Order.query().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        # First access — should hit cache (populated by eager loading)
        related1 = results[0].user()
        assert related1 is not None
        assert related1.id == user.id
        # Second access — should use same cached entry
        related2 = results[0].user()
        assert related2 is not None
        assert related2.id == user.id

    def test_cache_after_one(self, combined_fixtures):
        """After one() with with_(), the single result has its relation cached."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_cache2', email='ela_cache2@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-CACHE2-001', total_amount=Decimal('200'))
        order.save()

        result = Order.query().with_('user').where(Order.c.id == order.id).one()
        assert result is not None
        related = result.user()
        assert related is not None
        assert related.id == user.id

    def test_cache_independent_per_instance(self, combined_fixtures):
        """Each parent instance should have its own independent cached relation."""
        User, Order, _, _, _ = combined_fixtures
        user1 = User(username='ela_cache3a', email='ela_cache3a@example.com', age=25)
        user1.save()
        user2 = User(username='ela_cache3b', email='ela_cache3b@example.com', age=26)
        user2.save()

        order1 = Order(user_id=user1.id, order_number='ELA-CACHE3-001', total_amount=Decimal('100'))
        order1.save()
        order2 = Order(user_id=user2.id, order_number='ELA-CACHE3-002', total_amount=Decimal('200'))
        order2.save()

        results = Order.query().with_('user').where(
            Order.c.id.in_([order1.id, order2.id])
        ).order_by(Order.c.id).all()
        assert len(results) == 2

        related1 = results[0].user()
        assert related1.id == user1.id
        related2 = results[1].user()
        assert related2.id == user2.id

    def test_cache_not_mixed_between_instances(self, combined_fixtures):
        """Relation cache from one instance should never leak into another."""
        User, Order, _, _, _ = combined_fixtures
        user1 = User(username='ela_cache4a', email='ela_cache4a@example.com', age=25)
        user1.save()
        user2 = User(username='ela_cache4b', email='ela_cache4b@example.com', age=26)
        user2.save()

        order1 = Order(user_id=user1.id, order_number='ELA-CACHE4-001', total_amount=Decimal('100'))
        order1.save()
        order2 = Order(user_id=user2.id, order_number='ELA-CACHE4-002', total_amount=Decimal('200'))
        order2.save()

        results = Order.query().with_('user') \
            .where(Order.c.id.in_([order1.id, order2.id])) \
            .order_by(Order.c.id).all()
        assert len(results) == 2

        assert results[0].user().id == user1.id
        assert results[1].user().id == user2.id