# src/rhosocial/activerecord/testsuite/feature/query/connection/conftest.py
"""L2 environment fixtures for ``query/connection``.

- ``database`` / ``schema``: the directory's database and its ``users`` table;
- the pools are built from this directory's scenario and configuration, so they
  always point at the directory's database; the model is configured the same
  way.
"""

import logging
from pathlib import Path

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.connection.pool import AsyncBackendPool, BackendPool
from rhosocial.activerecord.connection.pool.config import PoolConfig
from rhosocial.activerecord.testsuite.feature.query.fixtures.async_models import (
    AsyncUser,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.definitions import (
    UsersDefinition,
)
from rhosocial.activerecord.testsuite.feature.query.fixtures.models import User

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (UsersDefinition,)

logger = logging.getLogger(__name__)


def _database_name() -> str:
    """Database name from this directory's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory database name."""
    name = _database_name()
    return backend_scenario, backend_scenario.make_config(name), name


@pytest.fixture(scope="session")
def database(database_config):
    """The directory's database, prepared once and left for later files."""
    scenario, config, name = database_config
    scenario.reset_database(name)
    backend = scenario.backend_class(connection_config=config)
    backend.connect()
    backend.introspect_and_adapt()
    yield backend
    backend.disconnect()


@pytest.fixture(scope="function", autouse=True)
def schema(database):
    """Drop and recreate the table this directory uses, before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


def log_pool_stats(pool, scenario_name: str, test_name: str, pool_type: str) -> None:
    try:
        stats = pool.get_stats()
        logger.info(
            f"[{scenario_name}] {test_name} ({pool_type}) - Pool stats: "
            f"created={stats.total_created}, destroyed={stats.total_destroyed}, "
            f"acquired={stats.total_acquired}, released={stats.total_released}, "
            f"available={stats.current_available}, in_use={stats.current_in_use}, "
            f"utilization={stats.utilization_rate:.2%}, "
            f"errors={stats.total_errors}, timeouts={stats.total_timeouts}"
        )
    except Exception as error:
        logger.warning(f"Failed to get pool stats: {error}")


def sync_pool(scenario, config):
    """Create a sync pool bound to the directory's database."""
    return BackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.backend_class(connection_config=config),
        )
    )


async def async_pool(scenario, config):
    """Create an async pool bound to the directory's database."""
    return await AsyncBackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.async_backend_class(connection_config=config),
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


@pytest.fixture(name="sync_pool_and_model")
def sync_pool_and_model(database_config, request):
    scenario, config, _name = database_config
    pool = sync_pool(scenario, config)
    User.configure(config, scenario.backend_class)
    yield pool, User
    log_pool_stats(pool, scenario.name, request.node.name, "sync")
    close_sync_pool(pool)
    User.backend().disconnect()


@pytest.fixture(name="async_pool_and_model")
async def async_pool_and_model(database_config, request):
    scenario, config, _name = database_config
    pool = await async_pool(scenario, config)
    await AsyncUser.configure(config, scenario.async_backend_class)
    yield pool, AsyncUser
    log_pool_stats(pool, scenario.name, request.node.name, "async")
    await close_async_pool(pool)
    await AsyncUser.backend().disconnect()
