# src/rhosocial/activerecord/testsuite/feature/basic/worker/test_parallel_crud_async.py
"""
Test WorkerPool integration with ActiveRecord parallel CRUD operations.

IMPORTANT:
- All task functions must be module-level pickle-able functions
- Tests require `if __name__ == '__main__'` guard for multiprocessing
- Provider must implement WorkerTestProtocol for these tests to work
"""
import time
from typing import Dict, Any, Optional

import pytest
from rhosocial.activerecord.worker import WorkerPool, PoolState, TaskContext

pytestmark = pytest.mark.serial


# ─────────────────────────────────────────────────────────────────────────────
# Synchronous Task Functions (must be module-level, pickle-able)
# ─────────────────────────────────────────────────────────────────────────────

def create_user_task(ctx: TaskContext, user_data: Dict[str, Any], conn_params: Dict) -> Optional[int]:
    """
    Create a user in Worker process.

    Args:
        ctx: Worker task context
        user_data: User data dictionary (username, email, age, etc.)
        conn_params: Worker connection parameters from WorkerTestProtocol

    Returns:
        Created user ID or None on failure
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    # Dynamic imports for Worker process
    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    # Import testsuite model
    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User

    User.configure(config, backend_class)

    try:
        user = User(**user_data)
        user.save()
        return user.id
    finally:
        User.backend().disconnect()


def read_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> Optional[Dict[str, Any]]:
    """
    Read a user in Worker process.

    Args:
        ctx: Worker task context
        user_id: User ID to read
        conn_params: Worker connection parameters

    Returns:
        User data dict or None if not found
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User

    User.configure(config, backend_class)

    try:
        user = User.find_one({'id': user_id})
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': str(user.email),
                'age': user.age
            }
        return None
    finally:
        User.backend().disconnect()


def update_user_task(ctx: TaskContext, user_id: int, updates: Dict[str, Any], conn_params: Dict) -> bool:
    """
    Update a user in Worker process.

    Args:
        ctx: Worker task context
        user_id: User ID to update
        updates: Dictionary of fields to update
        conn_params: Worker connection parameters

    Returns:
        True if updated, False if user not found
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User

    User.configure(config, backend_class)

    try:
        user = User.find_one({'id': user_id})
        if user:
            for key, value in updates.items():
                setattr(user, key, value)
            user.save()
            return True
        return False
    finally:
        User.backend().disconnect()


def delete_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> bool:
    """
    Delete a user in Worker process.

    Args:
        ctx: Worker task context
        user_id: User ID to delete
        conn_params: Worker connection parameters

    Returns:
        True if deleted, False if user not found
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import User

    User.configure(config, backend_class)

    try:
        user = User.find_one({'id': user_id})
        if user:
            user.delete()
            return True
        return False
    finally:
        User.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Asynchronous Task Functions (must be module-level, pickle-able)
# ─────────────────────────────────────────────────────────────────────────────

async def async_create_user_task(ctx: TaskContext, user_data: Dict[str, Any], conn_params: Dict) -> Optional[int]:
    """
    Create a user in Worker process using async model.

    Args:
        ctx: Worker task context
        user_data: User data dictionary
        conn_params: Worker connection parameters

    Returns:
        Created user ID or None on failure
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import AsyncUser

    await AsyncUser.configure(config, backend_class)

    try:
        user = AsyncUser(**user_data)
        await user.save()
        return user.id
    finally:
        await AsyncUser.backend().disconnect()


async def async_read_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> Optional[Dict[str, Any]]:
    """
    Read a user in Worker process using async model.
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import AsyncUser

    await AsyncUser.configure(config, backend_class)

    try:
        user = await AsyncUser.find_one({'id': user_id})
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': str(user.email),
                'age': user.age
            }
        return None
    finally:
        await AsyncUser.backend().disconnect()


