# src/rhosocial/activerecord/testsuite/feature/basic/worker/conftest.py
"""L2 environment fixtures for ``basic/worker``.

Worker processes need serializable connection information; the definition
class below turns the scenario/config pair into that payload.
"""
import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import UserDefinition
from rhosocial.activerecord.testsuite.feature.basic.fixtures import resolve

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    UserDefinition,
)

User = resolve("User")
AsyncUser = resolve("AsyncUser")


class WorkerConnection:
    """Serializable connection payload for a worker process."""

    def __init__(self, scenario, config):
        self.scenario = scenario
        self.config = config

    def params(self, is_async=False):
        backend_class = (
            self.scenario.async_backend_class if is_async else self.scenario.backend_class
        )
        return {
            "backend_module": backend_class.__module__,
            "backend_class_name": backend_class.__name__,
            "config_class_module": type(self.config).__module__,
            "config_class_name": type(self.config).__name__,
            "config_kwargs": self.config.to_dict(),
            "schema_sql": "",
        }


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """Scenario, connection configuration, and the directory database name."""
    name = "test_basic_worker"
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


@pytest.fixture(name="worker_connection_params")
def worker_connection_params(database_config):
    scenario, config, _name = database_config
    yield WorkerConnection(scenario, config).params()


@pytest.fixture(name="user_class_for_worker")
def user_class_for_worker(database_config):
    scenario, config, _name = database_config
    User.configure(config, scenario.backend_class)
    yield {"model": User, "conn_params": WorkerConnection(scenario, config).params()}
    User.backend().disconnect()


@pytest.fixture(name="async_user_class_for_worker")
async def async_user_class_for_worker(database_config):
    scenario, config, _name = database_config
    await AsyncUser.configure(config, scenario.async_backend_class)
    yield {
        "model": AsyncUser,
        "conn_params": WorkerConnection(scenario, config).params(is_async=True),
    }
    await AsyncUser.backend().disconnect()
