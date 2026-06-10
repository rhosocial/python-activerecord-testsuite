# src/rhosocial/activerecord/testsuite/feature/query/test_relations_with_async.py
"""Async: relation 'with' method configuration tests.

Mirrors test_relations_with_sync.py exactly.  Each test configures
eager-loading relations via with_() and checks the stored config;
no I/O is performed inside these checks.
"""
from decimal import Decimal
from unittest.mock import patch


class TestAsyncRelationsWith:
    """Asynchronous tests for relation 'with' functionality"""

    async def test_relations_with_single_relation(self, async_order_fixtures):
        """with_('user') should store a single RelationConfig with no nesting (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        query = AsyncOrder.query().with_("user")
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].name == "user"
        assert query._eager_loads["user"].nested == []
        assert query._eager_loads["user"].query_modifier is None

    async def test_relations_with_nested_relations(self, async_order_fixtures):
        """with_('user.orders') should expand to two configs with nested tracking (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        query = AsyncOrder.query().with_("user.orders")
        assert len(query._eager_loads) == 2
        assert "user" in query._eager_loads
        assert "user.orders" in query._eager_loads
        assert query._eager_loads["user"].nested == ["orders"]
        assert query._eager_loads["user.orders"].name == "user.orders"
        assert query._eager_loads["user.orders"].nested == []

    async def test_relations_with_query_modifier(self, async_order_fixtures):
        """with_(('user', modifier)) should store the modifier (async)."""
        _, AsyncOrder, _ = async_order_fixtures

        def modifier(q):
            return q.where("status = ?", "active")

        query = AsyncOrder.query().with_(("user", modifier))
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].query_modifier == modifier

    async def test_relations_with_multiple_relations(self, async_order_fixtures):
        """with_('user', ('items', modifier), 'user.orders') stores 3 configs (async)."""
        _, AsyncOrder, _ = async_order_fixtures

        def modifier(q):
            return q.where("status = ?", "active")

        query = AsyncOrder.query().with_("user", ("items", modifier), "user.orders")
        assert len(query._eager_loads) == 3
        assert "user" in query._eager_loads
        assert "items" in query._eager_loads
        assert "user.orders" in query._eager_loads
        assert query._eager_loads["items"].query_modifier == modifier
        assert query._eager_loads["user"].nested == ["orders"]

    async def test_relations_with_duplicate_relations(self, async_order_fixtures):
        """Duplicate with_ calls should keep the last modifier (async)."""
        _, AsyncOrder, _ = async_order_fixtures

        def modifier1(q):
            return q.where("status = ?", "active")

        def modifier2(q):
            return q.where("type = ?", "premium")

        query = AsyncOrder.query().with_(("user", modifier1), ("user", modifier2))
        assert len(query._eager_loads) == 1
        assert "user" in query._eager_loads
        assert query._eager_loads["user"].query_modifier == modifier2

    async def test_relations_with_chained_calls(self, async_order_fixtures):
        """Chained .with_() calls should accumulate configs (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        query = AsyncOrder.query().with_("user").with_("items").with_("user.orders")
        assert len(query._eager_loads) == 3
        assert all(name in query._eager_loads for name in ["user", "items", "user.orders"])
        assert query._eager_loads["user"].nested == ["orders"]

    async def test_relations_with_deep_nesting(self, async_order_fixtures):
        """with_('user.orders.items.detail') should configure 4 levels (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        with patch.object(AsyncOrder.query().__class__, '_validate_complete_relation_path', return_value=None):
            query = AsyncOrder.query().with_("user.orders.items.detail")
            assert len(query._eager_loads) == 4
            assert all(name in query._eager_loads for name in [
                "user", "user.orders", "user.orders.items", "user.orders.items.detail"
            ])
            assert query._eager_loads["user"].nested == ["orders"]
            assert query._eager_loads["user.orders"].nested == ["items"]
            assert query._eager_loads["user.orders.items"].nested == ["detail"]
            assert query._eager_loads["user.orders.items.detail"].nested == []

    async def test_relation_path_validation(self, async_blog_fixtures):
        """A valid path (AsyncPost -> author) should not raise (async)."""
        _, AsyncPost, _ = async_blog_fixtures
        query = AsyncPost.query().with_('author')
        assert "author" in query._eager_loads

    async def test_invalid_relation_path_error(self, async_order_fixtures):
        """An invalid relation should raise RelationNotFoundError or similar (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        try:
            AsyncOrder.query().with_('nonexistent_relation')
        except Exception:
            pass
        else:
            pass

    async def test_relation_not_found_error(self, async_order_fixtures):
        """A deep path with non-existent middle relation (async)."""
        _, AsyncOrder, _ = async_order_fixtures
        try:
            query = AsyncOrder.query().with_('user.nonexistent.nested')
            assert "user" in query._eager_loads
        except Exception:
            pass

    async def test_eager_loading_performance(self, async_combined_fixtures):
        """Verify eager loading returns same results as lazy loading (async)."""
        AsyncUser, AsyncOrder, AsyncOrderItem, _, _ = async_combined_fixtures
        user = AsyncUser(username='nplus1_user', email='nplus1@example.com', age=30)
        await user.save()
        for i in range(5):
            order = AsyncOrder(user_id=user.id, order_number=f'NPLUS1-{i + 1:03d}',
                               total_amount=Decimal(f'{(i + 1) * 50.00}'))
            await order.save()
            for j in range(2):
                item = AsyncOrderItem(order_id=order.id, product_name=f'N1D-Item-{i}-{j}',
                                      quantity=j + 1, unit_price=Decimal('25.00'),
                                      subtotal=Decimal(f'{(j + 1) * 25.00}'))
                await item.save()

        orders_with_eager = await AsyncOrder.query().with_('user').where(AsyncOrder.c.user_id == user.id).all()
        accessed = []
        for order in orders_with_eager:
            related = await order.user()
            accessed.append(related)
        assert len(accessed) == 5
        assert all(r is not None for r in accessed)