async def async_update_user_task(ctx: TaskContext, user_id: int, updates: Dict[str, Any], conn_params: Dict) -> bool:
    """
    Update a user in Worker process using async model.
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import AsyncUser

    await AsyncUser.configure(config, backend_class)

    try:
        user = await AsyncUser.find_one({'id': user_id})
        if user:
            for key, value in updates.items():
                setattr(user, key, value)
            await user.save()
            return True
        return False
    finally:
        await AsyncUser.backend().disconnect()


async def async_delete_user_task(ctx: TaskContext, user_id: int, conn_params: Dict) -> bool:
    """
    Delete a user in Worker process using async model.
    """
    if conn_params is None:
        raise ValueError("conn_params is required")

    import importlib
    backend_module = importlib.import_module(conn_params['backend_module'])
    backend_class = getattr(backend_module, conn_params['backend_class_name'])
    config_module = importlib.import_module(conn_params['config_class_module'])
    config_class = getattr(config_module, conn_params['config_class_name'])
    config = config_class(**conn_params['config_kwargs'])

    from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import AsyncUser

    await AsyncUser.configure(config, backend_class)

    try:
        user = await AsyncUser.find_one({'id': user_id})
        if user:
            await user.delete()
            return True
        return False
    finally:
        await AsyncUser.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes - Synchronous
# ─────────────────────────────────────────────────────────────────────────────
class TestAsyncParallelCRUD:
    """Test parallel CRUD operations with asynchronous models."""

    async def test_parallel_create(self, async_user_class_for_worker):
        """Test parallel async user creation."""
        AsyncUser = async_user_class_for_worker['model']
        conn_params = async_user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        users_data = [
            {'username': f'async_user_{i}', 'email': f'async_{i}@test.com', 'age': 25 + i}
            for i in range(10)
        ]

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_create_user_task, data, conn_params)
                for data in users_data
            ]
            results = [f.result(timeout=60) for f in futures]

        assert all(r is not None for r in results)
        assert len(set(results)) == 10

    async def test_parallel_read(self, async_user_class_for_worker):
        """Test parallel async user reading."""
        AsyncUser = async_user_class_for_worker['model']
        conn_params = async_user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users - use the same event loop as the fixture
        test_users = []
        for i in range(5):
            user = AsyncUser(
                username=f'async_read_{i}',
                email=f'async_read_{i}@test.com',
                age=25
            )
            await user.save()
            test_users.append(user)

        try:
            with WorkerPool(n_workers=4) as pool:
                futures = [
                    pool.submit(async_read_user_task, u.id, conn_params)
                    for u in test_users
                ]
                results = [f.result(timeout=60) for f in futures]

            assert all(r is not None for r in results)
            usernames = {r['username'] for r in results}
            assert usernames == {f'async_read_{i}' for i in range(5)}
        finally:
            for user in test_users:
                await user.delete()

    async def test_parallel_update(self, async_user_class_for_worker):
        """Test parallel async user updating."""
        AsyncUser = async_user_class_for_worker['model']
        conn_params = async_user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        test_users = []
        for i in range(5):
            user = AsyncUser(
                username=f'async_update_{i}',
                email=f'async_update_{i}@test.com',
                age=25,
                balance=0.0
            )
            await user.save()
            test_users.append(user)

        try:
            with WorkerPool(n_workers=4) as pool:
                futures = [
                    pool.submit(
                        async_update_user_task,
                        u.id,
                        {'balance': 200.0 + i},
                        conn_params
                    )
                    for i, u in enumerate(test_users)
                ]
                results = [f.result(timeout=60) for f in futures]

            assert all(results)

            for i, user in enumerate(test_users):
                await user.refresh()
                assert user.balance == 200.0 + i
        finally:
            for user in test_users:
                await user.delete()

    async def test_parallel_delete(self, async_user_class_for_worker):
        """Test parallel async user deletion."""
        AsyncUser = async_user_class_for_worker['model']
        conn_params = async_user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        test_ids = []
        for i in range(5):
            user = AsyncUser(
                username=f'async_delete_{i}',
                email=f'async_delete_{i}@test.com',
                age=25
            )
            await user.save()
            test_ids.append(user.id)

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(async_delete_user_task, uid, conn_params)
                for uid in test_ids
            ]
            results = [f.result(timeout=60) for f in futures]

        assert all(results)

        for uid in test_ids:
            user = await AsyncUser.find_one({'id': uid})
            assert user is None


