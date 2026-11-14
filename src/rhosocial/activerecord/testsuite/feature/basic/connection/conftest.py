# src/rhosocial/activerecord/testsuite/feature/basic/connection/conftest.py
"""L2 environment fixtures for ``basic/connection``.

The directory owns one database; pool fixtures build pools against it and
configure the model classes through ``ActiveRecord.configure``.
"""
import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.connection.pool import AsyncBackendPool, BackendPool
from rhosocial.activerecord.connection.pool.config import PoolConfig
from rhosocial.activerecord.testsuite.feature.basic.connection.fixtures import (
    AsyncTestUser,
    TestUser,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import TestUserDefinition

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    TestUserDefinition,
)


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_connection"
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
    """Drop and recreate this directory's tables before every test."""
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


@pytest.fixture(name="sync_pool_and_model")
def sync_pool_and_model(database_config):
    scenario, config, _name = database_config
    pool = BackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.backend_class(connection_config=config),
        )
    )
    TestUser.configure(config, scenario.backend_class)
    yield pool, TestUser
    try:
        pool.close(timeout=1.0, force=True)
    except Exception:
        pass
    TestUser.backend().disconnect()


@pytest.fixture(name="async_pool_and_model")
async def async_pool_and_model(database_config):
    scenario, config, _name = database_config
    pool = await AsyncBackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.async_backend_class(
                connection_config=config
            ),
        )
    )
    await AsyncTestUser.configure(config, scenario.async_backend_class)
    yield pool, AsyncTestUser
    try:
        await pool.close(timeout=1.0, force=True)
    except Exception:
        pass
    await AsyncTestUser.backend().disconnect()


@pytest.fixture(name="sync_pool_for_crud")
def sync_pool_for_crud(database_config):
    scenario, config, _name = database_config
    pool = BackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.backend_class(connection_config=config),
        )
    )
    TestUser.configure(config, scenario.backend_class)
    yield pool, TestUser
    try:
        pool.close(timeout=1.0, force=True)
    except Exception:
        pass
    TestUser.backend().disconnect()


@pytest.fixture(name="async_pool_for_crud")
async def async_pool_for_crud(database_config):
    scenario, config, _name = database_config
    pool = await AsyncBackendPool.create(
        PoolConfig(
            min_size=1,
            max_size=5,
            backend_factory=lambda: scenario.async_backend_class(
                connection_config=config
            ),
        )
    )
    await AsyncTestUser.configure(config, scenario.async_backend_class)
    yield pool, AsyncTestUser
    try:
        await pool.close(timeout=1.0, force=True)
    except Exception:
        pass
    await AsyncTestUser.backend().disconnect()
