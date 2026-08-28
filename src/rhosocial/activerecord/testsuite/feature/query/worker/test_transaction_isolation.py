# src/rhosocial/activerecord/testsuite/feature/query/worker/test_transaction_isolation.py
"""
Test WorkerPool transaction isolation in parallel operations.

Each Worker process has independent database connections, so transactions
are isolated within each process. This module tests that transaction
behavior is correct in Worker processes.

IMPORTANT:
- All task functions must be module-level pickle-able functions
- Tests require `if __name__ == '__main__'` guard for multiprocessing
- Provider must implement WorkerTestProtocol for these tests to work
"""
from typing import Dict, Any
from decimal import Decimal

import pytest
from rhosocial.activerecord.worker import WorkerPool, TaskContext

pytestmark = pytest.mark.serial



# ─────────────────────────────────────────────────────────────────────────────
# Synchronous Task Functions
# ─────────────────────────────────────────────────────────────────────────────

def transfer_balance_task(
    ctx: TaskContext,
    from_user_id: int,
    to_user_id: int,
    amount: float,
    conn_params: Dict
) -> Dict[str, Any]:
    """
    Execute a balance transfer within a transaction.

    Args:
        ctx: Worker task context
        from_user_id: Source user ID
        to_user_id: Target user ID
        amount: Amount to transfer
        conn_params: Worker connection parameters

    Returns:
        Dict with success status and details
    """
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
        backend = User.backend()

        # Check if FOR UPDATE is supported by this backend
        supports_for_update = backend.dialect.supports_for_update()

        backend.begin_transaction()

        try:
            if supports_for_update:
                # CRITICAL: Use fixed lock order to prevent lost updates and deadlocks
                # Always lock users in ascending ID order
                first_id, second_id = (
                    (from_user_id, to_user_id) if from_user_id < to_user_id else (to_user_id, from_user_id)
                )

                # Lock rows without single-row wrappers that some backends cannot lock.
                first_matches = User.query().where(User.c.id == first_id).for_update().all()
                second_matches = User.query().where(User.c.id == second_id).for_update().all()
                first_user = first_matches[0] if first_matches else None
                second_user = second_matches[0] if second_matches else None

                if not first_user or not second_user:
                    raise ValueError("User not found")

                # Determine which is source and which is target
                if from_user_id < to_user_id:
                    from_user, to_user = first_user, second_user
                else:
                    from_user, to_user = second_user, first_user

                if from_user.balance < amount:
                    raise ValueError("Insufficient balance")

                from_user.balance -= amount
                to_user.balance += amount

                from_user.save()
                to_user.save()
            else:
                # Backends without FOR UPDATE (e.g. SQLite, Oracle) cannot rely on row
                # locks. Use atomic conditional UPDATEs instead: each statement serializes
                # on the row and recomputes the balance from the current committed value,
                # so concurrent transfers never overwrite a stale balance (lost update).
                from_affected = User.query().where(
                    (User.c.id == from_user_id) & (User.c.balance >= amount)
                ).update_all({"balance": User.c.balance - amount})
                if from_affected == 0:
                    raise ValueError("Insufficient balance")

                to_affected = User.query().where(
                    User.c.id == to_user_id
                ).update_all({"balance": User.c.balance + amount})
                if to_affected == 0:
                    raise ValueError("User not found")

            backend.commit_transaction()

            from_user = User.find_one({'id': from_user_id})
            to_user = User.find_one({'id': to_user_id})
            return {
                'success': True,
                'from_balance': from_user.balance if from_user else None,
                'to_balance': to_user.balance if to_user else None
            }
        except Exception as e:
            backend.rollback_transaction()
            return {'success': False, 'error': str(e)}
    finally:
        User.backend().disconnect()


def get_balance_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> float:
    """Get user balance."""
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
        user = User.find_one({'id': user_id})
        return user.balance if user else -1
    finally:
        User.backend().disconnect()


