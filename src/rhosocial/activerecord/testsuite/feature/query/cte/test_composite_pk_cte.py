# src/rhosocial/activerecord/testsuite/feature/query/cte/test_composite_pk_cte.py
"""Tests for CTE query operations on models with composite primary keys."""
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.dialect.exceptions import UnsupportedFeatureError
class TestCTEQueryCompositePK:
    """Test CTE query operations against models with composite primary keys."""

    @pytest.fixture
    def seeded(self, order_item_class):
        items = [
            order_item_class(order_id=1, product_id=101, quantity=2, unit_price=Decimal("10.00")),
            order_item_class(order_id=1, product_id=102, quantity=1, unit_price=Decimal("20.00")),
            order_item_class(order_id=2, product_id=101, quantity=5, unit_price=Decimal("15.00")),
        ]
        order_item_class.bulk_create(items)
        return items

    def test_cte_aggregate(self, seeded, order_item_class):
        """A CTE wrapping the base composite-key query should aggregate over filtered rows."""
        backend = order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_basic_cte():
            pytest.skip("Backend does not support CTE")

        from rhosocial.activerecord.query import CTEQuery
        from rhosocial.activerecord.backend.expression import Column, Literal

        base = order_item_class.query()
        cte = CTEQuery(backend)
        cte.with_cte("order_summary", base)
        result = cte.from_cte("order_summary").select(
            Column(dialect, "order_id"), Column(dialect, "quantity")
        ).where(Column(dialect, "order_id") == 1).aggregate()
        assert len(result) == 2, "Expected 2 aggregated rows for order_id == 1"

    def test_cte_pk_filter(self, seeded, order_item_class):
        """A CTE built on the composite key predicate should return the matching row."""
        backend = order_item_class.backend()
        dialect = backend.dialect
        if not dialect.supports_basic_cte():
            pytest.skip("Backend does not support CTE")

        from rhosocial.activerecord.query import CTEQuery

        predicate = order_item_class._build_pk_where_predicate(
            {"order_id": 1, "product_id": 101}
        )
        base = order_item_class.query().where(predicate)
        cte = CTEQuery(backend)
        cte.with_cte("single_item", base)
        result = cte.from_cte("single_item").aggregate()
        assert len(result) == 1, "Expected 1 CTE row for the composite key"

    def test_cte_unsupported_backend(self, order_item_class):
        """CTEQuery should raise UnsupportedFeatureError when the backend lacks CTE."""
        backend = order_item_class.backend()
        dialect = backend.dialect
        if dialect.supports_basic_cte():
            pytest.skip("Backend supports CTE, can't test unsupported path")

        from rhosocial.activerecord.query import CTEQuery
        with pytest.raises(UnsupportedFeatureError):
            CTEQuery(backend)