# src/rhosocial/activerecord/testsuite/feature/basic/worker/test_parallel_crud.py
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
class TestParallelCRUD:
    """Test parallel CRUD operations with synchronous models."""

    def test_parallel_create(self, user_class_for_worker):
        """Test parallel user creation."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Prepare test data
        users_data = [
            {'username': f'user_{i}', 'email': f'user_{i}@test.com', 'age': 20 + i}
            for i in range(10)
        ]

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(create_user_task, data, conn_params)
                for data in users_data
            ]
            results = [f.result(timeout=60) for f in futures]

        # Verify all users created successfully
        assert all(r is not None for r in results)
        assert len(set(results)) == 10  # All IDs should be unique

    def test_parallel_read(self, user_class_for_worker):
        """Test parallel user reading."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users in main process
        test_users = []
        for i in range(5):
            user = User(username=f'read_test_{i}', email=f'read_{i}@test.com', age=25)
            user.save()
            test_users.append(user)

        try:
            with WorkerPool(n_workers=4) as pool:
                futures = [
                    pool.submit(read_user_task, u.id, conn_params)
                    for u in test_users
                ]
                results = [f.result(timeout=60) for f in futures]

            # Verify read results
            assert all(r is not None for r in results)
            usernames = {r['username'] for r in results}
            assert usernames == {f'read_test_{i}' for i in range(5)}
        finally:
            for user in test_users:
                user.delete()

    def test_parallel_update(self, user_class_for_worker):
        """Test parallel user updating."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users
        test_users = []
        for i in range(5):
            user = User(
                username=f'update_test_{i}',
                email=f'update_{i}@test.com',
                age=25,
                balance=0.0
            )
            user.save()
            test_users.append(user)

        try:
            with WorkerPool(n_workers=4) as pool:
                futures = [
                    pool.submit(
                        update_user_task,
                        u.id,
                        {'balance': 100.0 + i},
                        conn_params
                    )
                    for i, u in enumerate(test_users)
                ]
                results = [f.result(timeout=60) for f in futures]

            # Verify updates succeeded
            assert all(results)

            # Refresh and verify balances
            for i, user in enumerate(test_users):
                user.refresh()
                assert user.balance == 100.0 + i
        finally:
            for user in test_users:
                user.delete()

    def test_parallel_delete(self, user_class_for_worker):
        """Test parallel user deletion."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create test users
        test_ids = []
        for i in range(5):
            user = User(
                username=f'delete_test_{i}',
                email=f'delete_{i}@test.com',
                age=25
            )
            user.save()
            test_ids.append(user.id)

        with WorkerPool(n_workers=4) as pool:
            futures = [
                pool.submit(delete_user_task, uid, conn_params)
                for uid in test_ids
            ]
            results = [f.result(timeout=60) for f in futures]

        # Verify all deleted
        assert all(results)

        # Verify users no longer exist
        for uid in test_ids:
            assert User.find_one({'id': uid}) is None