def update_order_status_task(
    ctx: TaskContext,
    order_id: int,
    new_status: str,
    conn_params: Dict
) -> Dict[str, Any]:
    """
    Update order status within a transaction.

    Args:
        order_id: Order ID to update
        new_status: New status value
        conn_params: Worker connection parameters

    Returns:
        Dict with success status
    """
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
        backend = Order.backend()
        backend.begin_transaction()

        try:
            order = Order.find_one({'id': order_id})
            if not order:
                raise ValueError("Order not found")

            order.status = new_status
            order.save()

            backend.commit_transaction()

            return {'success': True, 'order_id': order_id, 'status': new_status}
        except Exception as e:
            backend.rollback_transaction()
            return {'success': False, 'error': str(e)}
    finally:
        Order.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Asynchronous Task Functions
# ─────────────────────────────────────────────────────────────────────────────

async def async_transfer_balance_task(
    ctx: TaskContext,
    from_user_id: int,
    to_user_id: int,
    amount: float,
    conn_params: Dict
) -> Dict[str, Any]:
    """
    Execute a balance transfer within a transaction (async).
    """
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
        backend = AsyncUser.backend()

        # Check if FOR UPDATE is supported by this backend
        supports_for_update = backend.dialect.supports_for_update()

        await backend.begin_transaction()

        try:
            if supports_for_update:
                # CRITICAL: Use fixed lock order to prevent lost updates and deadlocks
                # Always lock users in ascending ID order
                first_id, second_id = (
                    (from_user_id, to_user_id) if from_user_id < to_user_id else (to_user_id, from_user_id)
                )

                # Lock rows without single-row wrappers that some backends cannot lock.
                first_matches = await AsyncUser.query().where(AsyncUser.c.id == first_id).for_update().all()
                second_matches = await AsyncUser.query().where(AsyncUser.c.id == second_id).for_update().all()
                first_user = first_matches[0] if first_matches else None
                second_user = second_matches[0] if second_matches else None

                if not first_user or not second_user:
                    raise ValueError("User not found")

                # Determine which is source and which is target
                if from_user_id < to_user_id:
                    from_user, to_user = first_user, second_user
                else:
                    from_user, to_user = second_user, first_user

                if from_user.balance < amount:
                    raise ValueError("Insufficient balance")

                from_user.balance -= amount
                to_user.balance += amount

                await from_user.save()
                await to_user.save()
            else:
                # Backends without FOR UPDATE (e.g. SQLite, Oracle) cannot rely on row
                # locks. Use atomic conditional UPDATEs instead: each statement serializes
                # on the row and recomputes the balance from the current committed value,
                # so concurrent transfers never overwrite a stale balance (lost update).
                from_affected = await AsyncUser.query().where(
                    (AsyncUser.c.id == from_user_id) & (AsyncUser.c.balance >= amount)
                ).update_all({"balance": AsyncUser.c.balance - amount})
                if from_affected == 0:
                    raise ValueError("Insufficient balance")

                to_affected = await AsyncUser.query().where(
                    AsyncUser.c.id == to_user_id
                ).update_all({"balance": AsyncUser.c.balance + amount})
                if to_affected == 0:
                    raise ValueError("User not found")

            await backend.commit_transaction()

            from_user = await AsyncUser.find_one({'id': from_user_id})
            to_user = await AsyncUser.find_one({'id': to_user_id})
            return {
                'success': True,
                'from_balance': from_user.balance if from_user else None,
                'to_balance': to_user.balance if to_user else None
            }
        except Exception as e:
            await backend.rollback_transaction()
            return {'success': False, 'error': str(e)}
    finally:
        await AsyncUser.backend().disconnect()


async def async_get_balance_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> float:
    """Get user balance (async)."""
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
        user = await AsyncUser.find_one({'id': user_id})
        return user.balance if user else -1
    finally:
        await AsyncUser.backend().disconnect()


async def async_update_order_status_task(
    ctx: TaskContext,
    order_id: int,
    new_status: str,
    conn_params: Dict
) -> Dict[str, Any]:
    """Update order status within a transaction (async)."""
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
        backend = AsyncOrder.backend()
        await backend.begin_transaction()

        try:
            order = await AsyncOrder.find_one({'id': order_id})
            if not order:
                raise ValueError("Order not found")

            order.status = new_status
            await order.save()

            await backend.commit_transaction()

            return {'success': True, 'order_id': order_id, 'status': new_status}
        except Exception as e:
            await backend.rollback_transaction()
            return {'success': False, 'error': str(e)}
    finally:
        await AsyncOrder.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes - Synchronous
