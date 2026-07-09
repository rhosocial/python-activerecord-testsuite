# src/rhosocial/activerecord/testsuite/feature/query/worker/test_parallel_queries_async.py
"""
Test WorkerPool integration with parallel query operations.

IMPORTANT:
- All task functions must be module-level pickle-able functions
- Tests require `if __name__ == '__main__'` guard for multiprocessing
- Provider must implement WorkerTestProtocol for these tests to work
"""
from typing import Dict, Any, List
from decimal import Decimal

import pytest
from rhosocial.activerecord.worker import WorkerPool, TaskContext


# ─────────────────────────────────────────────────────────────────────────────
# Synchronous Task Functions
# ─────────────────────────────────────────────────────────────────────────────

def count_users_task(ctx: TaskContext, conn_params: Dict) -> int:
    """Count all users in database."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.models import User

    User.configure(config, backend_class)

    try:
        return User.query().count()
    finally:
        User.backend().disconnect()


def count_orders_task(ctx: TaskContext, conn_params: Dict) -> int:
    """Count all orders in database."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.models import Order

    Order.configure(config, backend_class)

    try:
        return Order.query().count()
    finally:
        Order.backend().disconnect()


def query_orders_by_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> List[Dict[str, Any]]:
    """Query orders for a specific user."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.models import Order

    Order.configure(config, backend_class)

    try:
        orders = Order.where(user_id=user_id).all()
        return [
            {
                'id': o.id,
                'order_number': o.order_number,
                'total_amount': float(o.total_amount),
                'status': o.status
            }
            for o in orders
        ]
    finally:
        Order.backend().disconnect()


def aggregate_query_task(ctx: TaskContext, conn_params: Dict) -> Dict[str, Any]:
    """Execute aggregate queries on orders."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.models import Order

    Order.configure(config, backend_class)

    try:
        total = Order.query().sum_('total_amount')
        count = Order.query().count()
        avg = Order.query().avg('total_amount')
        return {
            'total': float(total or 0),
            'count': count,
            'average': float(avg or 0)
        }
    finally:
        Order.backend().disconnect()


def query_order_items_task(ctx: TaskContext, order_id: int, conn_params: Dict) -> List[Dict[str, Any]]:
    """Query items for a specific order."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.models import OrderItem

    OrderItem.configure(config, backend_class)

    try:
        items = OrderItem.where(order_id=order_id).all()
        return [
            {
                'id': i.id,
                'product_name': i.product_name,
                'quantity': i.quantity,
                'unit_price': float(i.unit_price)
            }
            for i in items
        ]
    finally:
        OrderItem.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Asynchronous Task Functions
# ─────────────────────────────────────────────────────────────────────────────

async def async_count_users_task(ctx: TaskContext, conn_params: Dict) -> int:
    """Count all users in database (async)."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncUser

    await AsyncUser.configure(config, backend_class)

    try:
        return await AsyncUser.query().count()
    finally:
        await AsyncUser.backend().disconnect()


async def async_count_orders_task(ctx: TaskContext, conn_params: Dict) -> int:
    """Count all orders in database (async)."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncOrder

    await AsyncOrder.configure(config, backend_class)

    try:
        return await AsyncOrder.query().count()
    finally:
        await AsyncOrder.backend().disconnect()


async def async_query_orders_by_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> List[Dict[str, Any]]:
    """Query orders for a specific user (async)."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncOrder

    await AsyncOrder.configure(config, backend_class)

    try:
        orders = await AsyncOrder.where(user_id=user_id).all()
        return [
            {
                'id': o.id,
                'order_number': o.order_number,
                'total_amount': float(o.total_amount),
                'status': o.status
            }
            for o in orders
        ]
    finally:
        await AsyncOrder.backend().disconnect()


async def async_aggregate_query_task(ctx: TaskContext, conn_params: Dict) -> Dict[str, Any]:
    """Execute aggregate queries on orders (async)."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncOrder

    await AsyncOrder.configure(config, backend_class)

    try:
        total = await AsyncOrder.query().sum_('total_amount')
        count = await AsyncOrder.query().count()
        avg = await AsyncOrder.query().avg('total_amount')
        return {
            'total': float(total or 0),
            'count': count,
            'average': float(avg or 0)
        }
    finally:
        await AsyncOrder.backend().disconnect()


async def async_query_order_items_task(ctx: TaskContext, order_id: int, conn_params: Dict) -> List[Dict[str, Any]]:
    """Query items for a specific order (async)."""
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import AsyncOrderItem

    await AsyncOrderItem.configure(config, backend_class)

    try:
        items = await AsyncOrderItem.where(order_id=order_id).all()
        return [
            {
                'id': i.id,
                'product_name': i.product_name,
                'quantity': i.quantity,
                'unit_price': float(i.unit_price)
            }
            for i in items
        ]
    finally:
        await AsyncOrderItem.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes - Synchronous
# ─────────────────────────────────────────────────────────────────────────────
class TestAsyncParallelQueries:
    """Test parallel query operations with asynchronous models."""

    async def test_parallel_count_queries(self, async_order_fixtures_for_worker):
        """Test parallel async count queries."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures_for_worker['models']
        conn_params = async_order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_count_users_task, conn_params)
                for _ in range(10)
            ]
            results = [f.result(timeout=60) for f in futures]

        assert len(set(results)) == 1

    async def test_parallel_order_queries_by_user(self, async_order_fixtures_for_worker):
        """Test parallel async queries for orders by user."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures_for_worker['models']
        conn_params = async_order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Use the same event loop as the fixture
        users = await AsyncUser.query().limit(5).all()
        user_ids = [u.id for u in users]

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_query_orders_by_user_task, uid, conn_params)
                for uid in user_ids
            ]
            results = [f.result(timeout=60) for f in futures]

        assert len(results) == len(user_ids)
        assert all(isinstance(r, list) for r in results)

    async def test_parallel_aggregate_queries(self, async_order_fixtures_for_worker):
        """Test parallel async aggregate queries."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures_for_worker['models']
        conn_params = async_order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_aggregate_query_task, conn_params)
                for _ in range(5)
            ]
            results = [f.result(timeout=60) for f in futures]

        totals = {r['total'] for r in results}
        counts = {r['count'] for r in results}
        assert len(totals) == 1
        assert len(counts) == 1

    async def test_parallel_order_item_queries(self, async_order_fixtures_for_worker):
        """Test parallel async queries for order items."""
        AsyncUser, AsyncOrder, AsyncOrderItem = async_order_fixtures_for_worker['models']
        conn_params = async_order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        orders = await AsyncOrder.query().limit(5).all()
        order_ids = [o.id for o in orders]

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_query_order_items_task, oid, conn_params)
                for oid in order_ids
            ]
            results = [f.result(timeout=60) for f in futures]

        assert len(results) == len(order_ids)