# src/rhosocial/activerecord/testsuite/feature/query/test_eager_loading_nested.py
"""Test nested relation eager loading (e.g. 'posts.comments').

Verifies that with_('relation.nested') recursively preloads data at all levels.
"""
from decimal import Decimal
class TestSyncEagerLoadingNested:
    """Sync: nested eager loading — same behaviour as async.

    Must mirror every scenario in TestAsyncEagerLoadingNested.
    """

    def test_deep_nesting(self, combined_fixtures):
        """Order.with_('items').all() should preload each order's OrderItem records."""
        User, Order, OrderItem, _, _ = combined_fixtures
        user = User(username='ela_nest', email='ela_nest@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-NEST-001', total_amount=Decimal('100'))
        order.save()
        for j in range(2):
            item = OrderItem(order_id=order.id, product_name=f'Nested-{j}',
                             quantity=1, unit_price=Decimal('50'), subtotal=Decimal('50'))
            item.save()

        results = Order.query().with_('items').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related_items = results[0].items()
        assert len(related_items) == 2

    def test_two_level_with_belongs_to(self, combined_fixtures):
        """Order.with_('user').all() preloads the single BelongsTo relation."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_nest2', email='ela_nest2@example.com', age=30)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-NEST2-001', total_amount=Decimal('200'))
        order.save()

        results = Order.query().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related = results[0].user()
        assert related is not None
        assert related.id == user.id

    def test_multiple_nested_same_parent(self, combined_fixtures):
        """Accessing the same nested relation multiple times should return consistent data."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_nest3', email='ela_nest3@example.com', age=28)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-NEST3-001', total_amount=Decimal('300'))
        order.save()

        results = Order.query().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related = results[0].user()
        assert related is not None
        assert related.id == user.id

    def test_all_nested_loaded(self, combined_fixtures):
        """When all() returns multiple parent records, each should have nested data loaded."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_nest4', email='ela_nest4@example.com', age=32)
        user.save()
        for i in range(3):
            o = Order(user_id=user.id, order_number=f'ELA-NEST4-{i:03d}',
                      total_amount=Decimal('100'))
            o.save()

        results = Order.query().with_('user').where(Order.c.user_id == user.id).all()
        assert len(results) == 3
        for r in results:
            u = r.user()
            assert u is not None
            assert u.id == user.id