# ─────────────────────────────────────────────────────────────────────────────
class TestTransactionIsolation:
    """Test transaction isolation in Worker processes."""

    def test_transaction_in_worker(self, order_fixtures_for_worker):
        """Test transaction executes correctly in Worker process."""
        User, Order, OrderItem = order_fixtures_for_worker['models']
        conn_params = order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users
        user1 = User(username='tx_user1', email='tx1@test.com', age=30, balance=100.0)
        user1.save()
        user2 = User(username='tx_user2', email='tx2@test.com', age=25, balance=50.0)
        user2.save()

        try:
            with WorkerPool(n_workers=2) as pool:
                result = pool.submit(
                    transfer_balance_task,
                    user1.id, user2.id, 30.0,
                    conn_params
                ).result(timeout=60)

            assert result['success']

            # Verify balances
            user1.refresh()
            user2.refresh()
            assert user1.balance == 70.0
            assert user2.balance == 80.0
        finally:
            user1.delete()
            user2.delete()

    def test_transaction_rollback_on_error(self, order_fixtures_for_worker):
        """Test transaction rollback on error."""
        User, Order, OrderItem = order_fixtures_for_worker['models']
        conn_params = order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users
        user1 = User(username='rb_user1', email='rb1@test.com', age=30, balance=100.0)
        user1.save()
        user2 = User(username='rb_user2', email='rb2@test.com', age=25, balance=50.0)
        user2.save()

        try:
            with WorkerPool(n_workers=2) as pool:
                # Try to transfer more than balance
                result = pool.submit(
                    transfer_balance_task,
                    user1.id, user2.id, 200.0,  # Exceeds balance
                    conn_params
                ).result(timeout=60)

            assert not result['success']
            assert 'Insufficient balance' in result['error']

            # Verify balances unchanged
            user1.refresh()
            user2.refresh()
            assert user1.balance == 100.0
            assert user2.balance == 50.0
        finally:
            user1.delete()
            user2.delete()

    def test_concurrent_transactions_isolation(self, order_fixtures_for_worker):
        """Test concurrent transactions maintain isolation."""
        User, Order, OrderItem = order_fixtures_for_worker['models']
        conn_params = order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create source user and targets
        source = User(username='source', email='source@test.com', age=35, balance=1000.0)
        source.save()
        targets = []
        for i in range(5):
            target = User(
                username=f'target_{i}',
                email=f'target_{i}@test.com',
                age=20 + i,
                balance=0.0
            )
            target.save()
            targets.append(target)

        try:
            with WorkerPool(n_workers=5) as pool:
                # Concurrent transfers - wait for all to complete
                futures = [
                    pool.submit(
                        transfer_balance_task,
                        source.id, t.id, 50.0,
                        conn_params
                    )
                    for t in targets
                ]
                # Wait for all futures to complete
                for f in futures:
                    f.result(timeout=120)

            # Verify total balance is conserved (FOR UPDATE locking prevents lost updates)
            source.refresh()
            total_target = sum(
                User.find_one({'id': t.id}).balance for t in targets
            )

            # Total should equal initial 1000
            assert source.balance + total_target == 1000.0

        finally:
            source.delete()
            for t in targets:
                t.delete()

    def test_order_status_update_transaction(self, order_fixtures_for_worker):
        """Test order status update in transaction."""
        User, Order, OrderItem = order_fixtures_for_worker['models']
        conn_params = order_fixtures_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Get an order for testing
        order = Order.query().one()
        if not order:
            pytest.skip("No orders available for testing")

        original_status = order.status

        try:
            with WorkerPool(n_workers=2) as pool:
                result = pool.submit(
                    update_order_status_task,
                    order.id,
                    'completed',
                    conn_params
                ).result(timeout=60)

            assert result['success']

            # Verify status changed
            order.refresh()
            assert order.status == 'completed'

        finally:
            # Restore original status
            order.status = original_status
            order.save()