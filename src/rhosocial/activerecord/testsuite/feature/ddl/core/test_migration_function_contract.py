# src/rhosocial/activerecord/testsuite/feature/ddl/test_migration_function_contract.py
"""Backend contract for function migrations.

The contract is about the mechanism, not a process: a decorated function may
declare DDL, and a runner may render it without writing.  No backend needs to
ship an orchestrator for this to work.
"""

try:  # Python 3.8 has no typing.Annotated
    from typing import Annotated, Optional
except ImportError:  # pragma: no cover - only on 3.8
    from typing import Optional

    from typing_extensions import Annotated

import pytest
from rhosocial.activerecord.backend.expression.types import IntegerType, VarCharType
from rhosocial.activerecord.backend.migration import (
    MigrationDirection,
    NamedMigration,
    migration,
    resolve_migration_function,
)
from rhosocial.activerecord.backend.migration.context import (
    AsyncMigrationContext,
    MigrationContext,
)
from rhosocial.activerecord.backend.migration.functions import (
    MigrationFunctionError,
)
from rhosocial.activerecord.backend.named_expression.procedure import (
    AsyncProcedure,
    AsyncProcedureRunner,
    Procedure,
    ProcedureRunner,
    TransactionMode,
)
from rhosocial.activerecord.base import UseSqlType
from rhosocial.activerecord.model import ActiveRecord, AsyncActiveRecord


class ContractUser(ActiveRecord):
    @classmethod
    def table_name(cls):
        return "ddl_contract_function_users"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    name: Annotated[str, UseSqlType(VarCharType(length=64))]

    @classmethod
    @migration("v001_contract_users")
    def create_table(cls, ctx):
        if ctx.direction == MigrationDirection.UP:
            ctx.apply(cls.create_table_statement(backend=ctx.backend))
        else:
            ctx.apply(cls.drop_table_statement(backend=ctx.backend, if_exists=True))


class AsyncContractUser(AsyncActiveRecord):
    @classmethod
    def table_name(cls):
        return "ddl_contract_function_users"

    id: Annotated[Optional[int], UseSqlType(IntegerType())] = None
    name: Annotated[str, UseSqlType(VarCharType(length=64))]

    @classmethod
    @migration("v001_contract_users_async")
    async def create_table(cls, ctx):
        if ctx.direction == MigrationDirection.UP:
            await ctx.apply(cls.create_table_statement(backend=ctx.backend))
        else:
            await ctx.apply(cls.drop_table_statement(backend=ctx.backend, if_exists=True))


class LegacyNamedMigration(NamedMigration):
    version = "v999_legacy_contract"

    def up(self, ctx):
        pass

    def down(self, ctx):
        pass


class _DummyBackend:
    def __init__(self, dialect):
        self.dialect = dialect

    def execute(self, *args, **kwargs):  # pragma: no cover - dry run
        raise AssertionError("a dry run must not execute statements")


class _AsyncDummyBackend(_DummyBackend):
    async def execute(self, *args, **kwargs):  # pragma: no cover - dry run
        raise AssertionError("a dry run must not execute statements")


def _sync_procedure():
    def run(self, ctx):
        ContractUser.create_table(ctx)

    return type("ContractSyncProcedure", (Procedure,), {"run": run})


def _async_procedure():
    async def run(self, ctx):
        await AsyncContractUser.create_table(ctx)

    return type("ContractAsyncProcedure", (AsyncProcedure,), {"run": run})


def test_migration_decorator_records_version_and_dependencies():
    info = ContractUser.create_table.__func__.__migration__
    assert info.version == "v001_contract_users"
    assert info.dependencies == ()


def test_resolver_accepts_a_model_function():
    ref = resolve_migration_function(f"{__name__}:ContractUser.create_table")
    assert ref.owner is ContractUser
    assert ref.info.version == "v001_contract_users"


def test_resolver_rejects_named_migration_classes():
    with pytest.raises(MigrationFunctionError, match="NamedMigration"):
        resolve_migration_function(f"{__name__}:LegacyNamedMigration")


def test_sync_function_dry_run_renders_create_table(ddl_dialect):
    runner = ProcedureRunner(procedure_class=_sync_procedure())
    result = runner.run(
        _DummyBackend(ddl_dialect),
        transaction_mode=TransactionMode.AUTO,
        dry_run=True,
        context_factory=lambda **kwargs: MigrationContext(
            direction=MigrationDirection.UP, **kwargs
        ),
    )
    assert result.aborted is False
    assert result.dry_run is True
    assert result.dry_run_total == 1
    sql = result.dry_run_sql[0][1]
    assert "CREATE TABLE" in sql.upper()
    assert "ddl_contract_function_users" in sql


async def test_async_function_dry_run_renders_create_table(async_ddl_dialect):
    runner = AsyncProcedureRunner(procedure_class=_async_procedure())
    result = await runner.run(
        _AsyncDummyBackend(async_ddl_dialect),
        transaction_mode=TransactionMode.AUTO,
        dry_run=True,
        context_factory=lambda **kwargs: AsyncMigrationContext(
            direction=MigrationDirection.UP, **kwargs
        ),
    )
    assert result.aborted is False
    assert result.dry_run is True
    assert result.dry_run_total == 1
    sql = result.dry_run_sql[0][1]
    assert "CREATE TABLE" in sql.upper()
    assert "ddl_contract_function_users" in sql
