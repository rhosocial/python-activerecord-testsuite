# src/rhosocial/activerecord/testsuite/feature/basic/worker/test_connection_management.py
"""
Test database connection management in Worker processes.

This module tests that database connections are properly managed
in Worker processes, including cleanup, timeout handling, and
connection isolation between workers.
"""
import time
from typing import Dict

import pytest
from rhosocial.activerecord.worker import WorkerPool, TaskContext

pytestmark = pytest.mark.serial


# ─────────────────────────────────────────────────────────────────────────────
# Task Functions
# ─────────────────────────────────────────────────────────────────────────────

def count_users_task(ctx: TaskContext, conn_params: Dict) -> int:
    """
    Count users in database.

    Args:
        ctx: Worker task context
        conn_params: Worker connection parameters

    Returns:
        Number of users
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
        return User.query().count()
    finally:
        User.backend().disconnect()


def create_and_count_task(ctx: TaskContext, user_data: Dict, conn_params: Dict) -> Dict:
    """
    Create a user and return count.

    Tests that connection is properly used for both write and read.

    Args:
        ctx: Worker task context
        user_data: User data to create
        conn_params: Worker connection parameters

    Returns:
        Dict with created user ID and total count
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
        user = User(**user_data)
        user.save()
        count = User.query().count()
        return {'user_id': user.id, 'count': count}
    finally:
        User.backend().disconnect()


def connection_stress_task(ctx: TaskContext, iterations: int, conn_params: Dict) -> int:
    """
    Repeatedly connect and disconnect to stress test connection management.

    Args:
        ctx: Worker task context
        iterations: Number of connect/disconnect cycles
        conn_params: Worker connection parameters

    Returns:
        Number of successful iterations
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

    success_count = 0

    for _ in range(iterations):
        User.configure(config, backend_class)
        try:
            User.query().count()
            success_count += 1
        finally:
            User.backend().disconnect()

    return success_count


def slow_query_task(ctx: TaskContext, duration: float, conn_params: Dict) -> bool:
    """
    Simulate a slow query to test timeout handling.

    Args:
        ctx: Worker task context
        duration: How long to sleep
        conn_params: Worker connection parameters

    Returns:
        True if completed
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
        time.sleep(duration)
        User.query().count()
        return True
    finally:
        User.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectionManagement:
    """Test connection management in Worker processes."""

    def test_connection_cleanup_after_task(self, user_class_for_worker):
        """Test that connections are properly cleaned up after task completion."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=2) as pool:
            # Execute multiple tasks to verify cleanup
            for _ in range(5):
                futures = [
                    pool.submit(count_users_task, conn_params)
                    for _ in range(4)
                ]
                results = [f.result(timeout=30) for f in futures]
                assert all(isinstance(r, int) for r in results)

    def test_connection_isolation_between_workers(self, user_class_for_worker):
        """Test that each worker has isolated connection."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Create some test users first
        test_users = []
        for i in range(3):
            user = User(
                username=f'isolation_test_{i}',
                email=f'isolation_{i}@test.com',
                age=25
            )
            user.save()
            test_users.append(user)

        try:
            with WorkerPool(n_workers=4) as pool:
                # Each worker should see the same data (isolation doesn't mean different data)
                futures = [
                    pool.submit(count_users_task, conn_params)
                    for _ in range(4)
                ]
                results = [f.result(timeout=30) for f in futures]

                # All workers should see same count
                assert len(set(results)) == 1
        finally:
            for user in test_users:
                user.delete()

    def test_connection_stress(self, user_class_for_worker):
        """Test repeated connection/disconnection cycles."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=2) as pool:
            futures = [
                pool.submit(connection_stress_task, 5, conn_params)
                for _ in range(4)
            ]
            results = [f.result(timeout=60) for f in futures]

            # All iterations should succeed
            assert all(r == 5 for r in results)

    def test_task_timeout(self, user_class_for_worker):
        """Test task timeout handling."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=2) as pool:
            # Submit a slow task with short timeout
            fut = pool.submit(slow_query_task, 5.0, conn_params)

            # Should timeout waiting for result
            with pytest.raises(TimeoutError):
                fut.result(timeout=0.5)

    def test_parallel_connection_stress(self, user_class_for_worker):
        """Test many parallel connections."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Use more workers to stress test
        with WorkerPool(n_workers=8) as pool:
            futures = [
                pool.submit(count_users_task, conn_params)
                for _ in range(20)
            ]
            results = [f.result(timeout=60) for f in futures]

            assert len(results) == 20
            assert all(isinstance(r, int) for r in results)

    def test_connection_with_create_operations(self, user_class_for_worker):
        """Test connection works correctly with write operations."""
        User = user_class_for_worker['model']
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        # Track created user IDs for cleanup
        created_ids = []

        try:
            with WorkerPool(n_workers=4) as pool:
                futures = [
                    pool.submit(
                        create_and_count_task,
                        {'username': f'conn_test_{i}', 'email': f'conn_{i}@test.com', 'age': 25},
                        conn_params
                    )
                    for i in range(10)
                ]
                results = [f.result(timeout=60) for f in futures]

                # All should succeed
                assert all(r['user_id'] is not None for r in results)
                created_ids = [r['user_id'] for r in results]

        finally:
            # Cleanup
            for uid in created_ids:
                user = User.find_one({'id': uid})
                if user:
                    user.delete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
