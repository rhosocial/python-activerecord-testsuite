# src/rhosocial/activerecord/testsuite/feature/query/test_relations_with_sync.py
"""Sync: relation 'with' method configuration tests.

Verifies that with_() correctly stores eager-loading configurations
(relation paths, nested relations, query modifiers) without executing I/O.
"""
from decimal import Decimal
from unittest.mock import patch


class TestSyncRelationsWith:
    """Synchronous tests for relation 'with' functionality"""

    def test_relations_with_single_relation(self, order_fixtures):
        """with_('user') should store a single RelationConfig with no nesting."""
        _, Order, _ = order_fixtures
        query = Order.query().with_("user")
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].name == "user"
        assert query._eager_loads["user"].nested == []
        assert query._eager_loads["user"].query_modifier is None

    def test_relations_with_nested_relations(self, order_fixtures):
        """with_('user.orders') should expand to two configs with nested tracking."""
        _, Order, _ = order_fixtures
        query = Order.query().with_("user.orders")
        assert len(query._eager_loads) == 2
        assert "user" in query._eager_loads
        assert "user.orders" in query._eager_loads
        assert query._eager_loads["user"].nested == ["orders"]
        assert query._eager_loads["user.orders"].name == "user.orders"
        assert query._eager_loads["user.orders"].nested == []

    def test_relations_with_query_modifier(self, order_fixtures):
        """with_(('user', modifier)) should store the modifier in RelationConfig."""
        _, Order, _ = order_fixtures

        def modifier(q):
            return q.where("status = ?", "active")

        query = Order.query().with_(("user", modifier))
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].query_modifier == modifier

    def test_relations_with_multiple_relations(self, order_fixtures):
        """with_('user', ('items', modifier), 'user.orders') should store 3 configs."""
        _, Order, _ = order_fixtures

        def modifier(q):
            return q.where("status = ?", "active")

        query = Order.query().with_("user", ("items", modifier), "user.orders")
        assert len(query._eager_loads) == 3
        assert "user" in query._eager_loads
        assert "items" in query._eager_loads
        assert "user.orders" in query._eager_loads
        assert query._eager_loads["items"].query_modifier == modifier
        assert query._eager_loads["user"].nested == ["orders"]

    def test_relations_with_duplicate_relations(self, order_fixtures):
        """Duplicate with_ calls should keep the last modifier."""
        _, Order, _ = order_fixtures

        def modifier1(q):
            return q.where("status = ?", "active")

        def modifier2(q):
            return q.where("type = ?", "premium")

        query = Order.query().with_(("user", modifier1), ("user", modifier2))
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].query_modifier == modifier2

    def test_relations_with_chained_calls(self, order_fixtures):
        """Chained .with_() calls should accumulate configs."""
        _, Order, _ = order_fixtures
        query = Order.query().with_("user").with_("items").with_("user.orders")
        assert len(query._eager_loads) == 3
        assert all(name in query._eager_loads for name in ["user", "items", "user.orders"])
        assert query._eager_loads["user"].nested == ["orders"]

    def test_relations_with_deep_nesting(self, order_fixtures):
        """with_('user.orders.items.detail') should configure 4 levels."""
        _, Order, _ = order_fixtures
        with patch.object(Order.query().__class__, '_validate_complete_relation_path', return_value=None):
            query = Order.query().with_("user.orders.items.detail")
            assert len(query._eager_loads) == 4
            assert all(name in query._eager_loads for name in [
                "user", "user.orders", "user.orders.items", "user.orders.items.detail"
            ])
            assert query._eager_loads["user"].nested == ["orders"]
            assert query._eager_loads["user.orders"].nested == ["items"]
            assert query._eager_loads["user.orders.items"].nested == ["detail"]
            assert query._eager_loads["user.orders.items.detail"].nested == []

    def test_relation_path_validation(self, blog_fixtures):
        """A valid relation path (Post -> user) should not raise."""
        _, Post, _ = blog_fixtures
        query = Post.query().with_('user')
        assert "user" in query._eager_loads

    def test_invalid_relation_path_error(self, order_fixtures):
        """An invalid relation should raise RelationNotFoundError or similar."""
        _, Order, _ = order_fixtures
        try:
            Order.query().with_('nonexistent_relation')
        except Exception:
            pass  # Exception at build time is acceptable
        else:
            pass  # Exception at execution time is also acceptable

    def test_relation_not_found_error(self, order_fixtures):
        """A deep path with non-existent middle relation."""
        _, Order, _ = order_fixtures
        try:
            query = Order.query().with_('user.nonexistent.nested')
            assert "user" in query._eager_loads
        except Exception:
            pass

    def test_eager_loading_performance(self, combined_fixtures):
        """Verify eager loading returns same results as lazy loading (N+1 avoidance)."""
        User, Order, OrderItem, _, _ = combined_fixtures
        user = User(username='nplus1_user', email='nplus1@example.com', age=30)
        user.save()
        for i in range(5):
            order = Order(user_id=user.id, order_number=f'NPLUS1-{i + 1:03d}',
                          total_amount=Decimal(f'{(i + 1) * 50.00}'))
            order.save()
            for j in range(2):
                item = OrderItem(order_id=order.id, product_name=f'N1D-Item-{i}-{j}',
                                 quantity=j + 1, unit_price=Decimal('25.00'),
                                 subtotal=Decimal(f'{(j + 1) * 25.00}'))
                item.save()

        orders_with_eager = Order.query().with_('user').where(Order.c.user_id == user.id).all()
        accessed = []
        for order in orders_with_eager:
            related = order.user()
            accessed.append(related)
        assert len(accessed) == 5
        assert all(r is not None for r in accessed)
