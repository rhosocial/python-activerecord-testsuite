# src/rhosocial/activerecord/testsuite/feature/basic/worker/test_worker_pool_lifecycle.py
"""
Test WorkerPool lifecycle with database operations.

This module tests the lifecycle management of WorkerPool when used
with ActiveRecord database operations, including startup, shutdown,
and graceful termination scenarios.
"""
import time
from typing import Dict

import pytest
from rhosocial.activerecord.worker import WorkerPool, PoolState


# ─────────────────────────────────────────────────────────────────────────────
# Task Functions
# ─────────────────────────────────────────────────────────────────────────────

def simple_db_task(value: int, conn_params: Dict) -> int:
    """
    Simple database task that verifies connection availability.

    Args:
        value: Value to double
        conn_params: Worker connection parameters

    Returns:
        value * 2
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
        # Verify connection by counting users
        User.query().count()
        return value * 2
    finally:
        User.backend().disconnect()


def long_running_db_task(duration: float, conn_params: Dict) -> float:
    """
    Long-running database task for testing graceful shutdown.

    Args:
        duration: Duration to sleep in seconds
        conn_params: Worker connection parameters

    Returns:
        duration value
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
        # Keep connection alive
        User.query().count()
        return duration
    finally:
        User.backend().disconnect()


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes
# ─────────────────────────────────────────────────────────────────────────────

class TestWorkerPoolLifecycle:
    """Test WorkerPool lifecycle with database operations."""

    def test_pool_startup_and_shutdown(self, user_class_for_worker):
        """Test WorkerPool startup and shutdown with database tasks."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        pool = WorkerPool(n_workers=2)

        try:
            assert pool.state == PoolState.RUNNING
            assert pool.n_workers == 2
            assert pool.active_workers == 2

            # Submit a simple task to verify pool is working
            fut = pool.submit(simple_db_task, 5, conn_params)
            assert fut.result(timeout=30) == 10

        finally:
            report = pool.shutdown(graceful_timeout=5.0)

        assert pool.state == PoolState.STOPPED
        assert pool.active_workers == 0
        assert report.final_phase == "graceful"

    def test_context_manager_usage(self, user_class_for_worker):
        """Test WorkerPool as context manager."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        with WorkerPool(n_workers=2) as pool:
            assert pool.state == PoolState.RUNNING

            futures = [
                pool.submit(simple_db_task, i, conn_params)
                for i in range(4)
            ]
            results = [f.result(timeout=30) for f in futures]
            assert results == [0, 2, 4, 6]

        # Pool should be stopped after exiting context
        assert pool.state == PoolState.STOPPED

    def test_graceful_shutdown_with_pending_tasks(self, user_class_for_worker):
        """Test graceful shutdown waits for pending tasks to complete."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        pool = WorkerPool(n_workers=2)

        # Submit tasks that take some time
        futures = [
            pool.submit(long_running_db_task, 0.5, conn_params)
            for _ in range(2)
        ]

        # Let tasks start
        time.sleep(0.1)

        # Start shutdown immediately
        report = pool.shutdown(graceful_timeout=10.0)

        # Should be graceful shutdown
        assert report.final_phase == "graceful"
        # All tasks should have completed
        assert all(f.done for f in futures)
        assert all(f.succeeded for f in futures)

    def test_forced_shutdown_with_timeout(self, user_class_for_worker):
        """Test forced shutdown when graceful timeout expires."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        pool = WorkerPool(n_workers=2)

        # Submit a very long task
        pool.submit(long_running_db_task, 10.0, conn_params)

        # Let task start
        time.sleep(0.2)

        # Shutdown with very short timeout
        report = pool.shutdown(graceful_timeout=0.5, term_timeout=1.0)

        # Should have gone through terminate or kill phase
        assert report.final_phase in ("terminate", "kill")
        assert pool.state == PoolState.STOPPED

    def test_multiple_pools_sequential(self, user_class_for_worker):
        """Test creating and destroying multiple pools sequentially."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        for i in range(3):
            with WorkerPool(n_workers=2) as pool:
                futures = [
                    pool.submit(simple_db_task, j, conn_params)
                    for j in range(4)
                ]
                results = [f.result(timeout=30) for f in futures]
                assert results == [0, 2, 4, 6]

    def test_pool_reuse_after_shutdown(self, user_class_for_worker):
        """Test that pool cannot be reused after shutdown."""
        conn_params = user_class_for_worker['conn_params']

        if conn_params is None:
            pytest.skip("Provider does not implement WorkerTestProtocol")

        pool = WorkerPool(n_workers=2)
        pool.shutdown(graceful_timeout=1.0)

        assert pool.state == PoolState.STOPPED

        # Submitting after shutdown should raise
        from rhosocial.activerecord.worker import PoolDrainingError
        with pytest.raises(PoolDrainingError):
            pool.submit(simple_db_task, 1, conn_params)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
