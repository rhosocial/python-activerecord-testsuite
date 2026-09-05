# src/rhosocial/activerecord/testsuite/feature/query/basic/test_composite_pk_query.py
"""Tests for ActiveQuery operations on models with composite primary keys."""
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression import ComparisonPredicate, Literal
class TestActiveQueryCompositePK:
    """Test ActiveQuery operations against models with composite primary keys."""

    @pytest.fixture
    def seeded(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
            order_item_class(order_id=2, product_id=103, quantity=3, unit_price=Decimal("25.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    def test_where_pk_predicate(self, seeded, order_item_class):
        """Querying by the full composite key predicate should return the matching record."""
        predicate = order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        result = order_item_class.query().where(predicate).one()
        assert result is not None, "Expected to find the record by composite key"
        assert result.order_id == 1, "Expected order_id to be 1"
        assert result.product_id == 101, "Expected product_id to be 101"

    def test_where_single_column(self, seeded, order_item_class):
        """Filtering by a single composite key column should return matching rows."""
        backend = order_item_class.backend()
        results = order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).all()
        assert len(results) == 2, "Expected 2 rows with order_id == 1"

    def test_where_and_condition(self, seeded, order_item_class):
        """Combining multiple where clauses should apply both filters."""
        backend = order_item_class.backend()
        results = order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).where(
            Column(backend.dialect, "quantity") > 1
        ).all()
        assert len(results) == 1, "Expected 1 row matching both conditions"
        assert results[0].product_id == 101, "Expected product_id to be 101"

    def test_order_limit(self, seeded, order_item_class):
        """Ordering with limit should respect the configured row cap."""
        results = order_item_class.query().order_by("product_id").limit(2).all()
        assert len(results) == 2, "Expected 2 rows after limit"

    def test_count(self, seeded, order_item_class):
        """count() should return the total number of seeded records."""
        count = order_item_class.query().count()
        assert count == 4, "Expected count to be 4"

    def test_explain(self, seeded, order_item_class):
        """explain() should return a non-empty plan list when supported."""
        if not order_item_class.backend().dialect.supports_explain_plan():
            pytest.skip("Backend dialect does not support explain plan")
        result = order_item_class.query().explain().aggregate()
        assert isinstance(result, list), "Expected explain() result to be a list"
        assert len(result) > 0, "Expected explain() result to be non-empty"