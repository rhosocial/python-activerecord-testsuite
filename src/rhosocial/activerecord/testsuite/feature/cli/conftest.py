# src/rhosocial/activerecord/testsuite/feature/cli/conftest.py
"""L2 backend fixtures for the CLI feature.

The CLI tests address models by ``module:attribute`` strings, so the fixture
builds a throw-away module whose attributes are the models configured for the
directory's database.  The directory owns one fixture group: the basic tables
and the mixins ``tasks`` table the CLI exercises.
"""
import sys
import types
import uuid

import pytest

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.query import AsyncCTEQuery, CTEQuery
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncBulkUser,
    AsyncUser,
    AsyncValidatedUser,
    BASIC_DEFINITIONS,
    BulkUser,
    User,
    ValidatedUser,
)
from rhosocial.activerecord.testsuite.feature.cli.fixtures import (
    AsyncCLIReadOnlyUser,
    CLIReadOnlyUser,
)
from rhosocial.activerecord.testsuite.feature.mixins.fixtures.definitions import (
    TaskDefinition,
)
from rhosocial.activerecord.testsuite.feature.mixins.fixtures.models import (
    AsyncTask,
    Task,
)

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (
    BASIC_DEFINITIONS["users"],
    BASIC_DEFINITIONS["bulk_users"],
    BASIC_DEFINITIONS["validated_users"],
    TaskDefinition,
)


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the database name."""
    name = "test_cli"
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


def add_query_functions(module, user, cte_class) -> None:
    """Attach the query helpers the CLI accepts as ``module:function``."""
    prefix = "__cte__"

    def active_users():
        return user.query().where(user.c.age >= 18)

    def user_union():
        return user.query().where(user.c.age == 20).union(
            user.query().where(user.c.age == 40)
        )

    def user_cte():
        cte = cte_class(user.backend())
        cte.with_cte("cli_users", user.query().where(user.c.age >= 18))
        return cte.from_cte("cli_users")

    module.active_users = active_users
    module.user_union = user_union
    module.user_cte = user_cte
    setattr(module, prefix, True)


def build_module(name, user, bulk, read_only, soft, validated, cte_class):
    """Build and register the module the CLI imports by name."""
    module = types.ModuleType(name)
    module.User = user
    module.BulkUser = bulk
    module.ReadOnlyUser = read_only
    module.SoftDeleteTask = soft
    module.ValidatedUser = validated
    add_query_functions(module, user, cte_class)
    sys.modules[name] = module
    return module


def model_namespace(module, soft) -> types.SimpleNamespace:
    """Describe the module to the tests and to the CLI's --model arguments."""
    prefix = module.__name__
    return types.SimpleNamespace(
        module=module,
        model=f"{prefix}:User",
        bulk_model=f"{prefix}:BulkUser",
        validated_model=f"{prefix}:ValidatedUser",
        read_only_model=f"{prefix}:ReadOnlyUser",
        soft_delete_model=f"{prefix}:SoftDeleteTask" if soft is not None else None,
        query=f"{prefix}:active_users",
        union_query=f"{prefix}:user_union",
        cte_query=f"{prefix}:user_cte",
    )


@pytest.fixture(name="cli_models")
def cli_models(database_config):
    scenario, config, _name = database_config
    models = (User, BulkUser, ValidatedUser, Task, CLIReadOnlyUser)
    for model in models:
        model.configure(config, scenario.backend_class)
    user, bulk, validated, soft, read_only = models
    module = build_module(
        "cli_sync_" + uuid.uuid4().hex,
        user,
        bulk,
        read_only,
        soft,
        validated,
        CTEQuery,
    )
    yield model_namespace(module, soft)
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="async_cli_models")
async def async_cli_models(database_config):
    scenario, config, _name = database_config
    models = (
        AsyncUser,
        AsyncBulkUser,
        AsyncValidatedUser,
        AsyncTask,
        AsyncCLIReadOnlyUser,
    )
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    user, bulk, validated, soft, read_only = models
    module = build_module(
        "cli_async_" + uuid.uuid4().hex,
        user,
        bulk,
        read_only,
        soft,
        validated,
        AsyncCTEQuery,
    )
    yield model_namespace(module, soft)
    for model in models:
        await model.backend().disconnect()
