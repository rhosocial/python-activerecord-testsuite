# src/rhosocial/activerecord/testsuite/feature/cli/conftest.py
"""Fixtures for the CLI feature.

The CLI tests address models by ``module:attribute`` strings, so the fixture
builds a throw-away module whose attributes are the models configured for the
directory's database.  The directory owns one fixture group: every test
prepares the tables of the basic and mixins models the CLI exercises.
"""
import sys
import types
import uuid

import pytest
from rhosocial.activerecord.query import AsyncCTEQuery, CTEQuery

from rhosocial.activerecord.testsuite.feature.basic.fixtures import (
    tables as basic_tables,
)
from rhosocial.activerecord.testsuite.feature.basic.fixtures.models import (
    AsyncBulkUser,
    AsyncUser,
    AsyncValidatedUser,
    BulkUser,
    User,
    ValidatedUser,
)
from rhosocial.activerecord.testsuite.feature.cli.fixtures import (
    AsyncCLIReadOnlyUser,
    CLIReadOnlyUser,
)
from rhosocial.activerecord.testsuite.feature.mixins.fixtures import (
    tables as mixins_tables,
)
from rhosocial.activerecord.testsuite.feature.mixins.fixtures.models import (
    AsyncTask,
    Task,
)

BACKEND_ATTRIBUTES = (
    "__backend__",
    "__connection_config__",
    "__backend_class__",
    "__logging_config__",
)

GROUP_TABLES = (
    ("users", basic_tables.BASIC_TABLES["users"]),
    ("bulk_users", basic_tables.BASIC_TABLES["bulk_users"]),
    ("validated_users", basic_tables.BASIC_TABLES["validated_users"]),
    ("tasks", mixins_tables.MIXINS_TABLES["tasks"]),
)


def ensure_database(environment):
    """Create the directory's database, or clear it when it already exists."""
    environment.reset_database()


def prepare(environment):
    """Create the group's tables before every test."""
    for _, builder in GROUP_TABLES:
        environment.execute(builder(environment.dialect))


def teardown(environment):
    """Drop the group's tables after every test."""
    for name, _ in reversed(GROUP_TABLES):
        environment.execute(basic_tables.drop_table(environment.dialect, name))


def assign_backend(target, source) -> None:
    """Give a view model the backend configured on another model."""
    for attribute in BACKEND_ATTRIBUTES:
        if hasattr(source, attribute):
            setattr(target, attribute, getattr(source, attribute))


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
def cli_models(environment):
    user = environment.configure(User)
    bulk = environment.configure(BulkUser)
    validated = environment.configure(ValidatedUser)
    soft = environment.configure(Task)
    assign_backend(CLIReadOnlyUser, user)
    module = build_module(
        "cli_sync_" + uuid.uuid4().hex,
        user,
        bulk,
        CLIReadOnlyUser,
        soft,
        validated,
        CTEQuery,
    )
    yield model_namespace(module, soft)
    for model in (user, bulk, validated, soft):
        model.__backend__.disconnect()


@pytest.fixture(name="async_cli_models")
async def async_cli_models(environment):
    user = await environment.configure_async(AsyncUser)
    bulk = await environment.configure_async(AsyncBulkUser)
    validated = await environment.configure_async(AsyncValidatedUser)
    soft = await environment.configure_async(AsyncTask)
    assign_backend(AsyncCLIReadOnlyUser, user)
    module = build_module(
        "cli_async_" + uuid.uuid4().hex,
        user,
        bulk,
        AsyncCLIReadOnlyUser,
        soft,
        validated,
        AsyncCTEQuery,
    )
    yield model_namespace(module, soft)
    for model in (user, bulk, validated, soft):
        await model.__backend__.disconnect()
