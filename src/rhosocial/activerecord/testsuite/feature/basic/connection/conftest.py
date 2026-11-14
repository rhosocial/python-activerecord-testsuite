# src/rhosocial/activerecord/testsuite/feature/basic/connection/conftest.py
"""The ``basic/connection`` minimal test set.

The directory owns one database (named after its path) and one fixture group.
The pool fixtures hand a pool and a model configured against the same database,
so the pool-context tests can compare the class backend with the context backend.
"""
import pytest

from rhosocial.activerecord.connection.pool import AsyncBackendPool, BackendPool
from rhosocial.activerecord.connection.pool.config import PoolConfig

from rhosocial.activerecord.testsuite.feature.basic.connection.fixtures import (
    AsyncTestUser,
    TestUser,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures import tables

GROUP_TABLES = ("test_users",)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for name in GROUP_TABLES:
        environment.execute(tables.BASIC_TABLES[name](environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name in reversed(GROUP_TABLES):
        environment.execute(tables.drop_table(environment.dialect, name))


def sync_pool(environment):
    """Create a sync connection pool bound to this directory's database."""
    config = environment.make_config()
    return BackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: environment.scenario.backend_class(
                connection_config=config
            ),
        )
    )


async def async_pool(environment):
    """Create an async connection pool bound to this directory's database."""
    config = environment.make_config()
    return await AsyncBackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: environment.scenario.async_backend_class(
                connection_config=config
            ),
        )
    )


def close_pool(pool) -> None:
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


def _disconnect(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        backend.disconnect()


async def _disconnect_async(model) -> None:
    backend = getattr(model, "__backend__", None)
    if backend is not None:
        await backend.disconnect()


@pytest.fixture(name="sync_pool_and_model")
def sync_pool_and_model(environment):
    pool = sync_pool(environment)
    model = environment.configure(TestUser)
    yield pool, model
    close_pool(pool)
    _disconnect(model)


@pytest.fixture(name="async_pool_and_model")
async def async_pool_and_model(environment):
    pool = await async_pool(environment)
    model = await environment.configure_async(AsyncTestUser)
    yield pool, model
    await close_async_pool(pool)
    await _disconnect_async(model)


@pytest.fixture(name="sync_pool_for_crud")
def sync_pool_for_crud(environment):
    pool = sync_pool(environment)
    model = environment.configure(TestUser)
    yield pool, model
    close_pool(pool)
    _disconnect(model)


@pytest.fixture(name="async_pool_for_crud")
async def async_pool_for_crud(environment):
    pool = await async_pool(environment)
    model = await environment.configure_async(AsyncTestUser)
    yield pool, model
    await close_async_pool(pool)
    await _disconnect_async(model)
