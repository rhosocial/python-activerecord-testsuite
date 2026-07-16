# src/rhosocial/activerecord/testsuite/feature/query/eager_loading/test_eager_loading_with_all.py
"""Test eager loading using all() method.

Verifies that relations configured via with_() are eagerly loaded and accessible
after all() returns, without requiring additional database queries.
"""
from decimal import Decimal
class TestSyncEagerLoadingWithAll:
    """Sync: verify with_('relation').all() preloads — same behaviour as async.

    Must mirror every scenario in TestAsyncEagerLoadingWithAll.
    """

    def test_belongs_to(self, combined_fixtures):
        """After Order.with_('user').all(), order.user() should return the linked User."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_all_user', email='ela_all@example.com', age=25)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-ALL-001', total_amount=Decimal('100'))
        order.save()

        results = Order.query().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related = results[0].user()
        assert related is not None
        assert related.id == user.id
        assert related.username == 'ela_all_user'

    def test_has_many(self, combined_fixtures):
        """After User.with_('orders').all(), user.orders() should return all related Orders."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_all_hm', email='ela_all_hm@example.com', age=30)
        user.save()
        for i in range(3):
            o = Order(user_id=user.id, order_number=f'ELA-HM-{i:03d}', total_amount=Decimal('50'))
            o.save()

        results = User.query().with_('orders').where(User.c.id == user.id).all()
        assert len(results) == 1
        related = results[0].orders()
        assert len(related) == 3

    def test_empty_result(self, combined_fixtures):
        """when no records match, with_().all() should return empty list, not raise."""
        User, Order, _, _, _ = combined_fixtures
        results = Order.query().with_('user').where(Order.c.id == -1).all()
        assert len(results) == 0

    def test_data_correctness(self, combined_fixtures):
        """Preloaded User instance should have correct field values (username, id)."""
        User, _, _, Post, _ = combined_fixtures
        user = User(username='ela_all_dc', email='ela_all_dc@example.com', age=28)
        user.save()
        post = Post(title='Data Check', content='Content', user_id=user.id, status='published')
        post.save()

        results = Post.query().with_('user').where(Post.c.id == post.id).all()
        assert len(results) == 1
        related = results[0].user()
        assert related is not None
        assert related.id == user.id
        assert related.username == 'ela_all_dc'

    def test_multiple_relations(self, combined_fixtures):
        """Chaining with_() and where() should still correctly preload the User relation."""
        User, Order, _, _, _ = combined_fixtures
        user = User(username='ela_all_multi', email='ela_all_multi@example.com', age=35)
        user.save()
        order = Order(user_id=user.id, order_number='ELA-MULTI-001', total_amount=Decimal('150'))
        order.save()

        results = Order.query().with_('user').where(Order.c.id == order.id).all()
        assert len(results) == 1
        related_user = results[0].user()
        assert related_user is not None
        assert related_user.id == user.id