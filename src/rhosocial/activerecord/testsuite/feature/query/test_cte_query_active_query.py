"""
CTE Query ActiveQuery tests to verify CTE functionality with ActiveQuery as subqueries.

This module tests Common Table Expression (CTE) queries where the subqueries
are ActiveQuery instances. It includes tests for:
- Single ActiveQuery as CTE
- Multiple ActiveQuery instances as CTEs
Both synchronous and asynchronous versions are included.
"""
import pytest
from decimal import Decimal

from rhosocial.activerecord.query import CTEQuery, AsyncCTEQuery
from rhosocial.activerecord.testsuite.utils import requires_cte, requires_recursive_cte


class TestCTEQueryActiveQuery:
    """Test CTE queries with ActiveQuery subqueries (synchronous)."""

    @requires_cte()
    def test_single_active_query_cte(self, tree_fixtures):
        """Test basic CTE with a single ActiveQuery as subquery."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node

        Node = tree_fixtures[0]

        # Get backend from Node model
        backend = Node.backend()

        # Clean up any existing data
        for node in Node.query().all():
            node.delete()

        # Create test data
        root = Node(name="Root", value=Decimal('100.0'))
        root.save()

        child1 = Node(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        child1.save()

        child2 = Node(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        child2.save()

        grandchild = Node(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        grandchild.save()

        # Create a CTE using ActiveQuery as subquery
        cte_subquery = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value >= Decimal('50'))

        # Create CTEQuery instance with backend
        cte_query = CTEQuery(backend)
        cte_query.with_cte(name="high_value_nodes", query=cte_subquery)

        # Execute the CTE query using aggregate method
        result = cte_query.from_cte("high_value_nodes").select("name", "value").aggregate()

        assert len(result) == 3  # root, child1, child2
        # Check the actual structure of the result
        names = sorted([r['name'] for r in result])
        assert names == ["Child1", "Child2", "Root"]

    @requires_cte()
    def test_multiple_active_query_cte(self, tree_fixtures):
        """Test CTE with multiple ActiveQuery instances as subqueries."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.cte_models import Node

        Node = tree_fixtures[0]

        # Get backend from Node model
        backend = Node.backend()

        # Clean up any existing data
        for node in Node.query().all():
            node.delete()

        # Create test data
        root = Node(name="Root", value=Decimal('100.0'))
        root.save()

        child1 = Node(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        child1.save()

        child2 = Node(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        child2.save()

        grandchild = Node(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        grandchild.save()

        # Create multiple CTEs using ActiveQuery as subqueries
        high_value_cte = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value >= Decimal('60'))
        low_value_cte = Node.query().select(Node.c.id, Node.c.name, Node.c.value).where(Node.c.value < Decimal('60'))

        # Create CTEQuery instance with multiple CTEs
        cte_query = CTEQuery(backend)
        cte_query.with_cte(name="high_values", query=high_value_cte)
        cte_query.with_cte(name="low_values", query=low_value_cte)

        # Execute the CTE query using aggregate method
        result = cte_query.from_cte("high_values").select("name", "value").aggregate()

        assert len(result) >= 2  # Should have results from the high_values CTE


class TestAsyncCTEQueryActiveQuery:
    """Test CTE queries with ActiveQuery subqueries (asynchronous)."""

    @pytest.mark.asyncio
    @requires_cte()
    async def test_single_active_query_cte(self, async_tree_fixtures):
        """Test basic CTE with a single ActiveQuery as subquery (async version)."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode

        AsyncNode = async_tree_fixtures[0]

        # Get backend from AsyncNode model
        backend = AsyncNode.backend()

        # Clean up any existing data
        for node in await AsyncNode.query().all():
            await node.delete()

        # Create test data
        root = AsyncNode(name="Root", value=Decimal('100.0'))
        await root.save()

        child1 = AsyncNode(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        await child1.save()

        child2 = AsyncNode(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        await child2.save()

        grandchild = AsyncNode(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        await grandchild.save()

        # Create a CTE using ActiveQuery as subquery
        cte_subquery = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value >= Decimal('50'))

        # Create AsyncCTEQuery instance with backend
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte(name="high_value_nodes", query=cte_subquery)

        # Execute the CTE query using aggregate method
        result = await cte_query.from_cte("high_value_nodes").select("name", "value").aggregate()

        assert len(result) == 3  # root, child1, child2
        # Check the actual structure of the result
        names = sorted([r['name'] for r in result])
        assert names == ["Child1", "Child2", "Root"]

    @pytest.mark.asyncio
    @requires_cte()
    async def test_multiple_active_query_cte(self, async_tree_fixtures):
        """Test CTE with multiple ActiveQuery instances as subqueries (async version)."""
        from rhosocial.activerecord.testsuite.feature.query.fixtures.async_cte_models import AsyncNode

        AsyncNode = async_tree_fixtures[0]

        # Get backend from AsyncNode model
        backend = AsyncNode.backend()

        # Clean up any existing data
        for node in await AsyncNode.query().all():
            await node.delete()

        # Create test data
        root = AsyncNode(name="Root", value=Decimal('100.0'))
        await root.save()

        child1 = AsyncNode(name="Child1", value=Decimal('50.0'), parent_id=root.id)
        await child1.save()

        child2 = AsyncNode(name="Child2", value=Decimal('75.0'), parent_id=root.id)
        await child2.save()

        grandchild = AsyncNode(name="GrandChild1", value=Decimal('25.0'), parent_id=child1.id)
        await grandchild.save()

        # Create multiple CTEs using ActiveQuery as subqueries
        high_value_cte = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value >= Decimal('60'))
        low_value_cte = AsyncNode.query().select(AsyncNode.c.id, AsyncNode.c.name, AsyncNode.c.value).where(AsyncNode.c.value < Decimal('60'))

        # Create AsyncCTEQuery instance with multiple CTEs
        cte_query = AsyncCTEQuery(backend)
        cte_query.with_cte(name="high_values", query=high_value_cte)
        cte_query.with_cte(name="low_values", query=low_value_cte)

        # Execute the CTE query using aggregate method
        result = await cte_query.from_cte("high_values").select("name", "value").aggregate()

        assert len(result) >= 2  # Should have results from the high_values CTE