# src/rhosocial/activerecord/testsuite/feature/query/connection/conftest.py
"""Fixtures for the query connection-pool context tests.

The pool is built from the environment's own configuration, so it always
points at the directory's database; the model is configured the same way.
"""
import logging

import pytest

from rhosocial.activerecord.testsuite.feature.query.fixtures import tables
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import (
    User,
)

GROUP_TABLES = ("users",)

logger = logging.getLogger(__name__)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.QUERY_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


def log_pool_stats(pool, scenario: str, test_name: str, pool_type: str) -> None:
    try:
        stats = pool.get_stats()
        logger.info(
            f"[{scenario}] {test_name} ({pool_type}) - Pool stats: "
            f"created={stats.total_created}, destroyed={stats.total_destroyed}, "
            f"acquired={stats.total_acquired}, released={stats.total_released}, "
            f"available={stats.current_available}, in_use={stats.current_in_use}, "
            f"utilization={stats.utilization_rate:.2%}, "
            f"errors={stats.total_errors}, timeouts={stats.total_timeouts}"
        )
    except Exception as error:
        logger.warning(f"Failed to get pool stats: {error}")


def sync_pool(environment):
    """Create a sync pool bound to the directory's database."""
    from rhosocial.activerecord.connection.pool import BackendPool
    from rhosocial.activerecord.connection.pool.config import PoolConfig

    config = environment.make_config()
    backend_class = environment.scenario.backend_class
    return BackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: backend_class(connection_config=config),
        )
    )


async def async_pool(environment):
    """Create an async pool bound to the directory's database."""
    from rhosocial.activerecord.connection.pool import AsyncBackendPool
    from rhosocial.activerecord.connection.pool.config import PoolConfig

    config = environment.make_config()
    backend_class = environment.scenario.async_backend_class
    return await AsyncBackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: backend_class(connection_config=config),
        )
    )


def close_sync_pool(pool) -> None:
    """Close a sync pool, forcing it when a connection is still held."""
    try:
        pool.close(timeout=1.0, force=True)
    except Exception:
        pass


async def close_async_pool(pool) -> None:
    """Close an async pool, forcing it when a connection is still held."""
    try:
        await pool.close(timeout=1.0, force=True)
    except Exception:
        pass


def disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


@pytest.fixture(name="sync_pool_and_model")
def sync_pool_and_model(environment, request):
    pool = sync_pool(environment)
    model = environment.configure(User)
    yield pool, model
    log_pool_stats(pool, environment.scenario.name, request.node.name, "sync")
    close_sync_pool(pool)
    disconnect(model)


@pytest.fixture(name="async_pool_and_model")
async def async_pool_and_model(environment, request):
    pool = await async_pool(environment)
    model = await environment.configure_async(AsyncUser)
    yield pool, model
    log_pool_stats(pool, environment.scenario.name, request.node.name, "async")
    await close_async_pool(pool)
    await disconnect_async(model)
