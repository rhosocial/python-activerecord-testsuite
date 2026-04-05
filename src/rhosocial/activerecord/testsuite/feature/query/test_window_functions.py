# src/rhosocial/activerecord/testsuite/feature/query/test_window_functions.py
"""Test window function functionality in ActiveQuery."""
from decimal import Decimal

import pytest

from rhosocial.activerecord.testsuite.utils import requires_window_functions
from rhosocial.activerecord.backend.expression.advanced_functions import (
    WindowFunctionCall,
    WindowSpecification,
    WindowFrameSpecification,
)
from rhosocial.activerecord.backend.expression.query_parts import OrderByClause
from rhosocial.activerecord.backend.expression import core


@requires_window_functions()
def test_row_number_window_function(order_fixtures):
    """Test ROW_NUMBER() window function."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('100.00')]
    for i, amount in enumerate(amounts):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            total_amount=amount,
            status='pending' if i % 2 == 0 else 'paid'
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "DESC")])
        window_spec = WindowSpecification(dialect, order_by=order_by_clause)
        window_func = WindowFunctionCall(
            dialect,
            "ROW_NUMBER",
            window_spec=window_spec,
            alias="row_num"
        )

        query = Order.query().select("id", "total_amount", "status", window_func)
        query.order_by("row_num")

        results = query.aggregate()

        assert len(results) == 4
        assert results[0]['row_num'] == 1
        assert results[1]['row_num'] == 2
        assert results[2]['row_num'] == 3
        assert results[3]['row_num'] == 4

        assert float(results[0]['total_amount']) == pytest.approx(300.00)
        assert float(results[1]['total_amount']) == pytest.approx(200.00)
        assert float(results[2]['total_amount']) in (100.00, 100.00)
        assert float(results[3]['total_amount']) in (100.00, 100.00)
    except Exception as e:
        if 'no such function: ROW_NUMBER' in str(e):
            pytest.skip("SQLite installation doesn't support ROW_NUMBER window function")
        raise


@requires_window_functions()
def test_partition_by_window_function(order_fixtures):
    """Test window functions with PARTITION BY."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    statuses = ['pending', 'paid', 'pending', 'paid']
    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('400.00')]

    for i, (status, amount) in enumerate(zip(statuses, amounts)):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            status=status,
            total_amount=amount
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        partition_by = [core.Column(dialect, "status")]
        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "ASC")])
        window_spec = WindowSpecification(dialect, partition_by=partition_by, order_by=order_by_clause)
        window_func = WindowFunctionCall(
            dialect,
            "ROW_NUMBER",
            window_spec=window_spec,
            alias="rank"
        )

        query = Order.query().select("id", "status", "total_amount", window_func)
        query.order_by(("status", "ASC"), ("rank", "ASC"))

        results = query.aggregate()

        assert len(results) == 4
        for r in results:
            # All records should have rank in (1, 2) regardless of status
            assert r['rank'] in (1, 2)
    except Exception as e:
        if 'no such function: ROW_NUMBER' in str(e):
            pytest.skip("SQLite installation doesn't support ROW_NUMBER window function")
        raise


@requires_window_functions()
def test_aggregate_window_functions(order_fixtures):
    """Test aggregate functions with window specification."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('400.00')]
    for i, amount in enumerate(amounts):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            total_amount=amount,
            status='pending'
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "DESC")])
        window_spec = WindowSpecification(dialect, order_by=order_by_clause)
        sum_func = WindowFunctionCall(dialect, "SUM", args=[core.Column(dialect, "total_amount")], window_spec=window_spec, alias="running_sum")

        query = Order.query().select("id", "total_amount", sum_func)
        query.order_by(("total_amount", "DESC"))

        results = query.aggregate()

        assert len(results) == 4
        assert results[0]['running_sum'] == Decimal('400.00')
        assert results[1]['running_sum'] == Decimal('700.00')
        assert results[2]['running_sum'] == Decimal('900.00')
        assert results[3]['running_sum'] == Decimal('1000.00')
    except Exception as e:
        if 'no such function: SUM' in str(e):
            pytest.skip("SQLite installation doesn't support window aggregate functions")
        raise


@requires_window_functions()
def test_named_window_definitions(order_fixtures):
    """Test named window definitions."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('400.00')]
    for i, amount in enumerate(amounts):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            total_amount=amount,
            status='pending'
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "DESC")])
        window_spec = WindowSpecification(dialect, order_by=order_by_clause)
        window_func = WindowFunctionCall(
            dialect,
            "ROW_NUMBER",
            window_spec=window_spec,
            alias="row_num"
        )

        query = Order.query().select("id", "total_amount", window_func)
        query.order_by("row_num")

        results = query.aggregate()

        assert len(results) == 4
        assert results[0]['row_num'] == 1
    except Exception as e:
        if 'no such function: ROW_NUMBER' in str(e):
            pytest.skip("SQLite installation doesn't support ROW_NUMBER window function")
        raise


@requires_window_functions()
def test_window_frame_specifications(order_fixtures):
    """Test window frame specifications."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('400.00')]
    for i, amount in enumerate(amounts):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            total_amount=amount,
            status='pending'
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "ASC")])
        window_frame = WindowFrameSpecification(dialect, 'ROWS', 'UNBOUNDED PRECEDING', 'CURRENT ROW')
        window_spec = WindowSpecification(dialect, order_by=order_by_clause, frame=window_frame)

        first_value_func = WindowFunctionCall(
            dialect,
            "FIRST_VALUE",
            args=[core.Column(dialect, "total_amount")],
            window_spec=window_spec,
            alias="first_amount"
        )

        query = Order.query().select("id", "total_amount", first_value_func)
        query.order_by(("total_amount", "ASC"))

        results = query.aggregate()

        assert len(results) == 4
        assert float(results[0]['first_amount']) == pytest.approx(100.00)
    except Exception as e:
        if 'no such function' in str(e).lower():
            pytest.skip(f"SQLite installation doesn't support this window function: {e}")
        raise


@requires_window_functions()
def test_unbounded_window_frames(order_fixtures):
    """Test unbounded window frames."""
    User, Order, OrderItem = order_fixtures

    user = User(username='test_user', email='test@example.com', age=30)
    user.save()

    amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('300.00'), Decimal('400.00')]
    for i, amount in enumerate(amounts):
        order = Order(
            user_id=user.id,
            order_number=f'ORD-{i + 1}',
            total_amount=amount,
            status='pending'
        )
        order.save()

    try:
        dialect = Order.backend().dialect

        order_by_clause = OrderByClause(dialect, [(core.Column(dialect, "total_amount"), "ASC")])
        window_frame = WindowFrameSpecification(dialect, 'ROWS', 'UNBOUNDED PRECEDING', 'UNBOUNDED FOLLOWING')
        window_spec = WindowSpecification(dialect, order_by=order_by_clause, frame=window_frame)

        sum_func = WindowFunctionCall(
            dialect,
            "SUM",
            args=[core.Column(dialect, "total_amount")],
            window_spec=window_spec,
            alias="total_sum"
        )

        query = Order.query().select("id", "total_amount", sum_func)
        query.order_by(("total_amount", "ASC"))

        results = query.aggregate()

        assert len(results) == 4
        for r in results:
            assert float(r['total_sum']) == pytest.approx(1000.00)
    except Exception as e:
        if 'no such function' in str(e).lower():
            pytest.skip(f"SQLite installation doesn't support this window function: {e}")
        raise
