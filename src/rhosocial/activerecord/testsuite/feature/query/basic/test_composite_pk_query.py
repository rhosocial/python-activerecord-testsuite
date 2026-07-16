# src/rhosocial/activerecord/testsuite/feature/query/basic/test_composite_pk_query.py
from decimal import Decimal
import pytest

from rhosocial.activerecord.backend.expression.core import Column
from rhosocial.activerecord.backend.expression import ComparisonPredicate, Literal
class TestActiveQueryCompositePK:
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
        predicate = order_item_class._build_pk_where_predicate({"order_id": 1, "product_id": 101})
        result = order_item_class.query().where(predicate).one()
        assert result is not None
        assert result.order_id == 1
        assert result.product_id == 101

    def test_where_single_column(self, seeded, order_item_class):
        backend = order_item_class.backend()
        results = order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).all()
        assert len(results) == 2

    def test_where_and_condition(self, seeded, order_item_class):
        backend = order_item_class.backend()
        results = order_item_class.query().where(
            Column(backend.dialect, "order_id") == 1
        ).where(
            Column(backend.dialect, "quantity") > 1
        ).all()
        assert len(results) == 1
        assert results[0].product_id == 101

    def test_order_limit(self, seeded, order_item_class):
        results = order_item_class.query().order_by("product_id").limit(2).all()
        assert len(results) == 2

    def test_count(self, seeded, order_item_class):
        count = order_item_class.query().count()
        assert count == 4

    def test_explain(self, seeded, order_item_class):
        result = order_item_class.query().explain().aggregate()
        assert isinstance(result, list)
        assert len(result) > 0